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
def set_red(bulb):
    bulb.setRgb(255, 0, 0)  # Red color

def set_white(bulb):
    bulb.setRgb(255, 255, 255)

# Function to set brightness to 128 (50%)
def set_brightness(bulb):
    bulb.brightness == 128  # 50% brightness

def get_status(bulb):
    return bulb.is_on
    
