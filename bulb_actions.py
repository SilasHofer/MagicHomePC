from flux_led import WifiLedBulb

import shared_state

# Function to turn on the light
def Toggle_bulb():
    if(get_status()):
        shared_state.bulb.turnOff()
    else:
        shared_state.bulb.turnOn()


def turn_off_all_bulbs(devices):
    for device in devices:
        bulb = WifiLedBulb(device[1])
        bulb.turnOff()

def turn_on_all_bulbs(devices):
    for device in devices:
        shared_state.bulb = WifiLedBulb(device[1])
        shared_state.bulb.turnOn()


# Function to change color to Red
def set_rgb(color):
    shared_state.bulb.setRgb(color[0],color[1],color[2])

# Function to set brightness to 128 (50%)
def set_brightness():
    color = shared_state.bulb.getRgbw()
    shared_state.bulb._mode = "rgbw"
    shared_state.bulb.setRgbw(color[0],color[1],color[2],color[3],100)

def get_status():
    return shared_state.bulb.is_on

def get_color():
    return shared_state.bulb.getRgb()


def get_ip_of_selected_device(selected_device,devices):
    selected_name = selected_device.get()
    for device in devices:
        if device[0] == selected_name:
            return device[1]  # Return the IP address of the selected device
    return None  # If no match is found, return None

def change_device(selected_device, devices,*args):
    ip = get_ip_of_selected_device(selected_device,devices)
    shared_state.bulb = WifiLedBulb(ip)