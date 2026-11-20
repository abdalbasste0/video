"""Factory floor: runs the 15 workers for each video, several videos in parallel."""
import json
import re
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from . import connectors, settings as cfg
from .roster import BY_ID, WORKERS
from .workers import FUNCS

WRITING = ["trend_scout", "idea_judge", "researcher", "fact_checker", "hook_writer",
           "scriptwriter", "script_editor", "storyboarder"]
MEDIA_A = ["illustrator", "narrator"]                        # in parallel
CHAIN = ["sound_engineer", "editor", "shorts_maker"]         # in order, parallel with the two below
SIDE = ["thumbnail_designer", "seo_publisher"]


def _root(s):
    p = Path(s["output_dir"])
    return p if p.is_absolute() else cfg.ROOT / p


def _slug(text):
    t = re.sub(r"[^\w؀-ۿ]+", "-", text or "auto").strip("-")
    return t[:40] or "auto"


class Factory:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()
        self.listeners = []          # fn(job) called when a job finishes or fails
        self._pool, self._size = None, 0
        self._load()

    # -------------------------------------------------------------- storage
    def _load(self):
        root = _root(cfg.load()) / "jobs"
        for f in sorted(root.glob("*/job.json")) if root.exists() else []:
            try:
                j = json.loads(f.read_text(encoding="utf-8"))
                if j.get("status") in ("running", "queued"):
                    j["status"] = "stopped"
                self.jobs[j["id"]] = j
            except Exception:
                pass

    def _save(self, job):
        p = Path(job["dir"]) / "job.json"
        p.write_text(json.dumps(job, ensure_ascii=False, indent=1), encoding="utf-8")

    # -------------------------------------------------------------- public API
    def submit(self, topic=None, demo=False):
        s = cfg.load()
        jid = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3] + "-" + _slug(topic)
        d = _root(s) / "jobs" / jid
        d.mkdir(parents=True, exist_ok=True)
        job = {"id": jid, "topic": (topic or "").strip() or None, "dir": str(d), "status": "queued", "demo": demo,
               "created": time.time(), "current": None, "error": None, "publish": [],
               "steps": {w["id"]: {"status": "waiting"} for w in WORKERS}}
        with self.lock:
            self.jobs[jid] = job
        self._save(job)
        self._executor(s).submit(self._run, jid)
        return jid

    def resume(self, jid):
        job = self.jobs[jid]
        if job["status"] in ("running", "queued"):
            return
        job["status"], job["error"] = "queued", None
        self._executor(cfg.load()).submit(self._run, jid)

    def republish(self, jid, connector_id=None):
        job = self.jobs[jid]
        res = connectors.publish_all(cfg.load(), self._package(job), only_id=connector_id)
        job["publish"] = res
        self._save(job)
        return res

    def list(self):
        with self.lock:
            return sorted(self.jobs.values(), key=lambda j: j["created"], reverse=True)

    # -------------------------------------------------------------- internals
    def _executor(self, s):
        n = max(1, int(s.get("parallel_videos", 2)))
        if self._pool is None or n != self._size:
            self._pool, self._size = ThreadPoolExecutor(n, thread_name_prefix="video"), n
        return self._pool

    def _step(self, job, wid, s):
        st = job["steps"][wid]
        if st["status"] == "done":
            return
        w = BY_ID[wid]
        if not w["required"] and not s["workers"].get(wid, {}).get("enabled", True):
            st.update(status="skipped", output=None)
            return
        st.update(status="running", started=time.time())
        job["current"] = wid
        self._save(job)
        if job.get("demo") and w["kind"] == "llm":
            from .demo import DEMO
            out = DEMO[wid](job) if callable(DEMO[wid]) else DEMO[wid]
        else:
            out = FUNCS[wid](job, s)
        st.update(status="done", output=out, secs=round(time.time() - st["started"], 1))
        self._save(job)

    def _run(self, jid):
        job = self.jobs[jid]
        s = cfg.load()
        if job.get("demo"):
            s["voice"]["provider"] = s["voice"]["provider"] if s["voice"]["provider"] != "elevenlabs" else "edge"
        job["status"] = "running"
        try:
            for wid in WRITING:
                self._step(job, wid, s)
            self._parallel(job, s, [[w] for w in MEDIA_A])
            self._parallel(job, s, [CHAIN] + [[w] for w in SIDE])
            job["current"] = "publish"
            self._save(job)
            job["publish"] = connectors.publish_all(s, self._package(job))
            self._remember_topic(job, s)
            job["status"], job["current"] = "done", None
        except Exception as e:
            for st in job["steps"].values():
                if st["status"] == "running":
                    st["status"] = "error"
            job["status"], job["error"] = "error", f"{e}"
            job["trace"] = traceback.format_exc()[-3000:]
        job["finished"] = time.time()
        self._save(job)
        for fn in list(self.listeners):
            try:
                fn(job)
            except Exception:
                pass

    def _parallel(self, job, s, chains):
        errors = []

        def run_chain(chain):
            try:
                for wid in chain:
                    self._step(job, wid, s)
            except Exception as e:
                errors.append(e)
                raise

        with ThreadPoolExecutor(len(chains)) as ex:
            list(ex.map(lambda c: self._safe(run_chain, c), chains))
        if errors:
            raise errors[0]

    @staticmethod
    def _safe(fn, arg):
        try:
            fn(arg)
        except Exception:
            pass

    def _package(self, job):
        o = lambda w: (job["steps"].get(w) or {}).get("output") or {}
        seo, ed, sh, th = o("seo_publisher"), o("editor"), o("shorts_maker"), o("thumbnail_designer")
        topic = o("idea_judge").get("topic") or job.get("topic") or ""
        return {"job_id": job["id"], "job_dir": job["dir"], "topic": topic,
                "video": ed.get("video"), "short": sh.get("short"), "thumbnail": th.get("thumbnail"), "srt": ed.get("srt"),
                "title": seo.get("title") or topic, "description": seo.get("description", ""),
                "tags": seo.get("tags", []), "hashtags": seo.get("hashtags", []),
                "short_title": seo.get("short_title") or seo.get("title") or topic,
                "pinned_comment": seo.get("pinned_comment", "")}

    def _remember_topic(self, job, s):
        topic = self._package(job)["topic"]
        if topic:
            with open(_root(s) / "topics_done.txt", "a", encoding="utf-8") as f:
                f.write(topic.replace("\n", " ") + "\n")


FACTORY = None


def get_factory():
    global FACTORY
    if FACTORY is None:
        FACTORY = Factory()
    return FACTORY
