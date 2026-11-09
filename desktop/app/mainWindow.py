from . import shared_state
from flux_led import WifiLedBulb
import tkinter as tk
from tkinter import ttk
from . import bulb_actions as action
from . import ui_helpers as help
import math
from colorsys import hsv_to_rgb, rgb_to_hsv
import functools
from . import DeviceManager
from . import device_repository
from . import theme
from .widgets import PRESETS, ColorDots, Slider, ToggleSwitch, scaler

MIN_WIDTH = 380  # design units, scaled with the display


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


def card_heading(parent, title, hint=None):
    """Title (and optional muted hint) at the top left of a card; returns the row for extras on the right."""
    row = ttk.Frame(parent, style="Panel.TFrame")
    row.pack(fill="x")
    titles = ttk.Frame(row, style="Panel.TFrame")
    titles.pack(side="left")
    ttk.Label(titles, text=title, style="Card.TLabel", font=theme.font(10, "bold")).pack(anchor="w")
    if hint:
        ttk.Label(titles, text=hint, style="Card.TLabel", foreground=theme.MUTED, font=theme.font(8)).pack(anchor="w")
    return row


# Function to open the Tkinter window for light control
def open_window(icon):
    # Check if the window is already open
    if not hasattr(open_window, "window_opened") or not open_window.window_opened:
        open_window.window_opened = True

        # A child of the app's hidden Tk root (created in main.py, which also applies the theme)
        window = tk.Toplevel()
        window.title("Magic Home Control")
        window.configure(bg=theme.BG)
        window.resizable(False, False)
        open_window.window = window
        px = scaler(window)

        # Reset the flag however the window goes away
        def on_destroy(event):
            if event.widget is window:
                open_window.window_opened = False

        window.bind("<Destroy>", on_destroy)

        selected_device = tk.StringVar(window)
        selected_device.set("")  # Default value if no devices are connected
        selected_device_old = ""
        device_trace = None  # id of the trace on selected_device, so it can be replaced on re-render
        power = {"on": False}

        page = ttk.Frame(window, padding=(px(20), px(18)))
        page.pack(fill="both", expand=True)

        # --- Header: icon, app name, active bulb + state, Devices button ---
        header = ttk.Frame(page)
        header.pack(fill="x")
        try:
            logo = tk.PhotoImage(master=window, data=theme.icon_png(px(36)))
            ttk.Label(header, image=logo).pack(side="left", padx=(0, px(12)))
            window.logo = logo  # keep a reference
        except Exception:
            pass
        titles = ttk.Frame(header)
        titles.pack(side="left")
        ttk.Label(titles, text="Magic Home", font=theme.font(14, "bold")).pack(anchor="w")
        status_label = ttk.Label(titles, text="", style="Muted.TLabel")
        status_label.pack(anchor="w")
        ttk.Button(header, text="Devices",
                   command=lambda: DeviceManager.open_add_device_window(icon, update_dropdown, parent=window)
                   ).pack(side="right")

        # --- Device picker (only shown with more than one bulb) ---
        picker_row = ttk.Frame(page)
        device_dropdown = ttk.Combobox(picker_row, textvariable=selected_device, state="readonly")
        device_dropdown.pack(fill="x")

        # --- Footer (packed before the expanding area so it always stays visible) ---
        footer = ttk.Frame(page)
        footer.pack(fill="x", side="bottom", pady=(px(14), 0))
        ttk.Button(footer, text="All on",
                   command=lambda: run(lambda: action.turn_on_all_bulbs(device_repository.read_from_csv()),
                                       "All lights on")).pack(side="left")
        ttk.Button(footer, text="All off",
                   command=lambda: run(lambda: action.turn_off_all_bulbs(device_repository.read_from_csv()),
                                       "All lights off")).pack(side="left", padx=(px(8), 0))
        ttk.Button(footer, text="Quit", style="Danger.TButton",
                   command=lambda: quit_action(icon)).pack(side="right")

        message_label = theme.message_label(page)
        message_label.pack(fill="x", side="bottom", pady=(px(10), 0))

        # Area that holds the controls (rebuilt when the device list changes)
        frame_inside = ttk.Frame(page)
        frame_inside.pack(fill="both", expand=True, pady=(px(16), 0))

        # The wheel image is the same every time, so draw it once per window
        wheel_image = draw_color_wheel(shared_state.canvas_size, theme.SURFACE)

        def run(command, success=""):
            """Run a bulb command; show an error instead of crashing if the bulb is unreachable."""
            try:
                command()
            except Exception:
                theme.set_message(message_label, "The bulb did not respond", "error")
                return False
            theme.set_message(message_label, success, "success")
            return True

        def show_status():
            name = selected_device.get()
            status_label.config(text=f"{name}  ·  {'On' if power['on'] else 'Off'}" if name else "No device")

        def render_device_controls(show_controls):
            nonlocal device_trace

            # Clear previous widgets in frame_inside
            for widget in frame_inside.winfo_children():
                widget.destroy()

            # Remove the trace from the previous render; it points at destroyed widgets
            if device_trace is not None:
                selected_device.trace_remove("write", device_trace)
                device_trace = None

            if not show_controls:
                empty = ttk.Frame(frame_inside, style="Card.TFrame", padding=px(24))
                empty.pack(fill="both", expand=True)
                ttk.Label(empty, text="No devices connected", style="Card.TLabel",
                          font=theme.font(12, "bold")).pack(pady=(px(30), px(6)))
                ttk.Label(empty, text="Open Devices to add a light or scan your network.",
                          style="Card.TLabel", foreground=theme.MUTED, wraplength=px(280),
                          justify="center").pack()
                device_dropdown["values"] = ()
                status_label.config(text="No device")
                return

            gap = px(12)

            # --- Power card ---
            power_card = ttk.Frame(frame_inside, style="Card.TFrame", padding=px(16))
            power_card.pack(fill="x")
            power_row = card_heading(power_card, "Power", "Turn this light on or off")

            def toggle_power():
                was_on = power["on"]
                if run(action.Toggle_bulb):
                    power["on"] = not was_on
                switch.set(power["on"])
                show_status()

            switch = ToggleSwitch(power_row, px, command=toggle_power)
            switch.pack(side="right")

            # --- Color card ---
            color_card = ttk.Frame(frame_inside, style="Card.TFrame", padding=px(16))
            color_card.pack(fill="x", pady=(gap, 0))
            color_row = card_heading(color_card, "Color")
            hex_label = ttk.Label(color_row, text="", style="Value.TLabel")
            hex_label.pack(side="right")
            swatch = tk.Frame(color_row, width=px(16), height=px(16), bg=theme.SURFACE,
                              highlightthickness=1, highlightbackground=theme.BORDER_STRONG)
            swatch.pack(side="right", padx=(0, px(8)))

            # Color wheel
            canvas = tk.Canvas(color_card, width=shared_state.canvas_size, height=shared_state.canvas_size,
                               bg=theme.SURFACE, highlightthickness=0, cursor="crosshair")
            canvas.pack(pady=(px(12), px(12)))
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

            # Preset colors
            def pick_preset(color, name):
                if not run(lambda: action.set_color(*color)):
                    return
                help.update_rgb_values(red_var, green_var, blue_var, *color)  # updates the fields, sends nothing
                try:
                    help.move_white_point(canvas, marker)
                except Exception:
                    pass
                dots.select(name)

            dots = ColorDots(color_card, px, on_pick=pick_preset, size=24)
            dots.pack(fill="x")

            # RGB inputs
            rgb_row = ttk.Frame(color_card, style="Panel.TFrame")
            rgb_row.pack(fill="x", pady=(px(12), 0))
            rgb_row.columnconfigure((0, 1, 2), weight=1, uniform="rgb")

            validate_command = window.register(help.validate_rgb_input)
            color = action.get_color()
            red_var = tk.StringVar(value=color[0])
            green_var = tk.StringVar(value=color[1])
            blue_var = tk.StringVar(value=color[2])

            for column, (letter, var) in enumerate((("R", red_var), ("G", green_var), ("B", blue_var))):
                cell = ttk.Frame(rgb_row, style="Panel.TFrame")
                cell.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else px(6), 0))
                ttk.Label(cell, text=letter, style="Card.TLabel", foreground=theme.MUTED,
                          font=theme.font(8, "bold")).pack(side="left", padx=(0, px(6)))
                ttk.Entry(cell, textvariable=var, validate="key", validatecommand=(validate_command, "%P"),
                          width=4, justify="center").pack(side="left", fill="x", expand=True)
                var.trace_add("write", functools.partial(action.change_color, red_var=red_var, green_var=green_var,
                                                         blue_var=blue_var, canvas=canvas, marker=marker))

            # Swatch and hex value follow the RGB fields; a preset ring goes away for other colors
            def update_swatch(*args):
                try:
                    values = [max(0, min(255, int(var.get()))) for var in (red_var, green_var, blue_var)]
                except ValueError:
                    return
                hex_value = "#{:02x}{:02x}{:02x}".format(*values)
                swatch.config(bg=hex_value)
                hex_label.config(text=hex_value.upper())
                preset = dict(PRESETS).get(dots.selected)
                if preset is not None and tuple(values) != preset:
                    dots.select(None)

            for var in (red_var, green_var, blue_var):
                var.trace_add("write", update_swatch)
            update_swatch()

            # --- Brightness card ---
            brightness_card = ttk.Frame(frame_inside, style="Card.TFrame", padding=px(16))
            brightness_card.pack(fill="x", pady=(gap, 0))
            brightness_row = card_heading(brightness_card, "Brightness")
            brightness_value = ttk.Label(brightness_row, text="", style="Value.TLabel")
            brightness_value.pack(side="right")

            slider = Slider(brightness_card, px, on_change=lambda value: run(lambda: action.set_brightness(value)))
            slider.pack(fill="x", pady=(px(10), 0))
            slider.on_display = lambda value: brightness_value.config(text=f"{round(value)}%")

            # The app moves the slider through this variable (device change, picked color);
            # that only moves it - nothing is sent to the bulb.
            brightness_var = tk.DoubleVar(value=action.get_brightness() * 100)
            brightness_var.trace_add("write", lambda *args: slider.set(brightness_var.get()))
            slider.set(brightness_var.get())

            # A newly picked color (wheel, presets or R/G/B fields) is sent at its own brightness,
            # so move the slider to match, e.g. 100% for a color from the wheel.
            def sync_brightness_to_color(*args):
                try:
                    values = [max(0, min(255, int(var.get()))) for var in (red_var, green_var, blue_var)]
                except ValueError:
                    return
                if max(values) > 0:
                    brightness_var.set(max(values) / 255 * 100)

            for var in (red_var, green_var, blue_var):
                var.trace_add("write", sync_brightness_to_color)

            canvas.bind("<Button-1>", lambda event: help.on_color_select(event, canvas, marker, red_var, green_var, blue_var))

            def on_device_change(*args):
                action.change_device(
                    selected_device,
                    selected_device_old,
                    device_repository.read_from_csv(),
                    canvas,
                    marker,
                    red_var,
                    green_var,
                    blue_var,
                    message_label,
                    brightness_var=brightness_var,
                )
                power["on"] = shared_state.bulb is not None and bool(shared_state.bulb.is_on)
                switch.set(power["on"])
                dots.select(None)
                show_status()

            device_trace = selected_device.trace_add("write", on_device_change)

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

            # The picker is only useful with more than one bulb
            if len(connected_devices) > 1:
                picker_row.pack(fill="x", pady=(px(16), 0), after=header)
            else:
                picker_row.pack_forget()

            if connected_devices:
                render_device_controls(True)
                device_dropdown["values"] = [device[0] for device in connected_devices]
                # Show the bulb that is already active (e.g. picked in the quick panel), else the first
                start = next((device for device in connected_devices if device[1] == shared_state.current_ip),
                             connected_devices[0])
                try:
                    selected_device.set(start[0])
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

        # A normal window: size it to its content and center it on the screen
        window.update_idletasks()
        width = max(px(MIN_WIDTH), window.winfo_reqwidth())
        height = window.winfo_reqheight()
        x_position = max(0, (window.winfo_screenwidth() - width) // 2)
        y_position = max(0, (window.winfo_screenheight() - height) // 2)
        window.geometry(f"{width}x{height}+{x_position}+{y_position}")

        # Quit the whole app: ending the root's main loop makes main.py stop the tray icon
        def quit_action(icon):
            window.master.quit()

        # Handle window close event
        def on_close():
            open_window.window_opened = False  # Reset the flag when the window is closed
            window.destroy()  # Close the window

        window.protocol("WM_DELETE_WINDOW", on_close)
    else:
        # Already open: bring it to the front instead
        window = open_window.window
        window.deiconify()
        window.lift()
        window.focus_force()
