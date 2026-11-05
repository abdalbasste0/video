"""Discord bot that controls linked YouTube channels with slash commands."""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import aiohttp
import discord
from discord import app_commands
from dotenv import load_dotenv
from googleapiclient.errors import HttpError

import youtube_client as ytc

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bot")

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
ALLOWED_USERS = {int(x) for x in os.getenv("ALLOWED_USER_IDS", "").replace(" ", "").split(",") if x}
TZ = ZoneInfo(os.getenv("TIMEZONE", "Asia/Riyadh"))
MAX_DOWNLOAD_MB = int(os.getenv("MAX_DOWNLOAD_MB", "2048"))

store = ytc.ChannelStore(Path(os.getenv("TOKENS_DIR", "tokens")))

PRIVACY_CHOICES = [
    app_commands.Choice(name="خاص (private)", value="private"),
    app_commands.Choice(name="غير مدرج (unlisted)", value="unlisted"),
    app_commands.Choice(name="عام (public)", value="public"),
]
PRIVACY_AR = {"private": "خاص 🔒", "unlisted": "غير مدرج 🔗", "public": "عام 🌍"}


# ------------------------------------------------------------------ setup ---

class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = YTTree(self)

    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
        log.info("Slash commands synced")

    async def on_ready(self):
        log.info("Logged in as %s — channels: %s", self.user, store.aliases() or "none")


class YTTree(app_commands.CommandTree):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in ALLOWED_USERS:
            return True
        if interaction.type == discord.InteractionType.application_command:
            await interaction.response.send_message("⛔ ليس لديك صلاحية لاستخدام هذا البوت.", ephemeral=True)
        return False

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        err = getattr(error, "original", error)
        if isinstance(err, HttpError):
            try:
                msg = err.error_details[0]["message"] if err.error_details else err.reason
            except Exception:
                msg = str(err)
            text = f"❌ خطأ من يوتيوب ({err.status_code}): {msg}"
        elif isinstance(err, (KeyError, ValueError, LookupError, PermissionError, RuntimeError)):
            text = f"❌ {err.args[0] if err.args else err}"
        else:
            log.exception("Unhandled error", exc_info=err)
            text = f"❌ خطأ غير متوقع: {err}"
        if interaction.response.is_done():
            await interaction.followup.send(text[:1900])
        else:
            await interaction.response.send_message(text[:1900], ephemeral=True)


bot = Bot()
tree = bot.tree


# ---------------------------------------------------------------- helpers ---

async def channel_autocomplete(_: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=a, value=a)
        for a in store.aliases()
        if current.lower() in a.lower()
    ][:25]


async def yt_call(alias: str, func, *args, **kwargs):
    """Run a blocking YouTube call for the given channel in a worker thread."""
    def run():
        return func(store.service(alias), *args, **kwargs)
    return await asyncio.to_thread(run)


def parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y/%m/%d %H:%M"):
        try:
            dt = datetime.strptime(value.strip(), fmt).replace(tzinfo=TZ)
            break
        except ValueError:
            continue
    else:
        raise ValueError("صيغة الوقت غير صحيحة. استخدم مثلاً: 2026-11-10 18:30")
    if dt <= datetime.now(TZ):
        raise ValueError("وقت الجدولة يجب أن يكون في المستقبل")
    return dt


def parse_tags(value: Optional[str]) -> Optional[list[str]]:
    if value is None:
        return None
    return [t.strip() for t in value.split(",") if t.strip()]


def fmt_num(n: int) -> str:
    return f"{n:,}"


