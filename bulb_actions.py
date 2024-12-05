from flux_led import WifiLedBulb
from colorsys import rgb_to_hsv

import help_funktions as help
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
    color = shared_state.bulb.getRgbw()
    shared_state.bulb.setRgb(color[0],color[1],color[2],color[3],brightness)

def get_brightness():
    print(shared_state.bulb.raw_state)

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
            help.move_white_point(canvas,marker)
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

def change_device(selected_device,devices,canvas,marker,red_input,green_input,blue_input):
    ip = get_ip_of_selected_device(selected_device,devices)
    shared_state.bulb = WifiLedBulb(ip)
    color = get_color()

    help.move_white_point(canvas,marker)
    help.update_rgb_values(red_input,green_input,blue_input,color[0], color[1], color[2])