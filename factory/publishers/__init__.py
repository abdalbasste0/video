"""Multi-platform publishing: YouTube, TikTok, Instagram.

Called only by bot 9 (or the app), and only after the owner's final approval.
Each platform is published separately: if one fails, the others still go out, and the failure is reported to the owner.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..config import env, settings
from ..log import log
from . import instagram, tiktok, youtube

PLATFORMS = {"youtube": youtube, "tiktok": tiktok, "instagram": instagram}
NAMES_AR = {"youtube": "يوتيوب", "tiktok": "تيك توك", "instagram": "إنستغرام"}
ALIASES = {"يوتيوب": "youtube", "يوتوب": "youtube", "youtube": "youtube",
           "تيك": "tiktok", "تيكتوك": "tiktok", "tiktok": "tiktok",
           "انستا": "instagram", "انستغرام": "instagram", "إنستغرام": "instagram", "انستقرام": "instagram",
           "instagram": "instagram", "insta": "instagram"}


@dataclass
class Post:
    video: Path                      # main video (YouTube)
    title: str
    description: str
    tags: list[str] = field(default_factory=list)
    thumbnail: Path | None = None
    vertical_video: Path | None = None  # 9:16 version (TikTok + Instagram Reels)


def enabled_platforms() -> list[str]:
    """Platforms the owner chose (FACTORY_PLATFORMS) that have credentials set (or all of them in test mode)."""
    wanted = [p.strip() for p in env("FACTORY_PLATFORMS", "youtube,tiktok,instagram").split(",") if p.strip()]
    return [p for p in wanted if p in PLATFORMS and (settings.dry_run or PLATFORMS[p].configured())]


def platforms_from_text(text: str) -> list[str]:
    """Pulls platform names out of the owner's reply, e.g. "موافق انشر يوتيوب وتيكتوك" ("approved, publish to YouTube and TikTok")."""
    low = text.lower()
    hits = sorted((low.find(alias), key) for alias, key in ALIASES.items() if alias in low)
    found: list[str] = []
    for _, key in hits:
        if key not in found:
            found.append(key)
    return found


def publish_all(post: Post, platforms: list[str], already: dict | None = None) -> dict[str, dict]:
    results: dict[str, dict] = dict(already or {})
    for name in platforms:
        if results.get(name, {}).get("url"):
            continue  # already published there
        try:
            results[name] = PLATFORMS[name].publish(post)
        except Exception as e:  # noqa: BLE001 — one platform failing must not stop the others
            log.error("Publishing to %s failed: %s", name, e)
            results[name] = {"platform": name, "error": str(e)[:500]}
    return results
