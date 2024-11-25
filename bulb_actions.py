from flux_led import WifiLedBulb


# Function to turn on the light
def Toggle_bulb(bulb):
    if(get_status(bulb)):
        bulb.turnOff()
    else:
        bulb.turnOn()


def turn_off_all_bulbs(devices):
    for device in devices:
        bulb = WifiLedBulb(device[1])
        bulb.turnOff()

def turn_on_all_bulbs(devices):
    for device in devices:
        bulb = WifiLedBulb(device[1])
        bulb.turnOn()


# Function to change color to Red
def set_rgb(bulb,color):
    bulb.setRgb(color[0],color[1],color[2])  # Red color

# Function to set brightness to 128 (50%)
def set_brightness(bulb):
    bulb.brightness == 128  # 50% brightness

def get_status(bulb):
    return bulb.is_on

def get_color(bulb):
    return bulb.getRgb()
