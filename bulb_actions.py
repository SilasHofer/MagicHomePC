# Function to turn on the light
def turn_on(bulb):
    bulb.turnOn()

# Function to turn off the light
def turn_off(bulb):
    bulb.turnOff()

# Function to change color to Red
def set_red(bulb):
    bulb.setRgb(255, 0, 0)  # Red color

def set_white(bulb):
    bulb.setRgb(255, 255, 255)

# Function to set brightness to 128 (50%)
def set_brightness(bulb):
    bulb.brightness == 128  # 50% brightness