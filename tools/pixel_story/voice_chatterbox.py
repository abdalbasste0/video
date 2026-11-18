#!/usr/bin/env python3
"""Natural Sofia voiceover with Chatterbox (Resemble AI, MIT; one of Voicebox's engines), ONNX on CPU.

  CHATTERBOX_DIR=/path/to/chatterbox  python voice_chatterbox.py STORY.json OUT_DIR \
      [--ref company/voices/sofia_reference.wav] [--exaggeration 0.6] [--lm q4|fp32]

CHATTERBOX_DIR holds tokenizer.json and onnx/*.onnx(+_data) from onnx-community/chatterbox-ONNX.
Writes voiced_story.json, vo_full.wav, vo_short.wav exactly like voice.py (same build.py step after).
Speech is generated sentence by sentence (more stable, natural pauses) and the voice is cloned
from --ref (Sofia's reference clip, an original synthetic voice, not a real person).
"""
import argparse, json, os, re, sys, time
import numpy as np
import onnxruntime as ort
import soundfile as sf
from tokenizers import Tokenizer

SR = 24000
START, STOP = 6561, 6562
LAYERS, KV_HEADS, HEAD_DIM = 30, 16, 64
LEAD, TAIL, GAP = 0.25, 0.45, 0.22


class Chatterbox:
    def __init__(self, d, lm="q4", threads=None):
        o = ort.SessionOptions()
        if threads:
            o.intra_op_num_threads = threads
        P = lambda n: os.path.join(d, "onnx", n)
        self.enc = ort.InferenceSession(P("speech_encoder.onnx"), o)
        self.emb = ort.InferenceSession(P("embed_tokens.onnx"), o)
        self.lm = ort.InferenceSession(P("language_model_q4.onnx" if lm == "q4" else "language_model.onnx"), o)
        self.dec = ort.InferenceSession(P("conditional_decoder.onnx"), o)
        self.tok = Tokenizer.from_file(os.path.join(d, "tokenizer.json"))
        self.rng = np.random.default_rng(7)

    def set_voice(self, wav_path):
        a, sr = sf.read(wav_path, dtype="float32")
        if a.ndim > 1:
            a = a.mean(axis=1)
        if sr != SR:
            idx = np.arange(0, len(a), sr / SR)
            a = np.interp(idx, np.arange(len(a)), a).astype(np.float32)
        self.cond = self.enc.run(None, {"audio_values": a[None, :]})  # cond_emb, prompt_token, x_vector, prompt_feat

    def _sample(self, logits, gen, temperature=0.8, min_p=0.05, penalty=1.2):
        s = np.take_along_axis(logits, gen, axis=1)
        s = np.where(s < 0, s * penalty, s / penalty)
        logits = logits.copy(); np.put_along_axis(logits, gen, s, axis=1)
        logits = logits[0] / temperature
        p = np.exp(logits - logits.max()); p /= p.sum()
        p[p < min_p * p.max()] = 0; p /= p.sum()
        return int(self.rng.choice(len(p), p=p))

    def speak(self, text, exaggeration=0.6):
        cond_emb, prompt_token, xvec, feat = self.cond
        ids = np.array([self.tok.encode(text).ids], dtype=np.int64)
        pos = np.where(ids >= START, 0, np.arange(ids.shape[1])[None, :] - 1)
        feed = {"input_ids": ids, "position_ids": pos, "exaggeration": np.array([exaggeration], dtype=np.float32)}
        gen = np.array([[START]], dtype=np.int64)
        max_new = 60 + 14 * len(text.split())
        for i in range(max_new):
            emb = self.emb.run(None, feed)[0]
            if i == 0:
                emb = np.concatenate((cond_emb, emb), axis=1)
                past = {f"past_key_values.{l}.{kv}": np.zeros([1, KV_HEADS, 0, HEAD_DIM], dtype=np.float32)
                        for l in range(LAYERS) for kv in ("key", "value")}
                mask = np.ones((1, emb.shape[1]), dtype=np.int64)
            logits, *present = self.lm.run(None, dict(inputs_embeds=emb, attention_mask=mask, **past))
            nxt = self._sample(logits[:, -1, :], gen)
            gen = np.concatenate((gen, [[nxt]]), axis=1)
            if nxt == STOP:
                break
            feed["input_ids"] = np.array([[nxt]], dtype=np.int64)
            feed["position_ids"] = np.array([[i + 1]], dtype=np.int64)
            mask = np.concatenate([mask, np.ones((1, 1), dtype=np.int64)], axis=1)
            for j, k in enumerate(past):
                past[k] = present[j]
        toks = gen[:, 1:]
        if toks.shape[1] and toks[0, -1] == STOP:
            toks = toks[:, :-1]
        toks = np.concatenate([prompt_token, toks], axis=1)
        wav = self.dec.run(None, {"speech_tokens": toks, "speaker_embeddings": xvec, "speaker_features": feat})[0]
        return np.squeeze(wav, axis=0).astype(np.float32)


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = []
    for p in parts:  # keep very short fragments attached to the previous sentence
        if out and len(p.split()) < 3:
            out[-1] += " " + p
        else:
            out.append(p)
    return [p for p in out if p]


def trim(a, thr=0.01):
    nz = np.where(np.abs(a) > thr)[0]
    return a[max(0, nz[0] - 600): nz[-1] + 1200] if len(nz) else a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story"); ap.add_argument("out_dir")
    ap.add_argument("--ref", default="company/voices/sofia_reference.wav")
    ap.add_argument("--exaggeration", type=float, default=0.6)
    ap.add_argument("--lm", default="q4", choices=["q4", "fp32"])
    a = ap.parse_args()
    cb = Chatterbox(os.environ.get("CHATTERBOX_DIR", "chatterbox"), a.lm)
    cb.set_voice(a.ref)
    story = json.load(open(a.story))
    os.makedirs(a.out_dir, exist_ok=True)
    full, short, t0 = [], [], time.time()
    for n, s in enumerate(story["scenes"]):
        text = s.get("narration", "").strip()
        pieces = []
        for sent in sentences(text):
            pieces.append(trim(cb.speak(sent, a.exaggeration)))
            pieces.append(np.zeros(int(GAP * SR), dtype=np.float32))
        audio = np.concatenate(pieces[:-1]) if pieces else np.zeros(0, dtype=np.float32)
        dur = max(s.get("dur") or (3.0 if not text else 0), LEAD + len(audio) / SR + TAIL)
        clip = np.zeros(int(round(dur * SR)), dtype=np.float32)
        st = int(LEAD * SR); clip[st:st + len(audio)] = audio[: len(clip) - st]
        s["dur"] = round(len(clip) / SR, 3)
        full.append(clip)
        if s.get("short"):
            short.append(clip)
        print(f"  scene {n + 1}/{len(story['scenes'])} {s['dur']:.1f}s  ({time.time() - t0:.0f}s elapsed)", file=sys.stderr)
    story["voice"] = {"engine": "chatterbox (Voicebox engine)", "ref": a.ref, "exaggeration": a.exaggeration, "persona": "Sofia"}
    json.dump(story, open(os.path.join(a.out_dir, "voiced_story.json"), "w"), indent=1)
    sf.write(os.path.join(a.out_dir, "vo_full.wav"), np.concatenate(full), SR)
    if short:
        sf.write(os.path.join(a.out_dir, "vo_short.wav"), np.concatenate(short), SR)
    print(f"chatterbox: full {sum(map(len, full)) / SR:.1f}s, short {sum(map(len, short)) / SR:.1f}s, took {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
