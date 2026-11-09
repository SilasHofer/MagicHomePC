import math
from . import shared_state
from colorsys import hsv_to_rgb, rgb_to_hsv
from flux_led import BulbScanner, WifiLedBulb
from . import bulb_actions
from . import device_repository
from . import theme
import logging
import threading
import tkinter as tk

# Handle user click on the color wheel
def on_color_select(event,canvas,marker,red_input,green_input,blue_input):
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
            bulb_actions.change_color(red_var=tk.StringVar(value=color[0]), green_var=tk.StringVar(value=color[1]), blue_var=tk.StringVar(value=color[2]),canvas=canvas,marker=marker)
            update_rgb_values(red_input,green_input,blue_input,color[0], color[1], color[2])
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
    colors = shared_state.bulb.getRgb()
    red, green, blue = [c / 255 for c in bulb_actions.apply_color_order(colors[0], colors[1], colors[2], shared_state.current_device_info)]  # Normalize RGB to 0–1
    hue, saturation, _ = rgb_to_hsv(red, green, blue)

    # Convert HSV to position on the canvas
    angle = hue * 360  # Hue in degrees
    distance = saturation * radius
    x = int(radius + distance * math.cos(math.radians(angle)))
    y = int(radius + distance * math.sin(math.radians(angle)))
    canvas.coords(marker,x - point_size, y - point_size, x + point_size, y + point_size)


def try_to_connect(ip,message_label):
    try:
        WifiLedBulb(ip)
        theme.set_message(message_label, "Connection successful", "success")
        return True
    except ConnectionRefusedError as e:
        theme.set_message(message_label, "Network error: the bulb refused the connection", "error")
        logging.error(f"Connection Refused for IP: {ip}")
    except Exception as e:
        theme.set_message(message_label, "Could not reach the bulb", "error")
        logging.error(f"Unexpected error when connecting to {ip}: {e}")
    return False


def update_device_list(tree):
    # Get the devices from the CSV and update the Treeview
    try:
        devices = device_repository.read_from_csv()

    except Exception as e:
        logging.error(f"Failed to read devices: {e}")
        return
    
    for row in tree.get_children():
        tree.delete(row)  # Clear previous rows
    row = 0
    for device in devices:
        tree.insert("", "end", values=(device[0], device[1], device[3], "Delete"),
                    tags=("odd" if row % 2 else "even",))
        row += 1

    saved_ips = {device[1] for device in devices}
    for ip in getattr(tree, "discovered", []):
        if ip not in saved_ips:
            tree.insert("", "end", values=(f"Light {ip.split('.')[-1]}", ip, "—", "+ Add"),
                        tags=("odd" if row % 2 else "even", "found"))
            row += 1


def scan_network(window, tree, message_label, scan_button, timeout=5):
    scan_button.config(state="disabled", text="Scanning...")
    theme.set_message(message_label, "Scanning the network...", "info")
    result = {}

    def worker():
        try:
            result["found"] = BulbScanner().scan(timeout=timeout)
        except Exception as e:
            result["error"] = e

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    def poll():
        if thread.is_alive():
            window.after(200, poll)
            return
        scan_button.config(state="normal", text="Scan network")
        if "error" in result:
            logging.error(f"Network scan failed: {result['error']}")
            theme.set_message(message_label, "Scan failed", "error")
            return
        tree.discovered = sorted(
            {info["ipaddr"] for info in result["found"] if info.get("ipaddr")},
            key=lambda ip: tuple(int(part) for part in ip.split(".")),
        )
        saved_ips = {device[1] for device in device_repository.read_from_csv()}
        new_count = len([ip for ip in tree.discovered if ip not in saved_ips])
        update_device_list(tree)
        if tree.discovered:
            theme.set_message(message_label, f"Found {len(tree.discovered)} bulb(s), {new_count} new. Click Add to use one.", "success")
        else:
            theme.set_message(message_label, "No bulbs answered. Are they powered on?", "warning")

    poll()



def save_device(name,ip, color_order,message_label,tree):
    if try_to_connect(ip.get(),message_label):
        if device_repository.save_to_csv(name.get(),ip.get(),"Flux",color_order.get()):
            update_device_list(tree)
            theme.set_message(message_label, "Device saved", "success")
            logging.info(f"Device {name.get()} ({ip.get()}) saved successfully.")
            shared_state.bulb = WifiLedBulb(ip.get())
            return True
        theme.set_message(message_label, "A device with this IP already exists", "error")
        return False
    logging.error(f"Failed to save device {name.get()} ({ip.get()}).")
    theme.set_message(message_label, "Connection failed", "error")
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