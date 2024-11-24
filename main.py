import sys
import time
import threading
import tkinter as tk
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
from flux_led import WifiLedBulb
import bulb_actions as action


# Function to create the system tray icon
def create_image():
    # Create an image with PIL (Python Imaging Library)
    width, height = 64, 64
    image = Image.open("pictures/icon.png")
    draw = ImageDraw.Draw(image)

    # Draw a simple circle (could be an icon)
    draw.ellipse((10, 10, width - 10, height - 10), fill=(255, 0, 0))  # Red circle

    return image

# Function to quit the application (stop the icon and exit)
def quit_action(icon):
    icon.stop()
    sys.exit()

# Function to open the Tkinter window for light control
def open_window(icon):
    bulb = WifiLedBulb("192.168.0.48")
    # Check if the window is already open
    if not hasattr(open_window, "window_opened") or not open_window.window_opened:
        open_window.window_opened = True

        # Create the Tkinter window
        window = tk.Tk()
        window.title("Magic Home Control")

        # Get the current position of the mouse
        x, y = window.winfo_pointerxy()

        # Set the window size
        window_width = 300
        window_height = 200

        # Calculate the position to open the window above the mouse
        # This will place the window slightly above the cursor
        x_position = x - (window_width // 2)  # Center the window over the cursor
        y_position = y - window_height - 10  # Position it above the mouse, with some padding

        # Set the window size and position
        window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        # List of devices (bulbs) to choose from in the dropdown
        devices = [
            ("Lampe", "192.168.0.48"),
            ("Tisch", "192.168.0.42"),
        ]  # You can replace this with your actual bulbs
        selected_device = tk.StringVar(window)
        selected_device.set(devices[0][0])  # Default value

        def get_ip_of_selected_device():
            selected_name = selected_device.get()
            for device in devices:
                if device[0] == selected_name:
                    return device[1]  # Return the IP address of the selected device
            return None  # If no match is found, return None

        def change_device(*args):
            ip = get_ip_of_selected_device()
            nonlocal bulb 
            bulb = WifiLedBulb(ip)


        selected_device.trace("w", change_device)

        # Dropdown menu to select a device
        device_dropdown = tk.OptionMenu(window, selected_device,  *[device[0] for device in devices])
        device_dropdown.pack(pady=10)

        # Turn on button
        turn_on_button = tk.Button(window, text="Turn On", command=lambda: action.turn_on(bulb))
        turn_on_button.pack(pady=10)

        # Turn off button
        turn_off_button = tk.Button(window, text="Turn Off", command=lambda: action.turn_off(bulb))
        turn_off_button.pack(pady=10)

        # Set Red button
        set_red_button = tk.Button(window, text="Set Red", command=lambda: action.set_red(bulb))
        set_red_button.pack(pady=10)

        set_white_button = tk.Button(window, text="Set white", command=lambda: action.set_white(bulb))
        set_white_button.pack(pady=10)

        # Set brightness button
        set_brightness_button = tk.Button(window, text="Set Brightness (50%)", command=lambda: action.set_brightness(bulb))
        set_brightness_button.pack(pady=10)

        # Quit button for the window
        quit_button = tk.Button(window, text="Quit", command=lambda: quit_action(icon))
        quit_button.pack(pady=10)


        # Handle window close event
        def on_close():
            open_window.window_opened = False  # Reset the flag when the window is closed
            window.destroy()  # Close the window

        # Bind the window close event to the on_close function
        window.protocol("WM_DELETE_WINDOW", on_close)
        # Start the Tkinter main loop
        window.mainloop()
    else:
        print("Window is already open.")

# Function to start the system tray
def run_tray():
    menu = Menu(
        MenuItem('Open Control Window', open_window),
        MenuItem('Quit', quit_action)
    )

    icon = Icon("Magic Home Control", create_image(), menu=menu)
    

    # Run the system tray icon
    icon.run()

# Run the system tray in a separate thread
if __name__ == "__main__":
    tray_thread = threading.Thread(target=run_tray)
    tray_thread.start()
