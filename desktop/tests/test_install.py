import sys
from pathlib import Path

import pytest

from desktop.app import desktop_entry, paths


def test_database_env_variable_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("MAGIC_HOME_DEVICES_DB", str(tmp_path / "shared.db"))
    assert paths.default_database() == str(tmp_path / "shared.db")


def test_source_checkout_uses_repository_data_folder(monkeypatch):
    monkeypatch.delenv("MAGIC_HOME_DEVICES_DB", raising=False)
    root = Path(__file__).resolve().parents[2]
    assert paths.source_checkout_root() == root
    assert paths.default_database() == str(root / "data" / "devices.db")


def test_installed_copy_uses_user_data_folder(monkeypatch, tmp_path):
    monkeypatch.delenv("MAGIC_HOME_DEVICES_DB", raising=False)
    monkeypatch.setattr(paths, "source_checkout_root", lambda: None)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    expected = paths.user_data_dir() / "devices.db"
    assert paths.default_database() == str(expected)
    if sys.platform.startswith("linux"):
        assert expected == tmp_path / "data" / "magic-home" / "devices.db"


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="desktop entries are Linux only")
def test_install_and_uninstall_desktop_entry(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setattr(desktop_entry, "_refresh_menu", lambda: None)

    assert desktop_entry.install(autostart=True) == 0
    menu = tmp_path / "data" / "applications" / "magic-home.desktop"
    autostart = tmp_path / "config" / "autostart" / "magic-home.desktop"
    icon = tmp_path / "data" / "magic-home" / "icon.png"
    assert menu.is_file() and autostart.is_file() and icon.is_file()
    text = menu.read_text()
    assert "Name=Magic Home" in text
    assert "-m desktop.app.main" in text
    assert f"Icon={icon}" in text
    assert "X-GNOME-Autostart-enabled=true" in autostart.read_text()

    # Re-installing without autostart removes only the start-at-login entry
    assert desktop_entry.install(autostart=False) == 0
    assert menu.is_file() and not autostart.exists()

    assert desktop_entry.uninstall() == 0
    assert not menu.exists() and not icon.exists()


def test_exec_line_quotes_paths_with_spaces(monkeypatch):
    monkeypatch.setattr(sys, "executable", "/home/me/My Apps/python")
    assert 'Exec="/home/me/My Apps/python" -m desktop.app.main' in desktop_entry.entry_text()


def test_windows_install_creates_shortcuts_with_powershell(monkeypatch, tmp_path):
    """Windows can't be run here, so check the PowerShell it runs and the files it writes."""
    appdata = tmp_path / "AppData" / "Roaming"
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setattr(desktop_entry, "source_checkout_root", lambda: None)
    python_dir = tmp_path / "pipx" / "Scripts"
    python_dir.mkdir(parents=True)
    (python_dir / "pythonw.exe").write_text("")
    monkeypatch.setattr(sys, "executable", str(python_dir / "python.exe"))

    scripts = []

    def fake_powershell(command, **kwargs):
        script = command[-1]
        scripts.append((command, script))
        target = script.split("CreateShortcut('", 1)[1].split("')", 1)[0]
        Path(target).write_text("lnk")
        return subprocess.CompletedProcess(command, 0, "", "")

    import subprocess
    monkeypatch.setattr(desktop_entry.subprocess, "run", fake_powershell)

    assert desktop_entry.install(autostart=True) == 0
    programs = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    assert (programs / "Magic Home.lnk").exists()
    assert (programs / "Startup" / "Magic Home.lnk").exists()
    assert (appdata / "Magic Home" / "icon.ico").exists()

    command, script = scripts[0]
    assert command[0] == "powershell" and "-NoProfile" in command
    assert f"$link.TargetPath = '{python_dir / 'pythonw.exe'}'" in script   # no console window
    assert "$link.Arguments = '-m desktop.app.main'" in script
    assert f"$link.IconLocation = '{appdata / 'Magic Home' / 'icon.ico'}'" in script

    assert desktop_entry.install(autostart=False) == 0
    assert not (programs / "Startup" / "Magic Home.lnk").exists()

    assert desktop_entry.uninstall() == 0
    assert not (programs / "Magic Home.lnk").exists()
    assert not (appdata / "Magic Home" / "icon.ico").exists()


def test_powershell_strings_escape_quotes():
    assert desktop_entry._ps("C:\\Users\\O'Brien\\x") == "'C:\\Users\\O''Brien\\x'"
