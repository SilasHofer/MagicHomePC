import csv
import sqlite3
import os
from pathlib import Path


DEFAULT_FILENAME = os.getenv(
    "MAGIC_HOME_DEVICES_DB",
    str(Path(__file__).resolve().parents[2] / "data" / "devices.db"),
)

def _initialize(filename):
    database = Path(filename)
    database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS devices (ip TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL, color_order TEXT NOT NULL)"
        )
        has_devices = connection.execute("SELECT EXISTS (SELECT 1 FROM devices)").fetchone()[0]
        legacy_file = database.with_name("devices.csv")
        if not has_devices and legacy_file.exists():
            with legacy_file.open(newline="", encoding="utf-8") as file:
                connection.executemany(
                    "INSERT OR IGNORE INTO devices (ip, name, type, color_order) VALUES (?, ?, ?, ?)",
                    ((row[1], row[0], row[2], row[3]) for row in csv.reader(file) if len(row) >= 4),
                )
        connection.commit()


def save_to_csv(name, ip, tool, color_order, filename=DEFAULT_FILENAME):
    _initialize(filename)
    try:
        with sqlite3.connect(filename) as connection:
            connection.execute(
                "INSERT INTO devices (ip, name, type, color_order) VALUES (?, ?, ?, ?)",
                (ip, name, tool, color_order),
            )
            connection.commit()
    except sqlite3.IntegrityError:
        return False
    return True

def read_from_csv(filename=DEFAULT_FILENAME):
    _initialize(filename)
    with sqlite3.connect(filename) as connection:
        return connection.execute(
            "SELECT name, ip, type, color_order FROM devices ORDER BY name"
        ).fetchall()

def remove_from_csv(ip,filename=DEFAULT_FILENAME):
    _initialize(filename)
    with sqlite3.connect(filename) as connection:
        result = connection.execute("DELETE FROM devices WHERE ip = ?", (ip,))
        connection.commit()
    return result.rowcount > 0
