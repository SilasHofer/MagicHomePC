from flux_led import WifiLedBulb

from .models import Device, DeviceState


class BulbService:
    def __init__(self, repository) -> None:
        self.repository = repository
        self._base_colors: dict[str, tuple[int, int, int]] = {}

    def _device(self, ip: str) -> Device:
        device = self.repository.get(ip)
        if device is None:
            raise LookupError("Device not found")
        return device

    def _bulb(self, ip: str):
        self._device(ip)
        return WifiLedBulb(ip)

    @staticmethod
    def _device_to_rgb(values: tuple[int, int, int], order: str) -> tuple[int, int, int]:
        channels = dict(zip(order, values))
        return channels.get("R", 0), channels.get("G", 0), channels.get("B", 0)

    @staticmethod
    def _rgb_to_device(values: tuple[int, int, int], order: str) -> tuple[int, int, int]:
        channels = dict(zip("RGB", values))
        return tuple(channels.get(channel, 0) for channel in order)

    def state(self, ip: str) -> DeviceState:
        device = self._device(ip)
        bulb = WifiLedBulb(ip)
        color = self._device_to_rgb(tuple(bulb.getRgb()), device.color_order)
        if max(color) > 0:
            self._base_colors[ip] = self._normalize_color(color)
        return DeviceState(
            ip=ip,
            is_on=bool(bulb.is_on),
            color=color,
            brightness=round(max(color) / 255 * 100),
        )

    def turn_on(self, ip: str) -> None:
        self._bulb(ip).turnOn()

    def turn_off(self, ip: str) -> None:
        self._bulb(ip).turnOff()

    def set_color(self, ip: str, red: int, green: int, blue: int) -> None:
        device = self._device(ip)
        color = (red, green, blue)
        if max(color) > 0:
            self._base_colors[ip] = self._normalize_color(color)
        values = self._rgb_to_device(color, device.color_order)
        WifiLedBulb(ip).setRgb(*values)

    def set_brightness(self, ip: str, brightness: int) -> None:
        device = self._device(ip)
        bulb = WifiLedBulb(ip)
        current = self._device_to_rgb(tuple(bulb.getRgb()), device.color_order)
        if max(current) > 0:
            self._base_colors[ip] = self._normalize_color(current)
        base = self._base_colors.get(ip, (0, 0, 0))
        scaled = tuple(round(value * brightness / 100) for value in base)
        self.set_color(ip, *scaled)

    @staticmethod
    def _normalize_color(color: tuple[int, int, int]) -> tuple[int, int, int]:
        maximum = max(color)
        if maximum == 0:
            return (0, 0, 0)
        return tuple(min(255, round(value * 255 / maximum)) for value in color)

    def check(self, ip: str) -> bool:
        # Connection checks are also used before a device is saved.
        bulb = WifiLedBulb(ip)
        return bool(bulb.is_on or bulb.getRgb() is not None)

    def set_all(self, ips: list[str], enabled: bool) -> list[str]:
        failed: list[str] = []
        for ip in ips:
            try:
                self.turn_on(ip) if enabled else self.turn_off(ip)
            except Exception:
                failed.append(ip)
        return failed
