from pathlib import Path

from backend.app.repository import DeviceRepository


def test_repository_reads_devices(tmp_path: Path):
    database_file = tmp_path / "devices.db"
    legacy_file = tmp_path / "devices.csv"
    legacy_file.write_text("Desk,192.168.1.5,Flux,RGB\n", encoding="utf-8")

    repository = DeviceRepository(str(database_file))

    assert repository.list()[0].name == "Desk"
    assert repository.get("192.168.1.5").color_order == "RGB"
    assert repository.get("10.0.0.1") is None
