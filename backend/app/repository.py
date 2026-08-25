import csv
import sqlite3
from pathlib import Path

from .models import Device


class DeviceRepository:
    def __init__(self, filename: str = "data/devices.db") -> None:
        self.filename = Path(filename)
        self._initialize()

    def _initialize(self) -> None:
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.filename) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    ip TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    color_order TEXT NOT NULL
                )
                """
            )
            has_devices = connection.execute("SELECT EXISTS (SELECT 1 FROM devices)").fetchone()[0]
            legacy_file = self.filename.with_name("devices.csv")
            if not has_devices and legacy_file.exists():
                with legacy_file.open(newline="", encoding="utf-8") as file:
                    connection.executemany(
                        "INSERT OR IGNORE INTO devices (ip, name, type, color_order) VALUES (?, ?, ?, ?)",
                        ((row[1], row[0], row[2], row[3]) for row in csv.reader(file) if len(row) >= 4),
                    )
            connection.commit()

    def list(self) -> list[Device]:
        with sqlite3.connect(self.filename) as connection:
            rows = connection.execute(
                "SELECT name, ip, type, color_order FROM devices ORDER BY name"
            ).fetchall()
        return [Device(name=name, ip=ip, type=tool, color_order=order) for name, ip, tool, order in rows]

    def get(self, ip: str) -> Device | None:
        with sqlite3.connect(self.filename) as connection:
            row = connection.execute(
                "SELECT name, ip, type, color_order FROM devices WHERE ip = ?", (ip,)
            ).fetchone()
        return Device(name=row[0], ip=row[1], type=row[2], color_order=row[3]) if row else None

    def add(self, device: Device) -> Device:
        if self.get(device.ip) is not None:
            raise ValueError("A device with this IP address already exists")
        with sqlite3.connect(self.filename) as connection:
            connection.execute(
                "INSERT INTO devices (ip, name, type, color_order) VALUES (?, ?, ?, ?)",
                (device.ip, device.name, device.type, device.color_order),
            )
            connection.commit()
        return device

    def remove(self, ip: str) -> bool:
        with sqlite3.connect(self.filename) as connection:
            result = connection.execute("DELETE FROM devices WHERE ip = ?", (ip,))
            connection.commit()
        return result.rowcount > 0
