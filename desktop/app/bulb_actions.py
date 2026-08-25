from flux_led import WifiLedBulb
from colorsys import rgb_to_hsv
import numpy as np
import math

from .ui_helpers import move_white_point, update_rgb_values
from . import shared_state

# Function to turn on the light
def Toggle_bulb():
    if(get_status()):
        shared_state.bulb.turnOff()
    else:
        shared_state.bulb.turnOn()


def turn_off_all_bulbs(devices):
    for device in devices:
        if device[2] == "Flux":
            bulb = WifiLedBulb(device[1])
            bulb.turnOff()

def turn_on_all_bulbs(devices):
    for device in devices:
        if device[2] == "Flux":
            shared_state.bulb = WifiLedBulb(device[1])
            shared_state.bulb.turnOn()


# Function to change color to Red
def set_rgb(color):
    shared_state.bulb.setRgb(color[0],color[1],color[2])

def set_brightness(brightness):
    # brightness: 0-100
    if shared_state.bulb is None:
        return

    # normalize brightness to 0.0 - 1.0
    b = max(0.0, min(float(brightness) / 100.0, 1.0))

    # Get device RGB (device channel order) and map to UI-order (R,G,B)
    device_rgb = shared_state.bulb.getRgb()
    order = shared_state.current_device_info or "RGB"  # e.g. "GRB"
    # build mapping from order -> value
    mapping = {}
    for ch, val in zip(order, device_rgb):
        mapping[ch] = val
    ui_r = mapping.get('R', 0)
    ui_g = mapping.get('G', 0)
    ui_b = mapping.get('B', 0)

    # if everything is zero, nothing to scale
    max_val = max(ui_r, ui_g, ui_b)
    if max_val == 0:
        # bulb is off or black - set scaled color to 0
        scaled_r = scaled_g = scaled_b = 0
    else:
        # scale so the brightest channel goes to 255, then apply brightness fraction
        scale = 255.0 / max_val
        scaled_r = min(255, math.ceil(ui_r * scale * b))
        scaled_g = min(255, math.ceil(ui_g * scale * b))
        scaled_b = min(255, math.ceil(ui_b * scale * b))

    # convert UI-order back to device-order before sending
    # apply_color_order expects (r,g,b, order), where order is device order like "GRB"
    r_dev, g_dev, b_dev = apply_color_order(scaled_r, scaled_g, scaled_b, order)

    shared_state.bulb.setRgb(r_dev, g_dev, b_dev)


def get_brightness():
    if(shared_state.bulb is None):
        return 0
    color = shared_state.bulb.getRgb()
    color_array = np.array(color)
    max = color_array.max()
    return max/255

def get_status():
    return shared_state.bulb.is_on

def get_color():
    if(shared_state.bulb is None):
        return (0, 0, 0)
    return shared_state.bulb.getRgb()

def change_color(*args,red_var, green_var, blue_var,canvas,marker):
    try:
        if(shared_state.system_change == False):
            red = int(red_var.get())
            green = int(green_var.get())
            blue = int(blue_var.get())

            r, g, b = apply_color_order(red, green, blue, shared_state.current_device_info)
            set_rgb((r,g,b))
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
            return device[1], device[3]  # Return the IP address and color order of the selected device
    return None  # If no match is found, return None

def change_device(selected_device,selected_device_old,devices,canvas,marker,red_input,green_input,blue_input,message_label):
    ip,color_order = get_ip_of_selected_device(selected_device,devices)
    try:
        shared_state.bulb = WifiLedBulb(ip)
        shared_state.current_device_info = color_order
    except Exception as e:
        message_label.config(text="no connection", fg="red")
        selected_device.set(selected_device_old)
        return

    color = get_color()
    
    move_white_point(canvas,marker)
    update_rgb_values(red_input,green_input,blue_input,color[0], color[1], color[2])
    message_label.config(text="", fg="red")
    selected_device_old = selected_device.get()

def apply_color_order(r, g, b, order):
    # Normalize and validate order
    if order is None:
        order = "RGB"
    order = str(order).upper()
    if len(order) != 3 or set(order) != set("RGB"):
        order = "RGB"

    # Ensure numeric ints and clamp into 0-255
    def clamp(v):
        try:
            vi = int(v)
        except Exception:
            vi = 0
        return max(0, min(255, vi))

    mapping = {'R': clamp(r), 'G': clamp(g), 'B': clamp(b)}
    return tuple(mapping[c] for c in order)