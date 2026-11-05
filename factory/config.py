"""Factory settings: keys, paths, and the daily schedule."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Load a .env file without extra dependencies (does not override existing variables)."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip() if not raw.strip().startswith("#") else ""
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


# ---------------------------------------------------------------------------
# Daily schedule: every stage has a deadline (local time).
# Work starts at 08:00 and publishing must happen before 13:00.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Stage:
    key: str            # internal stage name
    bot: str            # name of the responsible bot
    title_ar: str       # Arabic display label (shown to the owner)
    deadline: time      # latest finish time
    needs_approval: bool = False  # does the stage wait for the owner's approval?


SCHEDULE: list[Stage] = [
    Stage("research", "bot1_trend_scout", "البحث عن الأفكار الفيروسية", time(8, 40), needs_approval=True),
    Stage("script", "bot2_script_writer", "كتابة السكريبت والتحقق من التواريخ", time(9, 30), needs_approval=True),
    Stage("voice", "bot3_voice", "التعليق الصوتي (ElevenLabs)", time(10, 0)),
    Stage("media", "bot4_media_hunter", "جلب الفيديوهات والصور", time(10, 40)),
    Stage("edit", "bot5_editor", "المونتاج وتركيب الصوت", time(11, 40)),
    Stage("qa", "bot6_qa", "الفحص قبل العرض", time(12, 0)),
    Stage("final_review", "bot9_manager", "عرض الفيديو النهائي على المالك", time(12, 45), needs_approval=True),
    Stage("publish", "bot9_manager", "النشر", time(12, 55)),
]

WORK_START = time(8, 0)
PUBLISH_HARD_LIMIT = time(13, 0)

# A helper bot (7 / 8) is dispatched once a stage has used this share of its time budget without finishing
HELPER_TRIGGER_RATIO = 0.6


@dataclass
class Settings:
    timezone: ZoneInfo = field(default_factory=lambda: ZoneInfo(env("FACTORY_TIMEZONE", "Africa/Cairo")))
    # Video language (narration, subtitles, title, description). Messages to the owner always stay in Arabic.
    language: str = field(default_factory=lambda: env("FACTORY_LANGUAGE", "en"))
    video_format: str = field(default_factory=lambda: env("FACTORY_FORMAT", "landscape"))
    dry_run: bool = field(default_factory=lambda: env("FACTORY_DRY_RUN", "0") == "1")

    # Claude
    model: str = "claude-opus-5-5"

    # ElevenLabs
    elevenlabs_key: str = field(default_factory=lambda: env("ELEVENLABS_API_KEY"))
    elevenlabs_voice: str = field(default_factory=lambda: env("ELEVENLABS_VOICE_ID"))
    elevenlabs_model: str = field(default_factory=lambda: env("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"))

    # Media
    pexels_key: str = field(default_factory=lambda: env("PEXELS_API_KEY"))
    pixabay_key: str = field(default_factory=lambda: env("PIXABAY_API_KEY"))

    # Telegram
    telegram_token: str = field(default_factory=lambda: env("TELEGRAM_BOT_TOKEN"))
    telegram_chat: str = field(default_factory=lambda: env("TELEGRAM_OWNER_CHAT_ID"))

    # YouTube
    yt_client_id: str = field(default_factory=lambda: env("YOUTUBE_CLIENT_ID"))
    yt_client_secret: str = field(default_factory=lambda: env("YOUTUBE_CLIENT_SECRET"))
    yt_refresh_token: str = field(default_factory=lambda: env("YOUTUBE_REFRESH_TOKEN"))

    workspace: Path = ROOT / "workspace"
    music_dir: Path = ROOT / "assets" / "music"

    @property
    def language_name(self) -> str:
        return {"en": "English", "ar": "Arabic (Modern Standard, simple)", "fr": "French", "es": "Spanish"}.get(
            self.language, self.language)

    @property
    def resolution(self) -> tuple[int, int]:
        return (1080, 1920) if self.video_format == "vertical" else (1920, 1080)

    def now(self) -> datetime:
        return datetime.now(self.timezone) + self._clock_offset

    @property
    def _clock_offset(self):
        """For testing only: FACTORY_FAKE_NOW=07:59 makes the factory act as if the time now is 07:59."""
        from datetime import timedelta
        if not hasattr(self, "_offset_cache"):
            fake = env("FACTORY_FAKE_NOW")
            if fake:
                real = datetime.now(self.timezone)
                h, m = map(int, fake.split(":"))
                self._offset_cache = real.replace(hour=h, minute=m, second=0, microsecond=0) - real
            else:
                self._offset_cache = timedelta(0)
        return self._offset_cache

    def at(self, t: time, day: date | None = None) -> datetime:
        day = day or self.now().date()
        return datetime.combine(day, t, tzinfo=self.timezone)

    def day_dir(self, day: date | None = None) -> Path:
        d = self.workspace / (day or self.now().date()).isoformat()
        d.mkdir(parents=True, exist_ok=True)
        return d


settings = Settings()


ENV_FILE = ROOT / ".env"


def save_env(updates: dict[str, str]) -> None:
    """Updates values in .env (used by the app's settings page) and applies them immediately without a restart."""
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    done = set()
    for i, raw in enumerate(lines):
        key = raw.split("=", 1)[0].strip()
        if "=" in raw and not raw.lstrip().startswith("#") and key in updates:
            lines[i] = f"{key}={updates[key]}"
            done.add(key)
    lines += [f"{k}={v}" for k, v in updates.items() if k not in done]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        ENV_FILE.chmod(0o600)  # the file holds secret keys
    except OSError:
        pass
    os.environ.update(updates)
    reload_settings()


def reload_settings() -> None:
    """Re-reads the settings in place (every module holds a reference to the same settings object)."""
    keep = {"workspace": settings.workspace, "music_dir": settings.music_dir}
    fresh = Settings()
    for k, v in vars(fresh).items():
        setattr(settings, k, v)
    for k, v in keep.items():
        setattr(settings, k, v)
