from pathlib import Path
from unittest.mock import patch

from backend.app.bulb_service import BulbService
from backend.app.models import Device
from backend.app.repository import DeviceRepository


def test_scan_marks_saved_devices_and_sorts_by_ip(tmp_path: Path):
    repository = DeviceRepository(str(tmp_path / "devices.db"))
    repository.add(Device(name="Desk", ip="192.168.1.20", type="Flux", color_order="RGB"))
    service = BulbService(repository)

    discoveries = [
        {"ipaddr": "192.168.1.20", "id": "AABBCC000020", "model": "AK001-ZJ200"},
        {"ipaddr": "192.168.1.3", "id": "AABBCC000003", "model": None},
        {"ipaddr": "", "id": "ignored"},
    ]
    with patch("backend.app.bulb_service.BulbScanner") as scanner:
        scanner.return_value.scan.return_value = discoveries
        result = service.scan(timeout=1)

    scanner.return_value.scan.assert_called_once_with(timeout=1)
    assert [device.ip for device in result] == ["192.168.1.3", "192.168.1.20"]
    assert [device.saved for device in result] == [False, True]
    assert result[0].model == ""
    assert result[1].id == "AABBCC000020"
