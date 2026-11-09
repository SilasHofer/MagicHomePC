from . import shared_state
from flux_led import WifiLedBulb
import tkinter as tk
from tkinter import ttk
from . import bulb_actions as action
from . import ui_helpers as help
import math
from colorsys import hsv_to_rgb, rgb_to_hsv
import functools
import sys
from . import DeviceManager
from . import device_repository
from . import theme

WINDOW_WIDTH = 360


def draw_color_wheel(size, background):
    """Render the HSV color wheel once into an image (much faster than one canvas line per pixel)."""
    image = tk.PhotoImage(width=size, height=size)
    radius = size // 2
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            dx = x - radius
            dy = y - radius
            distance = (dx**2 + dy**2)**0.5
            if distance <= radius:
                hue = (math.degrees(math.atan2(dy, dx)) % 360) / 360
                red, green, blue = hsv_to_rgb(hue, distance / radius, 1)
                row.append("#{:02x}{:02x}{:02x}".format(int(red * 255), int(green * 255), int(blue * 255)))
            else:
                row.append(background)
        rows.append("{" + " ".join(row) + "}")
    image.put(" ".join(rows))
    return image


# Function to open the Tkinter window for light control
def open_window(icon):
    # Check if the window is already open
    if not hasattr(open_window, "window_opened") or not open_window.window_opened:
        open_window.window_opened = True

        # Create the Tkinter window
        window = tk.Tk()
        window.title("Magic Home Control")
        theme.apply_theme(window)
        window.resizable(False, False)

        selected_device = tk.StringVar(window)
        selected_device.set("")  # Default value if no devices are connected
        selected_device_old = ""
        device_trace = None  # id of the trace on selected_device, so it can be replaced on re-render

        page = ttk.Frame(window, padding=(20, 18))
        page.pack(fill="both", expand=True)

        # --- Header ---
        header = ttk.Frame(page)
        header.pack(fill="x")
        titles = ttk.Frame(header)
        titles.pack(side="left")
        ttk.Label(titles, text="MAGIC HOME", style="Kicker.TLabel").pack(anchor="w")
        ttk.Label(titles, text="Control", style="Title.TLabel").pack(anchor="w")
        ttk.Button(header, text="Devices",
                   command=lambda: DeviceManager.open_add_device_window(icon, update_dropdown)
                   ).pack(side="right")

        # --- Device selector ---
        ttk.Label(page, text="DEVICE", style="Muted.TLabel").pack(anchor="w", pady=(16, 4))
        device_dropdown = ttk.Combobox(page, textvariable=selected_device, state="readonly")
        device_dropdown.pack(fill="x")

        # --- Footer (packed before the expanding area so it always stays visible) ---
        footer = ttk.Frame(page)
        footer.pack(fill="x", side="bottom", pady=(12, 0))
        ttk.Button(footer, text="Quit", style="Danger.TButton",
                   command=lambda: quit_action(icon)).pack(side="right")

        # Area that holds the controls (rebuilt when the device list changes)
        frame_inside = ttk.Frame(page)
        frame_inside.pack(fill="both", expand=True, pady=(14, 0))

        # The wheel image is the same every time, so draw it once per window
        wheel_image = draw_color_wheel(shared_state.canvas_size, theme.SURFACE)

        def render_device_controls(show_controls):
            nonlocal device_trace

            # Clear previous widgets in frame_inside
            for widget in frame_inside.winfo_children():
                widget.destroy()

            # Remove the trace from the previous render; it points at destroyed widgets
            if device_trace is not None:
                selected_device.trace_remove("write", device_trace)
                device_trace = None

            message_label = theme.message_label(frame_inside)

            if not show_controls:
                empty = ttk.Frame(frame_inside, style="Card.TFrame", padding=24)
                empty.pack(fill="both", expand=True)
                ttk.Label(empty, text="No devices connected", style="Card.TLabel",
                          font=theme.font(12, "bold")).pack(pady=(40, 6))
                ttk.Label(empty, text="Open Devices to add a light or scan your network.",
                          style="Card.TLabel", foreground=theme.MUTED, wraplength=260,
                          justify="center").pack()
                device_dropdown["values"] = ()
                return

            # --- Color card ---
            card = ttk.Frame(frame_inside, style="Card.TFrame", padding=16)
            card.pack(fill="x")

            card_header = ttk.Frame(card, style="Card.TFrame", padding=0)
            card_header.configure(borderwidth=0)
            card_header.pack(fill="x")
            ttk.Label(card_header, text="COLOR", style="CardMuted.TLabel").pack(side="left")
            hex_label = ttk.Label(card_header, text="", style="Value.TLabel")
            hex_label.pack(side="right")
            swatch = tk.Frame(card_header, width=14, height=14, bg=theme.SURFACE,
                              highlightthickness=1, highlightbackground=theme.BORDER_STRONG)
            swatch.pack(side="right", padx=(0, 8))

            # Color wheel
            canvas = tk.Canvas(card, width=shared_state.canvas_size, height=shared_state.canvas_size,
                               bg=theme.SURFACE, highlightthickness=0, cursor="crosshair")
            canvas.pack(pady=(12, 12))
            canvas.create_image(0, 0, anchor="nw", image=wheel_image)
            canvas.image = wheel_image  # keep a reference so Tk does not drop the image

            # Marker for current color
            radius = shared_state.canvas_size // 2
            red, green, blue = [c / 255 for c in action.get_color()]
            hue, saturation, _ = rgb_to_hsv(red, green, blue)
            distance = saturation * radius
            x = int(radius + distance * math.cos(math.radians(hue * 360)))
            y = int(radius + distance * math.sin(math.radians(hue * 360)))
            point = shared_state.point_size
            marker = canvas.create_oval(x - point, y - point, x + point, y + point,
                                        outline="white", width=3)

            # RGB inputs
            rgb_row = ttk.Frame(card, style="Card.TFrame", padding=0)
            rgb_row.configure(borderwidth=0)
            rgb_row.pack(fill="x")
            rgb_row.columnconfigure((0, 1, 2), weight=1)

            validate_command = window.register(help.validate_rgb_input)
            color = action.get_color()
            red_var = tk.StringVar(value=color[0])
            green_var = tk.StringVar(value=color[1])
            blue_var = tk.StringVar(value=color[2])

            for column, (letter, var) in enumerate((("R", red_var), ("G", green_var), ("B", blue_var))):
                ttk.Label(rgb_row, text=letter, style="CardMuted.TLabel").grid(row=0, column=column, sticky="w",
                                                                               padx=(0 if column == 0 else 6, 0))
                ttk.Entry(rgb_row, textvariable=var, validate="key", validatecommand=(validate_command, "%P"),
                          width=5, justify="center").grid(row=1, column=column, sticky="ew", pady=(3, 0),
                                                          padx=(0 if column == 0 else 6, 0))
                var.trace_add("write", functools.partial(action.change_color, red_var=red_var, green_var=green_var,
                                                         blue_var=blue_var, canvas=canvas, marker=marker))

            # Swatch and hex value follow the RGB fields
            def update_swatch(*args):
                try:
                    values = [max(0, min(255, int(var.get()))) for var in (red_var, green_var, blue_var)]
                except ValueError:
                    return
                hex_value = "#{:02x}{:02x}{:02x}".format(*values)
                swatch.config(bg=hex_value)
                hex_label.config(text=hex_value.upper())

            for var in (red_var, green_var, blue_var):
                var.trace_add("write", update_swatch)
            update_swatch()

            # --- Brightness ---
            brightness_header = ttk.Frame(card, style="Card.TFrame", padding=0)
            brightness_header.configure(borderwidth=0)
            brightness_header.pack(fill="x", pady=(16, 4))
            ttk.Label(brightness_header, text="BRIGHTNESS", style="CardMuted.TLabel").pack(side="left")
            brightness_value = ttk.Label(brightness_header, text="", style="Value.TLabel")
            brightness_value.pack(side="right")

            initial_brightness = tk.DoubleVar(value=action.get_brightness() * 100)

            # The label follows the slider, whether the user moves it or the app sets it
            def update_brightness_label(*args):
                brightness_value.config(text=f"{round(initial_brightness.get())}%")

            initial_brightness.trace_add("write", update_brightness_label)
            update_brightness_label()

            def on_brightness(value):
                action.set_brightness(float(value))

            brightness_slider = ttk.Scale(card, from_=1, to=100, orient=tk.HORIZONTAL,
                                          variable=initial_brightness, command=on_brightness)
            brightness_slider.pack(fill="x")

            # Click anywhere on the track to jump straight to that percentage, and keep the
            # button down to drag from there. Replaces ttk's default handling, which only
            # moves one step per click on the track.
            def move_slider_to(event):
                left = brightness_slider.coords(1)[0]
                right = brightness_slider.coords(100)[0]
                if right > left:
                    fraction = max(0.0, min(1.0, (event.x - left) / (right - left)))
                    value = round(1 + fraction * 99)
                    if value != round(brightness_slider.get()):
                        brightness_slider.set(value)  # set() also sends it to the bulb
                return "break"

            brightness_slider.bind("<Button-1>", move_slider_to)
            brightness_slider.bind("<B1-Motion>", move_slider_to)
            brightness_slider.bind("<ButtonRelease-1>", lambda event: "break")

            # A newly picked color (wheel or R/G/B fields) is sent at its own brightness,
            # so move the slider to match, e.g. 100% for a color from the wheel.
            # Setting the variable only moves the slider; it does not send anything.
            def sync_brightness_to_color(*args):
                try:
                    values = [max(0, min(255, int(var.get()))) for var in (red_var, green_var, blue_var)]
                except ValueError:
                    return
                if max(values) > 0:
                    initial_brightness.set(max(values) / 255 * 100)

            for var in (red_var, green_var, blue_var):
                var.trace_add("write", sync_brightness_to_color)

            canvas.bind("<Button-1>", lambda event: help.on_color_select(event, canvas, marker, red_var, green_var, blue_var))

            # --- Actions ---
            actions = ttk.Frame(frame_inside)
            actions.pack(fill="x", pady=(14, 0))
            actions.columnconfigure((0, 1), weight=1)
            ttk.Button(actions, text="⏻  Toggle on / off", style="Big.Accent.TButton",
                       command=lambda: action.Toggle_bulb()).grid(row=0, column=0, columnspan=2, sticky="ew")
            ttk.Button(actions, text="All on",
                       command=lambda: action.turn_on_all_bulbs(device_repository.read_from_csv())
                       ).grid(row=1, column=0, sticky="ew", pady=(8, 0), padx=(0, 4))
            ttk.Button(actions, text="All off",
                       command=lambda: action.turn_off_all_bulbs(device_repository.read_from_csv())
                       ).grid(row=1, column=1, sticky="ew", pady=(8, 0), padx=(4, 0))

            message_label.pack(in_=frame_inside, fill="x", pady=(10, 0))

            device_trace = selected_device.trace_add("write", lambda *args: action.change_device(
                selected_device,
                selected_device_old,
                device_repository.read_from_csv(),
                canvas,
                marker,
                red_var,
                green_var,
                blue_var,
                message_label,
                brightness_var=initial_brightness,
            ))

        def update_dropdown():
            new_devices = device_repository.read_from_csv()
            connected_devices = []
            for device in new_devices:
                try:
                    if device[2] == "Flux":
                        WifiLedBulb(device[1])
                        connected_devices.append(device)
                except Exception as e:
                    print(f"Device {device[0]} at {device[1]} connection error: {e}")

            if connected_devices:
                render_device_controls(True)
                device_dropdown["values"] = [device[0] for device in connected_devices]
                try:
                    selected_device.set(connected_devices[0][0])
                except Exception as e:
                    print(f"Error setting selected device: {e}")
                    render_device_controls(False)
                    return
                return new_devices[0][0]
            else:
                print("No device dropdown found")
                render_device_controls(False)
                return

        selected_device_old = update_dropdown()

        # Size the window to its content and open it just above the mouse (the tray icon)
        window.update_idletasks()
        height = window.winfo_reqheight()
        x, y = window.winfo_pointerxy()
        x_position = max(0, x - (WINDOW_WIDTH // 2))
        y_position = max(0, y - height - 5)
        window.geometry(f"{WINDOW_WIDTH}x{height}+{x_position}+{y_position}")

        # Function to quit the application (stop the icon and exit)
        def quit_action(icon):
            icon.stop()
            sys.exit()

        # Handle window close event
        def on_close():
            open_window.window_opened = False  # Reset the flag when the window is closed
            window.destroy()  # Close the window

        window.protocol("WM_DELETE_WINDOW", on_close)
        window.mainloop()
    else:
        print("Window is already open.")
