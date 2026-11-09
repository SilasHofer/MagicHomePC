
from desktop.app.bulb_actions import Toggle_bulb, turn_off_all_bulbs, turn_on_all_bulbs, set_rgb, get_brightness, get_ip_of_selected_device
from unittest.mock import patch, MagicMock
from flux_led import WifiLedBulb
import pytest


@patch("desktop.app.bulb_actions.get_status", return_value=True)
@patch("desktop.app.shared_state.bulb")
def test_Toggle_bulb_off(mock_bulb, mock_get_status):
    Toggle_bulb()
    mock_bulb.turnOff.assert_called_once()
    mock_bulb.turnOn.assert_not_called()


@patch("desktop.app.bulb_actions.get_status", return_value=False)
@patch("desktop.app.shared_state.bulb")
def test_Toggle_bulb_on(mock_bulb, mock_get_status):
    Toggle_bulb()
    mock_bulb.turnOn.assert_called_once()
    mock_bulb.turnOff.assert_not_called()


@patch("desktop.app.bulb_actions.WifiLedBulb")  # Mock the WifiLedBulb class
def test_turn_off_all_bulbs(mock_bulb_class):
    # Create different mock instances for each device
    mock_bulb_instances = [MagicMock(), MagicMock()]
    mock_bulb_class.side_effect = mock_bulb_instances  # Each call creates a NEW mock instance

    # Example list of devices (name, IP address)
    devices = [("Living Room", "192.168.1.10","Flux"), ("Bedroom", "192.168.1.11","Flux")]

    # Call the function
    turn_off_all_bulbs(devices)

    # Ensure a new instance was created for each device
    assert mock_bulb_class.call_count == len(devices)

    # Ensure turnOff() was called once on each separate bulb instance
    for mock_bulb in mock_bulb_instances:
        mock_bulb.turnOff.assert_called_once()

    # Ensure turnOn() was never called
    for mock_bulb in mock_bulb_instances:
        mock_bulb.turnOn.assert_not_called()

@patch("desktop.app.bulb_actions.WifiLedBulb")  # Mock the WifiLedBulb class
def test_turn_on_all_bulbs(mock_bulb_class):
    # Create different mock instances for each device
    mock_bulb_instances = [MagicMock(), MagicMock()]
    mock_bulb_class.side_effect = mock_bulb_instances  # Each call creates a NEW mock instance

    # Example list of devices (name, IP address)
    devices = [("Living Room", "192.168.1.10","Flux"), ("Bedroom", "192.168.1.11","Flux")]

    # Call the function
    turn_on_all_bulbs(devices)

    # Ensure a new instance was created for each device
    assert mock_bulb_class.call_count == len(devices)

    # Ensure turnOn() was called once on each separate bulb instance
    for mock_bulb in mock_bulb_instances:
        mock_bulb.turnOn.assert_called_once()

    # Ensure turnOff() was never called
    for mock_bulb in mock_bulb_instances:
        mock_bulb.turnOff.assert_not_called()

@patch("desktop.app.shared_state.bulb")
def test_set_rgb(mock_bulb):
    color = (255, 0, 0)
    set_rgb(color)
    mock_bulb.setRgb.assert_called_once_with(*color)

@patch("desktop.app.shared_state.bulb")
def test_get_brightness(mock_bulb):
    mock_bulb.getRgb.return_value = (255, 128, 64)
    brightness = get_brightness()
    assert brightness == pytest.approx(255 / 255, rel=1e-5)

@patch("desktop.app.shared_state.bulb")
def test_get_brightness_low(mock_bulb):
    mock_bulb.getRgb.return_value = (127, 128, 64)
    brightness = get_brightness()
    assert brightness == pytest.approx(128 / 255, rel=1e-5)

@patch("desktop.app.shared_state.bulb")
def test_get_brightness_zero(mock_bulb):
    mock_bulb.getRgb.return_value = (0, 0, 0)
    brightness = get_brightness()
    assert brightness == pytest.approx(0 / 255, rel=1e-5)

def test_get_ip_of_selected_device():
    devices = [("Living Room", "192.168.1.10", "Flux", "RGB"), ("Bedroom", "192.168.1.11", "Flux", "RGB")]
    # Mock selected_device (simulating a Tkinter StringVar)
    mock_selected_device = MagicMock()
    mock_selected_device.get.return_value = "Living Room"  # Simulate selected device
    ip = get_ip_of_selected_device(mock_selected_device, devices)
    assert ip == ("192.168.1.10", "RGB")

def test_get_ip_of_selected_device_not_found():
    devices = [("Living Room", "192.168.1.10", "Flux", "RGB"), ("Bedroom", "192.168.1.11", "Flux", "RGB")]
    # Mock selected_device (simulating a Tkinter StringVar)
    mock_selected_device = MagicMock()
    mock_selected_device.get.return_value = "Living Rooms"  # Simulate selected device
    ip = get_ip_of_selected_device(mock_selected_device, devices)
    assert ip == None

def test_get_ip_of_selected_device_emty_device_list():
    devices = []
    # Mock selected_device (simulating a Tkinter StringVar)
    mock_selected_device = MagicMock()
    mock_selected_device.get.return_value = "Living Rooms"  # Simulate selected device
    ip = get_ip_of_selected_device(mock_selected_device, devices)
    assert ip == None



class _FakeBulb:
    def __init__(self, rgb):
        self.rgb = rgb

    def getRgb(self):
        return self.rgb

    def setRgb(self, r, g, b):
        self.rgb = (r, g, b)


def test_brightness_drag_keeps_color(monkeypatch):
    from desktop.app import shared_state
    from desktop.app.bulb_actions import set_brightness

    monkeypatch.setattr(shared_state, "bulb", _FakeBulb((84, 21, 255)))
    monkeypatch.setattr(shared_state, "current_device_info", "RGB")
    monkeypatch.setattr(shared_state, "base_color", None)

    # Drag the slider all the way down and back up a few times
    for _ in range(3):
        for value in list(range(100, 0, -1)) + list(range(1, 101)):
            set_brightness(value)

    assert shared_state.bulb.rgb == (84, 21, 255)


def test_brightness_respects_color_order(monkeypatch):
    from desktop.app import shared_state
    from desktop.app.bulb_actions import set_brightness

    # Device order GRB: the bulb reports (G, R, B)
    monkeypatch.setattr(shared_state, "bulb", _FakeBulb((0, 255, 0)))  # pure red
    monkeypatch.setattr(shared_state, "current_device_info", "GRB")
    monkeypatch.setattr(shared_state, "base_color", None)

    set_brightness(50)

    assert shared_state.bulb.rgb == (0, 128, 0)  # still red, half brightness
