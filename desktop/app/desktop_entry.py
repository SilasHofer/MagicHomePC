"""Add Magic Home to the app menu and start it at login.

    magic-home --install-desktop-entry                 app menu + start at login
    magic-home --install-desktop-entry --no-autostart  app menu only
    magic-home --uninstall-desktop-entry               remove both again

Everything goes into the user's own folders, so no admin/root rights are needed.

Linux (freedesktop .desktop files):
  ~/.local/share/applications/magic-home.desktop   app menu entry
  ~/.config/autostart/magic-home.desktop           start at login
  ~/.local/share/magic-home/icon.png               icon used by both

Windows (shortcuts, started with pythonw.exe so no console window stays open):
  %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Magic Home.lnk           Start menu
  %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\Magic Home.lnk   start at login
  %APPDATA%\\Magic Home\\icon.ico                                              icon used by both
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .paths import APP_ID, APP_NAME, source_checkout_root, user_data_dir
from .theme import ICON_PATH


def install(autostart=True):
    if sys.platform.startswith("linux"):
        return _linux_install(autostart)
    if sys.platform == "win32":
        return _windows_install(autostart)
    print("Adding an app menu entry is supported on Linux and Windows only.")
    return 1


def uninstall():
    if sys.platform.startswith("linux"):
        return _linux_uninstall()
    if sys.platform == "win32":
        return _windows_uninstall()
    print("Adding an app menu entry is supported on Linux and Windows only.")
    return 1


def _remove(paths):
    removed = False
    for path in paths:
        if path.exists():
            path.unlink()
            print(f"Removed {path}")
            removed = True
    if not removed:
        print("Nothing to remove: no app menu or autostart entry was installed.")
    return removed


# --- Linux --------------------------------------------------------------------------------

def _data_home():
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def _config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def menu_entry_path():
    return _data_home() / "applications" / f"{APP_ID}.desktop"


def autostart_entry_path():
    return _config_home() / "autostart" / f"{APP_ID}.desktop"


def icon_path():
    return user_data_dir() / "icon.png"


def _quote(value):
    """Quote an argument for the Exec= line of a .desktop file."""
    value = str(value)
    if any(c in value for c in ' \t\n"\'\\><~|&;$*?#()`'):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$") + '"'
    return value


def entry_text(autostart=False):
    """The .desktop file: runs this same Python with the app module, so it works for pipx, a
    virtual environment or a source checkout alike."""
    lines = [
        "[Desktop Entry]",
        "Type=Application",
        f"Name={APP_NAME}",
        "GenericName=Smart Light Control",
        "Comment=Control your Magic Home / Flux LED lights from the system tray",
        f"Exec={_quote(sys.executable)} -m desktop.app.main",
        f"Icon={icon_path()}",
        "Terminal=false",
        "Categories=Utility;",
        "Keywords=light;lights;bulb;LED;smart home;Flux;",
        "StartupNotify=false",
    ]
    root = source_checkout_root()
    if root is not None:
        lines.append(f"Path={root}")  # a checkout is only importable from the repository folder
    if autostart:
        lines.append("X-GNOME-Autostart-enabled=true")
        lines.append("X-KDE-autostart-after=panel")
    return "\n".join(lines) + "\n"


def _refresh_menu():
    """Ask the desktop to pick up the new entry right away (it usually notices by itself)."""
    for command in (["kbuildsycoca6"], ["kbuildsycoca5"], ["update-desktop-database", str(menu_entry_path().parent)]):
        if shutil.which(command[0]):
            subprocess.run(command, capture_output=True, timeout=30)
            break


def _write_icon(path, size=256, ico=False):
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(ICON_PATH).convert("RGBA").resize((size, size), Image.LANCZOS)
    if ico:
        image.save(path, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (256, 256)])
    else:
        image.save(path)


def _linux_install(autostart):
    _write_icon(icon_path())

    menu_entry_path().parent.mkdir(parents=True, exist_ok=True)
    menu_entry_path().write_text(entry_text())
    menu_entry_path().chmod(0o755)
    print(f"Added to the app menu:  {menu_entry_path()}")

    if autostart:
        autostart_entry_path().parent.mkdir(parents=True, exist_ok=True)
        autostart_entry_path().write_text(entry_text(autostart=True))
        autostart_entry_path().chmod(0o755)
        print(f"Starts at login:        {autostart_entry_path()}")
    elif autostart_entry_path().exists():
        autostart_entry_path().unlink()
        print(f"Removed start at login: {autostart_entry_path()}")

    _refresh_menu()
    print(f'Look for "{APP_NAME}" in your app menu.')
    return 0


def _linux_uninstall():
    if _remove((menu_entry_path(), autostart_entry_path(), icon_path())):
        _refresh_menu()
    return 0


# --- Windows ------------------------------------------------------------------------------

def _start_menu_dir():
    appdata = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    return appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs"


def start_menu_shortcut_path():
    return _start_menu_dir() / f"{APP_NAME}.lnk"


def startup_shortcut_path():
    return _start_menu_dir() / "Startup" / f"{APP_NAME}.lnk"


def windows_icon_path():
    return user_data_dir() / "icon.ico"


def _windowless_python():
    """pythonw.exe next to the running python.exe: starts the app without a console window."""
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    return pythonw if pythonw.exists() else Path(sys.executable)


def _ps(value):
    """A PowerShell single-quoted string."""
    return "'" + str(value).replace("'", "''") + "'"


def shortcut_script(shortcut):
    """PowerShell that creates a .lnk shortcut starting the app (no extra Python packages needed)."""
    root = source_checkout_root()
    working_dir = root if root is not None else user_data_dir()
    return "\n".join([
        "$shell = New-Object -ComObject WScript.Shell",
        f"$link = $shell.CreateShortcut({_ps(shortcut)})",
        f"$link.TargetPath = {_ps(_windowless_python())}",
        "$link.Arguments = '-m desktop.app.main'",
        f"$link.WorkingDirectory = {_ps(working_dir)}",
        f"$link.IconLocation = {_ps(windows_icon_path())}",
        "$link.Description = 'Control your Magic Home / Flux LED lights from the system tray'",
        "$link.Save()",
    ])


def _create_shortcut(shortcut):
    shortcut.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-Command", shortcut_script(shortcut)],
        capture_output=True, text=True, timeout=60)
    if result.returncode != 0 or not shortcut.exists():
        raise RuntimeError(f"Could not create {shortcut}: {result.stderr.strip()}")


def _windows_install(autostart):
    user_data_dir().mkdir(parents=True, exist_ok=True)  # also the shortcut's working folder
    _write_icon(windows_icon_path(), ico=True)
    try:
        _create_shortcut(start_menu_shortcut_path())
        print(f"Added to the Start menu: {start_menu_shortcut_path()}")
        if autostart:
            _create_shortcut(startup_shortcut_path())
            print(f"Starts at login:         {startup_shortcut_path()}")
        elif startup_shortcut_path().exists():
            startup_shortcut_path().unlink()
            print(f"Removed start at login:  {startup_shortcut_path()}")
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(error)
        return 1
    print(f'Look for "{APP_NAME}" in the Start menu.')
    return 0


def _windows_uninstall():
    _remove((start_menu_shortcut_path(), startup_shortcut_path(), windows_icon_path()))
    return 0
