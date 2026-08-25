import os

import requests


class MagicHomeApiClient:
    """HTTP client for using the same backend from the desktop application."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("MAGIC_HOME_API", "http://localhost:8000")).rstrip("/")

    def devices(self) -> list[dict]:
        response = requests.get(f"{self.base_url}/api/devices", timeout=5)
        response.raise_for_status()
        return response.json()

    def turn_on(self, ip: str) -> None:
        response = requests.post(f"{self.base_url}/api/devices/{ip}/on", timeout=5)
        response.raise_for_status()

    def turn_off(self, ip: str) -> None:
        response = requests.post(f"{self.base_url}/api/devices/{ip}/off", timeout=5)
        response.raise_for_status()

    def set_color(self, ip: str, red: int, green: int, blue: int) -> None:
        response = requests.put(
            f"{self.base_url}/api/devices/{ip}/color",
            json={"red": red, "green": green, "blue": blue},
            timeout=5,
        )
        response.raise_for_status()
