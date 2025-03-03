from flux_led import WifiLedBulb
from colorsys import rgb_to_hsv
import numpy as np
import math

from ui_helpers import move_white_point, update_rgb_values
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

def set_brightness(brightness):

    brightness = brightness/100

    color = shared_state.bulb.getRgb()
    color_array = np.array(color)
    max = color_array.max()


    multpilicator =  255/max

    red = math.ceil(color[0]*multpilicator*brightness)
    blue = math.ceil(color[1]*multpilicator*brightness)
    green = math.ceil(color[2]*multpilicator*brightness)

    if(red == 256):
        red = 255
    if(blue == 256):
        blue = 255
    if(green == 256):
        green = 255

    shared_state.bulb.setRgb(red,blue,green)


def get_brightness():
    color = shared_state.bulb.getRgb()
    color_array = np.array(color)
    max = color_array.max()
    return max/255

def get_status():
    return shared_state.bulb.is_on

def get_color():
    return shared_state.bulb.getRgb()

def change_color(*args,red_var, green_var, blue_var,canvas,marker):
    try:
        if(shared_state.system_change == False):
            red = int(red_var.get())
            green = int(green_var.get())
            blue = int(blue_var.get())
            set_rgb((red,green,blue))
            move_white_point(canvas,marker)
        else:
            shared_state.system_change = False
        # Call your desired function here
    except ValueError:
        # Handle case where input is not a valid integer
        print("Invalid RGB input.")


def get_ip_of_selected_device(selected_device,devices):
    selected_name = selected_device.get()
    for device in devices:
        if device[0] == selected_name:
            return device[1]  # Return the IP address of the selected device
    return None  # If no match is found, return None

def change_device(selected_device,selected_device_old,devices,canvas,marker,red_input,green_input,blue_input,message_label):
    ip = get_ip_of_selected_device(selected_device,devices)
    try:
        shared_state.bulb = WifiLedBulb(ip)
    except Exception as e:
        message_label.config(text="no connection", fg="red")
        selected_device.set(selected_device_old)
        return

    color = get_color()

    move_white_point(canvas,marker)
    update_rgb_values(red_input,green_input,blue_input,color[0], color[1], color[2])
    message_label.config(text="", fg="red")
    selected_device_old = selected_device.get()