import sys
import math
import time
import threading
import tkinter as tk
from colorsys import hsv_to_rgb, rgb_to_hsv
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
from flux_led import WifiLedBulb
import bulb_actions as action
import shared_state
import help_funktions as help


# Function to create the system tray icon
def create_image():
    # Create an image with PIL (Python Imaging Library)
    width, height = 64, 64
    image = Image.open("pictures\icon.png")
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
    shared_state.bulb = WifiLedBulb("192.168.0.48")
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
        window_height = 400

        # Calculate the position to open the window above the mouse
        # This will place the window slightly above the cursor
        x_position = x - (window_width // 2)  # Center the window over the cursor
        y_position = y - window_height - 10  # Position it above the mouse, with some padding

        # Set the window size and position
        window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")


        frame = tk.Frame(window)
        frame.pack(pady=5)

        # List of devices (bulbs) to choose from in the dropdown
        devices = [
            ("Lampe", "192.168.0.48"),
            ("Tisch", "192.168.0.42"),
        ]  # You can replace this with your actual bulbs
        selected_device = tk.StringVar(window)
        selected_device.set(devices[0][0])  # Default value

        selected_device.trace("w", lambda *args: action.change_device(selected_device, devices,canvas,marker,point_size,radius,red_var,green_var,blue_var))

        # Dropdown menu to select a device
        device_dropdown = tk.OptionMenu(frame, selected_device,  *[device[0] for device in devices])
        device_dropdown.grid(row=0, column=2, padx=5,pady=10)

        # Toggle on/off button
        turn_on_button = tk.Button(frame, text="Toggle on/off", command=lambda: action.Toggle_bulb())
        turn_on_button.grid(row=1, column=1, padx=5)

        # turn On all button
        turn_on_button = tk.Button(frame, text="turn On all", command=lambda: action.turn_on_all_bulbs(devices))
        turn_on_button.grid(row=1, column=2, padx=5)

        # turn off all button
        turn_on_button = tk.Button(frame, text="turn off all", command=lambda: action.turn_off_all_bulbs(devices))
        turn_on_button.grid(row=1, column=3, padx=5)

        # Create the canvas for the color wheel
        canvas_size = 150
        canvas = tk.Canvas(window, width=canvas_size, height=canvas_size, bg=window["bg"], highlightthickness=0)
        canvas.pack(pady=10)

        # Draw the color wheel
        radius = canvas_size // 2
    
        for x in range(canvas_size):
            for y in range(canvas_size):
                dx = x - radius
                dy = y - radius
                distance = (dx**2 + dy**2)**0.5
                if distance <= radius:  # Point is inside the circle
                    # Calculate hue and saturation
                    angle = math.degrees(math.atan2(dy, dx)) % 360
                    hue = angle / 360
                    saturation = distance / radius
                    red, green, blue = hsv_to_rgb(hue, saturation, 1)
                    color = "#{:02x}{:02x}{:02x}".format(int(red * 255), int(green * 255), int(blue * 255))
                    canvas.create_line(x, y, x + 1, y, fill=color)  # Draw pixel
        
            # Convert RGB to HSV
        red, green, blue = [c / 255 for c in action.get_color()]  # Normalize RGB to 0–1
        hue, saturation, _ = rgb_to_hsv(red, green, blue)

        # Convert HSV to position on the canvas
        angle = hue * 360  # Hue in degrees
        distance = saturation * radius
        x = int(radius + distance * math.cos(math.radians(angle)))
        y = int(radius + distance * math.sin(math.radians(angle)))

        # Draw a white point
        point_size = 3  # Size of the marker
        marker = canvas.create_oval(x - point_size, y - point_size, x + point_size, y + point_size, fill="white", outline="black")



        # Create a frame to hold the RGB input boxes on one line
        frame_rgb = tk.Frame(window)
        frame_rgb.pack(pady=5)

        # Label for RGB
        tk.Label(frame_rgb, text="RGB (0-255):").grid(row=0, column=1, padx=5)

        # Create validation command
        validate_command = window.register(help.validate_rgb_input)

        color = action.get_color()

        # Dedicated StringVar for each input box
        red_var = tk.StringVar(value=color[0])
        green_var = tk.StringVar(value=color[1])
        blue_var = tk.StringVar(value=color[2])

        # Red Input Box
        red_input = tk.Entry(frame_rgb, textvariable=red_var, validate="key", validatecommand=(validate_command, "%P"), width=5)
        red_input.grid(row=2, column=0, padx=5)

        # Green Input Box
        green_input = tk.Entry(frame_rgb, textvariable=green_var, validate="key", validatecommand=(validate_command, "%P"), width=5)
        green_input.grid(row=2, column=1, padx=5)

        # Blue Input Box
        blue_input = tk.Entry(frame_rgb, textvariable=blue_var, validate="key", validatecommand=(validate_command, "%P"), width=5)
        blue_input.grid(row=2, column=2, padx=5)


        # Set brightness button
        set_brightness_button = tk.Button(window, text="Set Brightness (50%)", command=lambda: action.set_brightness())
        set_brightness_button.pack(pady=10)


        canvas.bind("<Button-1>", lambda event: help.on_color_select(event, radius, canvas,marker,point_size))

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

    icon = Icon(name="Magic Home Control",icon=create_image(),title="Magic Home Control",menu=Menu(
    MenuItem(text="Left-Click-Action",action=open_window,default=True),
    MenuItem(text="Quit", action=quit_action)
))


    # Run the system tray icon
    icon.run()

# Run the system tray in a separate thread
if __name__ == "__main__":
    tray_thread = threading.Thread(target=run_tray)
    tray_thread.start()
