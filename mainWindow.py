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
        print(f"Error connecting to bulb: {e}")
    
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

        selected_device = tk.StringVar(window)
        selected_device.set("")  # Default value if no devices are connected
        selected_device_old = ""

        # Set the window size and position
        window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        frame_device = tk.Frame(window)
        frame_device.pack(pady=5)

        frame_top = tk.Frame(window)
        frame_top.pack(pady=2)

        # Add Device button (always visible)
        Add_device = tk.Button(frame_top, text="Device manager", command=lambda: DeviceManager.open_add_device_window(icon, update_dropdown))
        Add_device.grid(row=0, column=1, padx=5)

        # Placeholder for device_dropdown
        device_dropdown = None

        frame_inside = tk.Frame(window)
        frame_inside.pack(pady=5)

        def render_device_controls(show_controls, device_dropdown):
            # Remove old dropdown if it exists
            if device_dropdown is not None:
                device_dropdown.destroy()
                device_dropdown = None

            # Clear previous widgets in frame_inside
            for widget in frame_inside.winfo_children():
                widget.destroy()

            message_label = tk.Label(frame_inside, text="", fg="black")
            message_label.grid(row=1, column=1, columnspan=2, pady=5)
            if not show_controls:
                message_label.config(text="No devices connected", fg="red")
                return


            # Device dropdown (created/destroyed with controls)
            device_dropdown = tk.OptionMenu(frame_top, selected_device, *[device[0] for device in csv_controller.read_from_csv()])
            device_dropdown.grid(row=0, column=2, padx=5, pady=10)

            # Toggle buttons
            tk.Button(frame_inside, text="Toggle on/off", command=lambda: action.Toggle_bulb()).grid(row=2, column=1, padx=5)
            tk.Button(frame_inside, text="Turn On all", command=lambda: action.turn_on_all_bulbs(csv_controller.read_from_csv())).grid(row=2, column=2, padx=5)
            tk.Button(frame_inside, text="Turn off all", command=lambda: action.turn_off_all_bulbs(csv_controller.read_from_csv())).grid(row=2, column=3, padx=5)

            # --- Color wheel canvas ---
            canvas = tk.Canvas(frame_inside, width=shared_state.canvas_size, height=shared_state.canvas_size, bg=window["bg"], highlightthickness=0)
            canvas.grid(row=3, column=1, columnspan=3, pady=10)
            radius = shared_state.canvas_size // 2
            for x in range(shared_state.canvas_size):
                for y in range(shared_state.canvas_size):
                    dx = x - radius
                    dy = y - radius
                    distance = (dx**2 + dy**2)**0.5
                    if distance <= radius:
                        angle = math.degrees(math.atan2(dy, dx)) % 360
                        hue = angle / 360
                        saturation = distance / radius
                        red, green, blue = hsv_to_rgb(hue, saturation, 1)
                        color = "#{:02x}{:02x}{:02x}".format(int(red * 255), int(green * 255), int(blue * 255))
                        canvas.create_line(x, y, x + 1, y, fill=color)
            # Marker for current color
            red, green, blue = [c / 255 for c in action.get_color()]
            hue, saturation, _ = rgb_to_hsv(red, green, blue)
            angle = hue * 360
            distance = saturation * radius
            x = int(radius + distance * math.cos(math.radians(angle)))
            y = int(radius + distance * math.sin(math.radians(angle)))
            marker = canvas.create_oval(
                x - shared_state.point_size, y - shared_state.point_size,
                x + shared_state.point_size, y + shared_state.point_size,
                fill="white", outline="black"
            )

            # --- RGB input frame ---
            frame_rgb = tk.Frame(frame_inside)
            frame_rgb.grid(row=4, column=1, columnspan=3, pady=5)
            tk.Label(frame_rgb, text="RGB (0-255):").grid(row=0, column=1, padx=5)
            validate_command = window.register(help.validate_rgb_input)
            color = action.get_color()
            red_var = tk.StringVar(value=color[0])
            green_var = tk.StringVar(value=color[1])
            blue_var = tk.StringVar(value=color[2])
            red_var.trace_add("write", functools.partial(action.change_color, red_var=red_var, green_var=green_var, blue_var=blue_var, canvas=canvas, marker=marker))
            green_var.trace_add("write", functools.partial(action.change_color, red_var=red_var, green_var=green_var, blue_var=blue_var, canvas=canvas, marker=marker))
            blue_var.trace_add("write", functools.partial(action.change_color, red_var=red_var, green_var=green_var, blue_var=blue_var, canvas=canvas, marker=marker))
            tk.Entry(frame_rgb, textvariable=red_var, validate="key", validatecommand=(validate_command, "%P"), width=5).grid(row=2, column=0, padx=5)
            tk.Entry(frame_rgb, textvariable=green_var, validate="key", validatecommand=(validate_command, "%P"), width=5).grid(row=2, column=1, padx=5)
            tk.Entry(frame_rgb, textvariable=blue_var, validate="key", validatecommand=(validate_command, "%P"), width=5).grid(row=2, column=2, padx=5)

            # --- Brightness slider ---
            initial_brightness = tk.DoubleVar(value=action.get_brightness() * 100)
            brightness_slider = tk.Scale(
                frame_inside,
                from_=1,
                to=100,
                orient=tk.HORIZONTAL,
                label="Brightness (%)",
                length=200,
                variable=initial_brightness,
                command=lambda value: action.set_brightness(float(value))
            )
            brightness_slider.grid(row=5, column=1, columnspan=3, pady=10)

            canvas.bind("<Button-1>", lambda event: help.on_color_select(event, canvas, marker, red_var, green_var, blue_var))
            selected_device.trace_add("write", lambda *args: action.change_device(
                selected_device,
                selected_device_old,
                csv_controller.read_from_csv(),
                canvas,
                marker,
                red_var,
                green_var,
                blue_var,
                message_label
            ))
            return device_dropdown  # <-- return the new dropdown

        def update_dropdown():
            new_devices = csv_controller.read_from_csv()
            nonlocal device_dropdown

            if new_devices:
                device_dropdown = render_device_controls(True, device_dropdown)
                menu = device_dropdown["menu"]
                menu.delete(0, "end")
                for device in new_devices:
                    menu.add_command(
                        label=device[0],
                        command=tk._setit(selected_device, device[0])
                    )
                try:
                    selected_device.set(new_devices[0][0])
                except Exception as e:
                    print(f"Error setting selected device: {e}")
                    device_dropdown = render_device_controls(False, device_dropdown)
                    return
                return new_devices[0][0]
            else:
                print(f"No device dropdown found")
                device_dropdown = render_device_controls(False, device_dropdown)
                return

        # Add device
        Add_device = tk.Button(frame_top, text="Device manager", command=lambda: DeviceManager.open_add_device_window(icon, update_dropdown))
        Add_device.grid(row=0, column=1, padx=5)

        selected_device_old = update_dropdown()

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
