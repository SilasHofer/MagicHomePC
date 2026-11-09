"""Where the desktop app keeps its data.

- MAGIC_HOME_DEVICES_DB, if set, always wins (e.g. to share one database with the web app).
- Running from a source checkout of the repository: data/devices.db in the repository,
  shared with the web app and Docker, exactly as before.
- Installed (pipx / pip): a per-user folder, because the installed code is read-only:
  Linux   ~/.local/share/magic-home/devices.db  (or $XDG_DATA_HOME/magic-home)
  Windows %APPDATA%\\Magic Home\\devices.db
  macOS   ~/Library/Application Support/Magic Home/devices.db
"""
import os
import sys
from pathlib import Path

APP_ID = "magic-home"
APP_NAME = "Magic Home"


def user_data_dir():
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / APP_ID


def source_checkout_root():
    """The repository folder when running from a git checkout (not an installed copy), else None."""
    root = Path(__file__).resolve().parents[2]
    if (root / "compose.yaml").is_file() and (root / "desktop" / "app").is_dir():
        return root
    return None


def default_database():
    configured = os.getenv("MAGIC_HOME_DEVICES_DB")
    if configured:
        return configured
    root = source_checkout_root()
    folder = root / "data" if root is not None else user_data_dir()
    return str(folder / "devices.db")
