"""Link a YouTube channel to the bot.

Usage:
    python auth.py <alias>

Example:
    python auth.py main
    python auth.py gaming

A browser window opens; sign in with the Google account that owns the
channel (if it is a Brand Account, pick that channel). The token is saved
to tokens/<alias>.json and the bot can use the channel right away.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

from youtube_client import SCOPES, ChannelStore, channel_stats

load_dotenv()


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    alias = sys.argv[1]
    store = ChannelStore(Path(os.getenv("TOKENS_DIR", "tokens")))
    store.token_path(alias)  # validates the alias

    secrets = os.getenv("GOOGLE_CLIENT_SECRETS", "client_secret.json")
    if not Path(secrets).exists():
        print(f"لم أجد ملف {secrets}. حمّله من Google Cloud Console (راجع README).")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(secrets, SCOPES)
    creds = flow.run_local_server(
        port=int(os.getenv("OAUTH_PORT", "8765")),
        prompt="consent",
        access_type="offline",
        open_browser=True,
    )
    store.save(alias, creds)

    info = channel_stats(store.service(alias))
    print(f"✅ تم ربط القناة '{info['title']}' باسم: {alias}")


if __name__ == "__main__":
    main()
