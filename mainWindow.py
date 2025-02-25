import shared_state
from flux_led import WifiLedBulb
import tkinter as tk
import bulb_actions as action
import ui_helpers as help
import math
from colorsys import hsv_to_rgb, rgb_to_hsv
import functools
import sys
import DeviceManager
import csv_controller



# Function to open the Tkinter window for light control
def open_window(icon):
    try:
        shared_state.bulb = WifiLedBulb(csv_controller.read_from_csv()[0][1])
    except Exception as e:
        shared_state.is_connected = False
    
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
        window_height = 475

        # Calculate the position to open the window above the mouse
        # This will place the window slightly above the cursor
        x_position = x - (window_width // 2)  # Center the window over the cursor
        y_position = y - window_height -5  # Position it above the mouse, with some padding

        # Set the window size and position
        window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        frame = tk.Frame(window)
        frame.pack(pady=5)

            # Initialize device_dropdown (default to an empty menu)
        selected_device = tk.StringVar(window)
        selected_device.set("")  # Default value if no devices are connected
        selected_device_old = ""
        device_dropdown = tk.OptionMenu(frame, selected_device, "")
        device_dropdown.grid(row=0, column=2, padx=5, pady=10)

        frame_inside = tk.Frame(window)
        frame_inside.pack(pady=5)

        def update_dropdown():
            # Refresh the dropdown menu with updated devices
            new_devices = csv_controller.read_from_csv()
            menu = device_dropdown["menu"]
            menu.delete(0, "end")  # Clear existing items
            for device in new_devices:
                menu.add_command(
                    label=device[0],
                    command=tk._setit(selected_device, device[0])
                )
            try:
                selected_device.set(new_devices[0][0])
                shared_state.is_connected = True
            except Exception as e:
                shared_state.is_connected = False
                frame_inside.pack_forget()
                return
            return new_devices[0][0]

        # Add device
        Add_device = tk.Button(frame, text="Device manager", command=lambda: DeviceManager.open_add_device_window(icon,update_dropdown))
        Add_device.grid(row=0, column=1, padx=5)

        selected_device_old = update_dropdown()
        
        if(shared_state.is_connected == True):

            selected_device.trace("w", lambda *args: action.change_device(selected_device,selected_device_old, csv_controller.read_from_csv(),canvas,marker,red_var,green_var,blue_var,message_label))

            # Dropdown menu to select a device
            device_dropdown = tk.OptionMenu(frame_inside, selected_device,  *[device[0] for device in csv_controller.read_from_csv()])
            device_dropdown.grid(row=0, column=2, padx=5,pady=10)
            # Add the label to display messages
            message_label = tk.Label(frame_inside, text="", fg="black")
            message_label.grid(row=1, column=1, columnspan=2, pady=5)
            # Toggle on/off button
            turn_on_button = tk.Button(frame_inside, text="Toggle on/off", command=lambda: action.Toggle_bulb())
            turn_on_button.grid(row=2, column=1, padx=5)

            # turn On all button
            turn_on_button = tk.Button(frame_inside, text="turn On all", command=lambda: action.turn_on_all_bulbs(csv_controller.read_from_csv()))
            turn_on_button.grid(row=2, column=2, padx=5)

            # turn off all button
            turn_on_button = tk.Button(frame_inside, text="turn off all", command=lambda: action.turn_off_all_bulbs(csv_controller.read_from_csv()))
            turn_on_button.grid(row=2, column=3, padx=5)

            # Create the canvas for the color wheel
            canvas = tk.Canvas(window, width=shared_state.canvas_size, height=shared_state.canvas_size, bg=window["bg"], highlightthickness=0)
            canvas.pack(pady=10)

            # Draw the color wheel
            radius = shared_state.canvas_size // 2
        
            for x in range(shared_state.canvas_size):
                for y in range(shared_state.canvas_size):
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
            marker = canvas.create_oval(x - shared_state.point_size, y - shared_state.point_size, x + shared_state.point_size, y + shared_state.point_size, fill="white", outline="black")

            # Create a frame_inside to hold the RGB input boxes on one line
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


            red_var.trace_add("write", functools.partial(action.change_color, red_var=red_var, green_var=green_var, blue_var=blue_var,canvas=canvas,marker=marker))
            green_var.trace_add("write", functools.partial(action.change_color, red_var=red_var, green_var=green_var, blue_var=blue_var,canvas=canvas,marker=marker))
            blue_var.trace_add("write", functools.partial(action.change_color, red_var=red_var, green_var=green_var, blue_var=blue_var,canvas=canvas,marker=marker))

            # Red Input Box
            red_input = tk.Entry(frame_rgb, textvariable=red_var, validate="key", validatecommand=(validate_command, "%P"), width=5)
            red_input.grid(row=2, column=0, padx=5)

            # Green Input Box
            green_input = tk.Entry(frame_rgb, textvariable=green_var, validate="key", validatecommand=(validate_command, "%P"), width=5)
            green_input.grid(row=2, column=1, padx=5)

            # Blue Input Box
            blue_input = tk.Entry(frame_rgb, textvariable=blue_var, validate="key", validatecommand=(validate_command, "%P"), width=5)
            blue_input.grid(row=2, column=2, padx=5)

            initial_brightness = tk.DoubleVar(value=action.get_brightness() * 100)

            # Add a slider for brightness control
            brightness_slider = tk.Scale(
                window,
                from_=1,
                to=100,
                orient=tk.HORIZONTAL,  # Horizontal slider
                label="Brightness (%)",  # Label for the slider
                length=200,  # Length of the slider in pixels
                variable=initial_brightness,
                command=lambda value: action.set_brightness(float(value))  # Call set_brightness on change
            )

            brightness_slider.pack(pady=10)


            canvas.bind("<Button-1>", lambda event: help.on_color_select(event,canvas,marker,red_var,green_var,blue_var))

        # Quit button for the window
        quit_button = tk.Button(window, text="Quit", command=lambda: quit_action(icon))
        quit_button.pack(pady=10)

                # Function to quit the application (stop the icon and exit)
        def quit_action(icon):
            icon.stop()
            sys.exit()

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
