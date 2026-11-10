"""Fast tests (no rendering of full videos). Run:  python -m pytest -q"""
import json

import pytest

from studio import captions, config, poses, qc, queue, rig, shots, text, tts


def test_roster_has_100_roles_10_per_department():
    r = config.roster()
    assert len(r["roles"]) == 100
    assert len({x["id"] for x in r["roles"]}) == 100
    for d in r["departments"]:
        roles = [x for x in r["roles"] if x["department"] == d["key"]]
        assert len(roles) == 10, d["key"]
        for role in roles:
            assert role["mission"] and role["output"] and len(role["checklist"]) >= 2


def test_department_agents_exist():
    for d in config.roster()["departments"]:
        assert (config.ROOT / ".claude" / "agents" / f"{d['key']}.md").exists()


def test_languages_have_required_fields():
    for code, lang in config.languages().items():
        for k in ("direction", "font", "font_body", "words_per_minute", "tts", "caption_style"):
            assert k in lang, (code, k)
        assert lang["direction"] in ("rtl", "ltr")
        assert {"narrator", "hero", "ally", "antagonist"} <= set(lang["tts"]["voices"])


def test_arabic_is_reshaped_and_font_has_glyphs():
    lang = config.language("ar")
    shaped = text.shape("من أطفأ الضوء؟", "rtl")
    assert text.is_shaped_arabic(shaped)
    assert text.missing_glyphs(lang["font"], shaped) == []


def test_latin_fonts_cover_accents():
    for code, s in [("fr", "éèàçù Ç"), ("es", "ñáéíóú ¿¡")]:
        assert text.missing_glyphs(config.language(code)["font"], s) == []


def test_pose_library_size_and_validity():
    lib = poses.library()
    assert len(lib) >= 25
    for name in lib:
        p = poses.sample(name, 0.37)
        for k in poses.PAIR_KEYS:
            assert len(p[k]) == 2


def test_cycles_loop_smoothly():
    """End of a cycle must equal its start (no pop when looping)."""
    for name, d in poses.library().items():
        if d.get("type") == "cycle":
            a, b = poses.sample(name, 0.0), poses.sample(name, d["duration"] - 1e-6)
            assert abs(a["torso"] - b["torso"]) < 1.0, name


def test_walk_has_positive_stride():
    assert poses.get("walk")["stride"] > 0.1
    assert poses.get("run")["stride"] > poses.get("walk")["stride"]


def test_easing_bounds():
    for e in poses.EASINGS.values():
        assert e(0) == pytest.approx(0, abs=1e-6) and e(1) == pytest.approx(1, abs=1e-6)


def test_character_renders_with_every_emotion_and_accessory():
    for i, acc in enumerate(config.characters_cfg()["accessories"]):
        img, anchor, info = rig.render_character({"color": "teal", "accessory": acc}, poses.sample("walk", 0.2), 200, 1,
                                                 rig.EMOTIONS[i % 6], mouth=0.5)
        assert img.size[0] > 50 and img.getbbox()


def test_feet_on_ground_when_grounded():
    j = rig.solve(poses.sample("walk", 0.1), 300, 1)
    off = rig.ground_offset(j, poses.sample("walk", 0.1))
    lowest = max(j[k][1] for k in rig.POINT_KEYS) + off
    assert abs(lowest) < 1e-6


def test_actor_walks_from_to():
    actor = {"char": "hero", "x": 0.2, "actions": [{"t0": 0, "t1": 2, "do": "walk", "to": 0.6}]}
    _, x0, f0, _ = shots.actor_at(actor, 0.0)
    _, x1, f1, _ = shots.actor_at(actor, 2.0)
    assert x0 == pytest.approx(0.2) and x1 == pytest.approx(0.6) and f1 == 1


def test_similarity_detects_copies():
    a = "a lighthouse keeper finds a door under the sea that opens only at midnight"
    assert qc.similarity(a, a) > 0.99
    assert qc.similarity(a, "two hikers lost in a desert follow strange radio signals") < 0.3


def test_word_budget_lands_on_15_minutes():
    b = queue.word_budget(config.language("en"))
    assert b["target_words"] == 150 * 15
    assert b["min_words"] < b["target_words"] < b["max_words"]


def test_report_parser():
    t = "| R001 | Premise | PASS | ok |\n| R002 | World | fail | missing map |"
    assert queue.parse_report(t) == {"R001": "pass", "R002": "fail"}


def test_srt_grouping(tmp_path):
    lines = [{"text": "Do you hear that? It is coming through the trees.", "start": 1.0, "end": 3.5}]
    out = captions.write_srt("en", tmp_path / "x.srt", lines=lines, log=lambda *_: None)
    body = out.read_text(encoding="utf-8")
    assert "00:00:01,000 -->" in body and "trees." in body


def test_elevenlabs_budget_guard(monkeypatch):
    monkeypatch.setattr(tts, "usage_this_month", lambda: 99_990.0)
    with pytest.raises(config.StudioError):
        tts.elevenlabs_budget_check(["x" * 500], log=lambda *_: None)
