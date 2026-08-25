from pathlib import Path

from desktop.app.device_repository import read_from_csv, remove_from_csv, save_to_csv


def test_save_and_read_devices(tmp_path: Path):
    database = tmp_path / "devices.db"

    assert save_to_csv("Test", "192.168.10.123", "Flux", "RGB", database)
    assert not save_to_csv("Duplicate", "192.168.10.123", "Flux", "RGB", database)
    assert read_from_csv(database) == [("Test", "192.168.10.123", "Flux", "RGB")]


def test_remove_device(tmp_path: Path):
    database = tmp_path / "devices.db"
    save_to_csv("Test", "192.168.10.123", "Flux", "RGB", database)

    assert remove_from_csv("192.168.10.123", database)
    assert not remove_from_csv("192.168.10.123", database)
    assert read_from_csv(database) == []


def test_imports_legacy_csv(tmp_path: Path):
    database = tmp_path / "devices.db"
    (tmp_path / "devices.csv").write_text("Desk,192.168.1.5,Flux,GRB\n", encoding="utf-8")

    assert read_from_csv(database) == [("Desk", "192.168.1.5", "Flux", "GRB")]
