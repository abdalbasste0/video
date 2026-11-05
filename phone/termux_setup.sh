#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  Video Factory — one-time setup on Android (Termux)
#  Run inside Termux:   bash ~/video/phone/termux_setup.sh
# ============================================================
set -e
APP="$HOME/video"
cd "$APP"

echo "▶ 1/6 Packages (python, ffmpeg, git, termux-api)…"
pkg update -y
pkg install -y python ffmpeg git termux-api clang make libffi openssl

echo "▶ 2/6 Python libraries…"
# pure-python fallbacks so nothing needs a compiler-heavy build on the phone
export AIOHTTP_NO_EXTENSIONS=1 MULTIDICT_NO_EXTENSIONS=1 YARL_NO_EXTENSIONS=1 \
       FROZENLIST_NO_EXTENSIONS=1 PROPCACHE_NO_EXTENSIONS=1
pip install --upgrade pip
pip install pyyaml python-dotenv requests edge-tts
if ! pip install anthropic; then
  echo "  anthropic needs pydantic-core → installing rust (one-time, ~10 min)…"
  pkg install -y rust && pip install anthropic || \
  echo "  ⚠️ anthropic not installed: scripts use the built-in template until you install it."
fi

echo "▶ 3/6 Arabic font for captions (from Android system fonts)…"
mkdir -p library/fonts library/music library/sfx library/images library/luts
cp -n /system/fonts/NotoNaskhArabic*.ttf library/fonts/ 2>/dev/null || true
cp -n /system/fonts/NotoSansArabic*.ttf library/fonts/ 2>/dev/null || true
cp -n /system/fonts/Roboto-Bold.ttf library/fonts/ 2>/dev/null || true

echo "▶ 4/6 Settings file (.env)…"
[ -f .env ] || cp .env.example .env
echo "  → edit it now:  nano $APP/.env   (TELEGRAM_BOT_TOKEN, TELEGRAM_OWNER_ID, keys)"

echo "▶ 5/6 Home-screen shortcuts (Termux:Widget)…"
mkdir -p "$HOME/.shortcuts/tasks" "$HOME/.shortcuts/icons"
cp phone/shortcuts/*.sh "$HOME/.shortcuts/" 2>/dev/null || true
cp phone/shortcuts/tasks/*.sh "$HOME/.shortcuts/tasks/"
chmod +x "$HOME"/.shortcuts/*.sh "$HOME"/.shortcuts/tasks/*.sh phone/*.sh

echo "▶ 6/6 Auto-start after reboot (Termux:Boot)…"
mkdir -p "$HOME/.termux/boot"
cp phone/boot/start-video-factory.sh "$HOME/.termux/boot/"
chmod +x "$HOME/.termux/boot/start-video-factory.sh"

termux-setup-storage || true
python main.py doctor || true
cat <<'MSG'

✅ Setup finished. Last steps on the phone:
  1. Long-press the home screen → Widgets → Termux:Widget → drop it on the home screen.
     You now have buttons:  🎬 Video Factory · ➕ New Video · 📊 Status · ⏹ Stop
  2. Android Settings → Apps → Termux → Battery → "Unrestricted" (no optimisation).
     Do the same for Termux:Boot and Termux:API.
  3. Open Termux:Boot once (so Android lets it start at boot).
  4. Tap 🎬 Video Factory. Your Telegram bot says "Video Factory is online".
MSG
