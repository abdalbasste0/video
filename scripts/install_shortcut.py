"""Creates an "مصنع الفيديو" (Video Factory) shortcut on the desktop to open the app with one click.

Run it once on your computer from the project folder:
    python scripts/install_shortcut.py

- Windows: a .lnk shortcut with the factory icon (opens without a black console window)
- macOS:   an "مصنع الفيديو.command" file on the desktop
- Linux:   a .desktop file on the desktop and in the applications menu
"""
from __future__ import annotations

import base64
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "مصنع الفيديو"
ICON_PNG = ROOT / "assets" / "icon.png"
ICON_ICO = ROOT / "assets" / "icon.ico"


def windows_desktop() -> Path:
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        if out:
            return Path(out)
    except (OSError, subprocess.SubprocessError):
        pass
    for cand in (Path(os.environ.get("OneDrive", "")) / "Desktop", Path.home() / "Desktop"):
        if cand.exists():
            return cand
    return Path.home() / "Desktop"


def install_windows() -> Path:
    desktop = windows_desktop()
    pyw = Path(sys.executable).with_name("pythonw.exe")
    target = pyw if pyw.exists() else Path(sys.executable)
    lnk = desktop / f"{NAME}.lnk"
    ps = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}');"
        "$s.TargetPath = '{target}'; $s.Arguments = '-m factory app';"
        "$s.WorkingDirectory = '{wd}'; $s.IconLocation = '{icon}'; $s.Description = 'Video Factory'; $s.Save()"
    ).format(lnk=str(lnk).replace("'", "''"), target=str(target).replace("'", "''"),
             wd=str(ROOT).replace("'", "''"), icon=str(ICON_ICO).replace("'", "''"))
    # -EncodedCommand (UTF-16LE) so the Arabic name isn't garbled
    enc = base64.b64encode(ps.encode("utf-16-le")).decode()
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", enc],
                       capture_output=True, text=True)
    if r.returncode != 0 or not lnk.exists():
        # Fallback: a simple .bat file
        bat = desktop / f"{NAME}.bat"
        bat.write_text(f'@echo off\r\ncd /d "{ROOT}"\r\nstart "" "{target}" -m factory app\r\n', encoding="utf-8")
        return bat
    return lnk


def install_macos() -> Path:
    f = Path.home() / "Desktop" / f"{NAME}.command"
    f.write_text(f'#!/bin/bash\ncd "{ROOT}"\n"{sys.executable}" -m factory app\n', encoding="utf-8")
    f.chmod(0o755)
    return f


def install_linux() -> Path:
    entry = (
        "[Desktop Entry]\nType=Application\n"
        f"Name={NAME}\nName[en]=Video Factory\nComment=Video Factory\n"
        f'Exec="{sys.executable}" -m factory app\nPath={ROOT}\nIcon={ICON_PNG}\n'
        "Terminal=false\nCategories=AudioVideo;\n"
    )
    desktop = Path(subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True).stdout.strip()
                   or Path.home() / "Desktop") if shutil.which("xdg-user-dir") else Path.home() / "Desktop"
    desktop.mkdir(parents=True, exist_ok=True)
    f = desktop / "video-factory.desktop"
    f.write_text(entry, encoding="utf-8")
    f.chmod(0o755)
    apps = Path.home() / ".local" / "share" / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    (apps / "video-factory.desktop").write_text(entry, encoding="utf-8")
    if shutil.which("gio"):  # lets GNOME launch it without a warning
        subprocess.run(["gio", "set", str(f), "metadata::trusted", "true"], capture_output=True)
    return f


def main() -> None:
    system = platform.system()
    path = {"Windows": install_windows, "Darwin": install_macos}.get(system, install_linux)()
    print(f"✅ تم إنشاء الاختصار: {path}")
    print("اضغط عليه مرتين لفتح تطبيق مصنع الفيديو.")


if __name__ == "__main__":
    main()