async def download(url: str, dest: Path, on_progress=None) -> None:
    limit = MAX_DOWNLOAD_MB * 1024 * 1024
    timeout = aiohttp.ClientTimeout(total=None, sock_read=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            total = resp.content_length or 0
            if total > limit:
                raise ValueError(f"الملف أكبر من الحد المسموح ({MAX_DOWNLOAD_MB}MB)")
            done = 0
            with dest.open("wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 1024):
                    done += len(chunk)
                    if done > limit:
                        raise ValueError(f"الملف أكبر من الحد المسموح ({MAX_DOWNLOAD_MB}MB)")
                    f.write(chunk)
                    if on_progress and total:
                        await on_progress(done / total)


def progress_bar(fraction: float) -> str:
    filled = int(fraction * 20)
    return "█" * filled + "░" * (20 - filled) + f" {fraction * 100:.0f}%"


class Throttle:
    """Edits a Discord message at most every few seconds."""

    def __init__(self, message: discord.WebhookMessage, every: float = 3.0):
        self.message, self.every, self.last = message, every, 0.0

    async def __call__(self, text: str, force: bool = False):
        now = time.monotonic()
        if force or now - self.last >= self.every:
            self.last = now
            try:
                await self.message.edit(content=text)
            except discord.HTTPException:
                pass


# --------------------------------------------------------------- commands ---

@tree.command(name="help", description="عرض قائمة الأوامر")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 أوامر بوت يوتيوب", color=0xFF0000)
    for name, desc in [
        ("/channels", "عرض القنوات المربوطة"),
        ("/stats", "إحصائيات قناة"),
        ("/videos", "آخر فيديوهات القناة"),
        ("/upload", "رفع فيديو (ملف مرفق أو رابط) مع جدولة اختيارية"),
        ("/edit", "تعديل العنوان/الوصف/الوسوم"),
        ("/privacy", "تغيير الخصوصية أو جدولة النشر"),
        ("/thumbnail", "تغيير الصورة المصغرة"),
        ("/delete", "حذف فيديو (مع تأكيد)"),
        ("/comments", "آخر التعليقات على فيديو"),
        ("/reply", "الرد على تعليق"),
    ]:
        embed.add_field(name=name, value=desc, inline=False)
    embed.set_footer(text="لربط قناة جديدة: python auth.py <اسم>")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="channels", description="عرض قنوات يوتيوب المربوطة")
async def channels_cmd(interaction: discord.Interaction):
    aliases = store.aliases()
    if not aliases:
        await interaction.response.send_message(
            "لا توجد قنوات مربوطة بعد. شغّل على السيرفر: `python auth.py main`", ephemeral=True
        )
        return
    await interaction.response.defer(thinking=True)
    lines = []
    for alias in aliases:
        try:
            info = await yt_call(alias, ytc.channel_stats)
            lines.append(
                f"**{alias}** → {info['title']} — 👥 {fmt_num(info['subscribers'])} · 🎬 {info['videos']}"
            )
        except Exception as e:  # keep listing the others
            lines.append(f"**{alias}** → ⚠️ {e}")
    await interaction.followup.send("📺 القنوات المربوطة:\n" + "\n".join(lines))


@tree.command(name="stats", description="إحصائيات قناة")
@app_commands.describe(channel="القناة")
@app_commands.autocomplete(channel=channel_autocomplete)
async def stats_cmd(interaction: discord.Interaction, channel: str):
    await interaction.response.defer(thinking=True)
    info = await yt_call(channel, ytc.channel_stats)
    embed = discord.Embed(
        title=info["title"], url=f"https://youtube.com/channel/{info['id']}", color=0xFF0000
    )
    if info["thumbnail"]:
        embed.set_thumbnail(url=info["thumbnail"])
    embed.add_field(
        name="👥 المشتركين",
        value="مخفي" if info["hidden_subs"] else fmt_num(info["subscribers"]),
    )
    embed.add_field(name="👁️ المشاهدات", value=fmt_num(info["views"]))
    embed.add_field(name="🎬 الفيديوهات", value=fmt_num(info["videos"]))
    await interaction.followup.send(embed=embed)


@tree.command(name="videos", description="آخر فيديوهات القناة")
@app_commands.describe(channel="القناة", count="العدد (1-20)")
@app_commands.autocomplete(channel=channel_autocomplete)
async def videos_cmd(
    interaction: discord.Interaction, channel: str, count: app_commands.Range[int, 1, 20] = 5
):
    await interaction.response.defer(thinking=True)
    videos = await yt_call(channel, ytc.recent_videos, count)
    if not videos:
        await interaction.followup.send("لا توجد فيديوهات.")
        return
    embed = discord.Embed(title=f"🎬 آخر الفيديوهات — {channel}", color=0xFF0000)
    for v in videos:
        embed.add_field(
            name=v.title[:250],
            value=(
                f"{PRIVACY_AR.get(v.privacy, v.privacy)} · 👁️ {fmt_num(v.views)} · 👍 {fmt_num(v.likes)}"
                f" · 💬 {fmt_num(v.comments)}\n`{v.id}` · {v.url}"
            ),
            inline=False,
        )
    await interaction.followup.send(embed=embed)


@tree.command(name="upload", description="رفع فيديو إلى قناة يوتيوب")
@app_commands.describe(
    channel="القناة",
    title="عنوان الفيديو",
    file="ملف الفيديو (مرفق)",
    url="أو رابط مباشر للفيديو",
    description="الوصف",
    tags="وسوم مفصولة بفاصلة",
    privacy="الخصوصية",
    schedule="وقت النشر، مثل: 2026-11-10 18:30 (يجعل الفيديو مجدولاً)",
    thumbnail="صورة مصغرة (اختياري)",
)
@app_commands.choices(privacy=PRIVACY_CHOICES)
@app_commands.autocomplete(channel=channel_autocomplete)
async def upload_cmd(
    interaction: discord.Interaction,
    channel: str,
    title: str,
    file: Optional[discord.Attachment] = None,
    url: Optional[str] = None,
    description: str = "",
    tags: Optional[str] = None,
    privacy: str = "private",
    schedule: Optional[str] = None,
    thumbnail: Optional[discord.Attachment] = None,
):
    if not file and not url:
        await interaction.response.send_message("أرفق ملف فيديو أو ضع رابطاً.", ephemeral=True)
        return
    publish_at = parse_time(schedule)
    store.token_path(channel)  # validate alias early
    await interaction.response.send_message(f"⏳ جاري تجهيز الفيديو **{title}**…")
    msg = await interaction.original_response()
    update = Throttle(msg)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        video_path = tmp / "video"
        source = file.url if file else url

        async def dl_progress(frac):
            await update(f"⬇️ تحميل الفيديو…\n{progress_bar(frac)}")

        await download(source, video_path, dl_progress)

        loop = asyncio.get_running_loop()

        def up_progress(frac):
            asyncio.run_coroutine_threadsafe(update(f"⬆️ الرفع إلى يوتيوب…\n{progress_bar(frac)}"), loop)

        await update("⬆️ بدء الرفع إلى يوتيوب…", force=True)
        video_id = await yt_call(
            channel,
            ytc.upload_video,
            video_path,
            title=title,
            description=description,
            tags=parse_tags(tags),
            privacy=privacy,
            publish_at=publish_at,
            on_progress=up_progress,
        )

        thumb_note = ""
        if thumbnail:
            thumb_path = tmp / (thumbnail.filename or "thumb.jpg")
            await thumbnail.save(thumb_path)
            try:
                await yt_call(channel, ytc.set_thumbnail, video_id, thumb_path)
                thumb_note = "\n🖼️ تم تعيين الصورة المصغرة"
            except HttpError as e:
                thumb_note = f"\n⚠️ تعذر تعيين الصورة المصغرة: {e.reason}"

    when = (
        f"📅 مجدول للنشر: {publish_at.strftime('%Y-%m-%d %H:%M')} ({TZ.key})"
        if publish_at
        else f"الخصوصية: {PRIVACY_AR[privacy]}"
    )
    await update(
        f"✅ تم رفع **{title}** على `{channel}`\n{when}\nhttps://youtu.be/{video_id}{thumb_note}",
        force=True,
    )


@tree.command(name="edit", description="تعديل عنوان/وصف/وسوم فيديو")
@app_commands.describe(
    channel="القناة", video="رابط أو معرف الفيديو", title="عنوان جديد",
    description="وصف جديد", tags="وسوم جديدة مفصولة بفاصلة",
)
@app_commands.autocomplete(channel=channel_autocomplete)
async def edit_cmd(
    interaction: discord.Interaction,
    channel: str,
    video: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
):
    if title is None and description is None and tags is None:
        await interaction.response.send_message("حدّد شيئاً لتعديله.", ephemeral=True)
        return
    vid = ytc.extract_video_id(video)
    await interaction.response.defer(thinking=True)
    await yt_call(channel, ytc.update_video, vid, title=title, description=description, tags=parse_tags(tags))
    await interaction.followup.send(f"✅ تم تعديل الفيديو https://youtu.be/{vid}")


@tree.command(name="privacy", description="تغيير خصوصية فيديو أو جدولة نشره")
@app_commands.describe(
    channel="القناة", video="رابط أو معرف الفيديو", privacy="الخصوصية الجديدة",
    schedule="أو وقت نشر مجدول، مثل: 2026-11-10 18:30",
)
@app_commands.choices(privacy=PRIVACY_CHOICES)
@app_commands.autocomplete(channel=channel_autocomplete)
async def privacy_cmd(
    interaction: discord.Interaction,
    channel: str,
    video: str,
    privacy: str = "public",
    schedule: Optional[str] = None,
):
    vid = ytc.extract_video_id(video)
    publish_at = parse_time(schedule)
    await interaction.response.defer(thinking=True)
    await yt_call(channel, ytc.set_privacy, vid, privacy, publish_at)
    state = (
        f"مجدول للنشر {publish_at.strftime('%Y-%m-%d %H:%M')}" if publish_at else PRIVACY_AR[privacy]
    )
    await interaction.followup.send(f"✅ الفيديو https://youtu.be/{vid} أصبح: {state}")


@tree.command(name="thumbnail", description="تغيير الصورة المصغرة لفيديو")
@app_commands.describe(channel="القناة", video="رابط أو معرف الفيديو", image="الصورة (JPG/PNG أقل من 2MB)")
@app_commands.autocomplete(channel=channel_autocomplete)
async def thumbnail_cmd(
    interaction: discord.Interaction, channel: str, video: str, image: discord.Attachment
):
    vid = ytc.extract_video_id(video)
    await interaction.response.defer(thinking=True)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / (image.filename or "thumb.jpg")
        await image.save(path)
        await yt_call(channel, ytc.set_thumbnail, vid, path)
    await interaction.followup.send(f"🖼️ تم تغيير الصورة المصغرة لـ https://youtu.be/{vid}")


class ConfirmDelete(discord.ui.View):
    def __init__(self, user_id: int, channel: str, video_id: str):
        super().__init__(timeout=60)
        self.user_id, self.channel, self.video_id = user_id, channel, video_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label="نعم، احذف", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(content="⏳ جاري الحذف…", view=None)
        try:
            await yt_call(self.channel, ytc.delete_video, self.video_id)
            await interaction.edit_original_response(content=f"🗑️ تم حذف الفيديو `{self.video_id}`")
        except HttpError as e:
            await interaction.edit_original_response(content=f"❌ فشل الحذف: {e.reason}")
        self.stop()

    @discord.ui.button(label="إلغاء", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(content="تم الإلغاء.", view=None)
        self.stop()


@tree.command(name="delete", description="حذف فيديو نهائياً")
@app_commands.describe(channel="القناة", video="رابط أو معرف الفيديو")
@app_commands.autocomplete(channel=channel_autocomplete)
async def delete_cmd(interaction: discord.Interaction, channel: str, video: str):
    vid = ytc.extract_video_id(video)
    await interaction.response.defer(thinking=True, ephemeral=True)
    videos = await yt_call(channel, ytc.get_videos, [vid])
    if not videos:
        await interaction.followup.send("الفيديو غير موجود في هذه القناة.", ephemeral=True)
        return
    await interaction.followup.send(
        f"⚠️ هل أنت متأكد من حذف **{videos[0].title}** نهائياً من `{channel}`؟",
        view=ConfirmDelete(interaction.user.id, channel, vid),
        ephemeral=True,
    )


@tree.command(name="comments", description="آخر التعليقات على فيديو")
@app_commands.describe(channel="القناة", video="رابط أو معرف الفيديو", count="العدد (1-20)")
@app_commands.autocomplete(channel=channel_autocomplete)
async def comments_cmd(
    interaction: discord.Interaction, channel: str, video: str,
    count: app_commands.Range[int, 1, 20] = 10,
):
    vid = ytc.extract_video_id(video)
    await interaction.response.defer(thinking=True)
    comments = await yt_call(channel, ytc.list_comments, vid, count)
    if not comments:
        await interaction.followup.send("لا توجد تعليقات.")
        return
    embed = discord.Embed(title="💬 آخر التعليقات", url=f"https://youtu.be/{vid}", color=0xFF0000)
    for c in comments:
        embed.add_field(
            name=f"{c['author']} · 👍 {c['likes']} · ↩️ {c['replies']}"[:250],
            value=f"{c['text'][:900]}\n`{c['id']}`",
            inline=False,
        )
    embed.set_footer(text="للرد: /reply مع معرف التعليق")
    await interaction.followup.send(embed=embed)


@tree.command(name="reply", description="الرد على تعليق")
@app_commands.describe(channel="القناة", comment_id="معرف التعليق (من /comments)", text="نص الرد")
@app_commands.autocomplete(channel=channel_autocomplete)
async def reply_cmd(interaction: discord.Interaction, channel: str, comment_id: str, text: str):
    await interaction.response.defer(thinking=True)
    await yt_call(channel, ytc.reply_comment, comment_id.strip(), text)
    await interaction.followup.send(f"✅ تم الرد على التعليق `{comment_id}`")


def main():
    if not TOKEN:
        raise SystemExit("ضع DISCORD_TOKEN في ملف .env")
    if not ALLOWED_USERS:
        raise SystemExit("ضع معرفك في ALLOWED_USER_IDS داخل ملف .env (لحماية قنواتك)")
    bot.run(TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
