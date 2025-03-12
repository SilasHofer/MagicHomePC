import math
import shared_state
from colorsys import hsv_to_rgb, rgb_to_hsv
from flux_led import WifiLedBulb
import csv_controller
import logging
import tinytuya
import json

# Handle user click on the color wheel
def on_color_select(event,canvas,marker,red_input,green_input,blue_input):
    from color_controller import apply_color_change
    radius = shared_state.canvas_size // 2
    dx = event.x - radius
    dy = event.y - radius
    distance = (dx**2 + dy**2)**0.5
    if distance <= radius:  # Check if click is inside the wheel
        angle = math.degrees(math.atan2(dy, dx)) % 3600
        hue = angle / 360
        saturation = distance / radius
        red, green, blue = hsv_to_rgb(hue, saturation, 1)
        color = (int(red * 255), int(green * 255), int(blue * 255))
        if shared_state.bulb:
            apply_color_change(color,canvas,marker,red_input,green_input,blue_input)
            logging.info(f"User selected color: {color}") 

            

def update_rgb_values(red_var,green_var,blue_var,new_red, new_green, new_blue):
    """Update the RGB input boxes with new values."""
    shared_state.system_change = True
    red_var.set(new_red)
    shared_state.system_change = True
    green_var.set(new_green)
    shared_state.system_change = True
    blue_var.set(new_blue)


def move_white_point(canvas,marker):
        # Convert RGB to HSV
    point_size = shared_state.point_size
    radius = shared_state.canvas_size // 2
    red, green, blue = [c / 255 for c in shared_state.bulb.getRgb()]  # Normalize RGB to 0–1
    hue, saturation, _ = rgb_to_hsv(red, green, blue)

    # Convert HSV to position on the canvas
    angle = hue * 360  # Hue in degrees
    distance = saturation * radius
    x = int(radius + distance * math.cos(math.radians(angle)))
    y = int(radius + distance * math.sin(math.radians(angle)))
    canvas.coords(marker,x - point_size, y - point_size, x + point_size, y + point_size)


def try_to_connect(ip,message_label):
    try:
        bulb = WifiLedBulb(ip)
        if bulb.is_on:  # Check if the bulb is responding
            message_label.config(text="Connection Successful", fg="green")
            return True
        else:
            message_label.config(text="Bulb found but not responding", fg="orange")
            return False
    except ConnectionRefusedError as e:
        message_label.config(text="Network Error", fg="red")
        logging.error(f"Connection Refused for IP: {ip}")
    except Exception as e:
        message_label.config(text="Unexpected Error", fg="red")
        logging.error(f"Unexpected error when connecting to {ip}: {e}")
    return False


def update_device_list(tree):
    # Get the devices from the CSV and update the Treeview
    try:
        devices = csv_controller.read_from_csv()
    except Exception as e:
        logging.error(f"Failed to read devices: {e}")
        return
    
    for row in tree.get_children():
        tree.delete(row)  # Clear previous rows
    for device in devices:
        tree.insert("", "end", values=(device[0], device[1],device[2], "DELETE"))



def save_device(name,ip,message_label,tree):
    if try_to_connect(ip.get(),message_label):
        if csv_controller.save_to_csv(name.get(),ip.get()," Flux"):
            update_device_list(tree)
            message_label.config(text="Device Saved", fg="green")
            logging.info(f"Device {name.get()} ({ip.get()}) saved successfully.")
            return True
    logging.error(f"Failed to save device {name.get()} ({ip.get()}).")
    return False

        # Function to validate the input (only allow digits and limit the length to 3 digits)
def validate_rgb_input(P):
    # Allow empty input (to delete the current value)
    if P == "":
        return True
    # Allow only digits and ensure the value is between 0 and 255
    if P.isdigit() and len(P) <= 3:
        value = int(P)
        if 0 <= value <= 255:  # Ensure the number is between 0 and 255
            return True
    return False

def Scan_tuya_devices(tree):
    tinytuya.scan()
    # Open and read the snapshot file
    with open('snapshot.json', 'r') as f:
        devices = json.load(f)
    for device in devices['devices']:
        tree.insert("", "end", values=(device.get('id'), device.get('ip'), "ADD"))
