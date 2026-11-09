"""Small quick-control popup opened from the tray icon.

Device picker, on/off, brightness, color presets and All on/off, plus a link
to open the full app. It is a child of the app's hidden Tk root (see main.py).
"""
import tkinter as tk
from tkinter import ttk

from . import bulb_actions as action
from . import device_repository
from . import shared_state
from . import theme

WIDTH = 300

# (name, (R, G, B)) presets shown as color dots
PRESETS = (
    ("Warm white", (255, 170, 90)),
    ("Cool white", (255, 255, 255)),
    ("Red", (255, 0, 0)),
    ("Orange", (255, 110, 0)),
    ("Green", (0, 255, 60)),
    ("Blue", (0, 90, 255)),
    ("Purple", (150, 0, 255)),
    ("Pink", (255, 0, 150)),
)


def open_quick_panel(open_full_app, x=None, y=None):
    """Show the panel as a borderless popup at the tray icon; if it is open, close it.

    open_full_app: called (after this panel closes) when "Open full app" is clicked.
    x, y: where the tray icon was clicked, in Tk pixels (None = the mouse position).
    """
    existing = getattr(open_quick_panel, "window", None)
    if existing is not None and existing.winfo_exists():
        existing.destroy()  # clicking the icon again closes the panel
        return

    # Clicking anywhere outside the popup closes it. A borderless popup is not told when
    # you click another (Wayland) window, so an almost invisible full-screen layer is put
    # behind the popup to catch that click. It is created first so the popup (and the
    # device dropdown's list, opened later) stack above it.
    catcher = _make_click_catcher()
    if catcher is not None:
        catcher.bind("<ButtonPress>", lambda event: close())

    window = tk.Toplevel()
    open_quick_panel.window = window
    window.title("Magic Home")
    window.overrideredirect(True)  # no title bar or frame: a popup, not a window
    window.configure(bg=theme.BORDER_STRONG)  # shows as a 1px border around the page

    def close():
        if window.winfo_exists():
            window.destroy()

    # The catcher goes away with the popup, however the popup is closed
    window.bind("<Destroy>", lambda event: catcher.destroy()
                if event.widget is window and catcher is not None and catcher.winfo_exists() else None)

    page = ttk.Frame(window, padding=16)
    page.pack(fill="both", expand=True, padx=1, pady=1)

    devices = device_repository.read_from_csv()
    message = theme.message_label(page)

    if not devices:
        ttk.Label(page, text="No devices yet", font=theme.font(11, "bold")).pack(anchor="w")
        ttk.Label(page, text="Open the full app to add or scan for lights.",
                  style="Muted.TLabel", wraplength=WIDTH - 32).pack(anchor="w", pady=(2, 8))
        _open_link(page, window, open_full_app)
        _place_at(window, x, y)
        window.lift()
        window.bind("<Escape>", lambda event: close())
        window.focus_force()
        return

    # --- Device picker and power button ---
    top = ttk.Frame(page)
    top.pack(fill="x")
    device_var = tk.StringVar(window)
    power = ttk.Button(top, text="⏻", width=3)
    power.pack(side="right", padx=(8, 0))  # packed first so the dropdown can't push it out
    picker = ttk.Combobox(top, textvariable=device_var, state="readonly", width=10,
                          values=[device[0] for device in devices])
    picker.pack(side="left", fill="x", expand=True)

    # --- Brightness ---
    brightness_row = ttk.Frame(page)
    brightness_row.pack(fill="x", pady=(14, 0))
    ttk.Label(brightness_row, text="BRIGHTNESS", style="Muted.TLabel", font=theme.font(8, "bold")).pack(side="left")
    brightness_label = ttk.Label(brightness_row, text="", foreground=theme.ACCENT, font=theme.font(9, "bold"))
    brightness_label.pack(side="right")

    brightness_var = tk.DoubleVar(window, value=100)
    brightness_var.trace_add("write", lambda *args: brightness_label.config(text=f"{round(brightness_var.get())}%"))
    slider = ttk.Scale(page, from_=1, to=100, orient=tk.HORIZONTAL, variable=brightness_var,
                       command=lambda value: run(lambda: action.set_brightness(float(value))))
    slider.pack(fill="x", pady=(4, 0))
    theme.enable_click_to_jump(slider, 1, 100)

    # --- Color presets ---
    dot, gap = 22, 10
    dots = tk.Canvas(page, height=dot + 4, width=len(PRESETS) * (dot + gap) - gap + 4,
                     bg=theme.BG, highlightthickness=0, cursor="hand2")
    dots.pack(anchor="w", pady=(14, 0))
    for index, (name, color) in enumerate(PRESETS):
        left = 2 + index * (dot + gap)
        item = dots.create_oval(left, 2, left + dot, 2 + dot, fill="#{:02x}{:02x}{:02x}".format(*color),
                                outline=theme.BORDER_STRONG, width=1)
        dots.tag_bind(item, "<Button-1>", lambda event, c=color, n=name: pick_color(c, n))

    # --- All on / All off ---
    group = ttk.Frame(page)
    group.pack(fill="x", pady=(14, 0))
    group.columnconfigure((0, 1), weight=1, uniform="group")
    ttk.Button(group, text="All on",
               command=lambda: run(lambda: action.turn_on_all_bulbs(device_repository.read_from_csv()),
                                   "All lights on")).grid(row=0, column=0, sticky="ew", padx=(0, 4))
    ttk.Button(group, text="All off",
               command=lambda: run(lambda: action.turn_off_all_bulbs(device_repository.read_from_csv()),
                                   "All lights off")).grid(row=0, column=1, sticky="ew", padx=(4, 0))

    message.pack(fill="x", pady=(6, 0))
    _open_link(page, window, open_full_app)

    # --- Behaviour ---
    def run(command, success=None):
        """Run a bulb command and show an error instead of crashing if the bulb is unreachable."""
        if shared_state.bulb is None:
            theme.set_message(message, "No bulb connected", "error")
            return False
        try:
            command()
        except Exception:
            theme.set_message(message, "The bulb did not respond", "error")
            return False
        theme.set_message(message, success or "", "success")
        return True

    def show_power(is_on):
        power.configure(style="Accent.TButton" if is_on else "TButton")

    def select_device(*args):
        device = next((d for d in devices if d[0] == device_var.get()), None)
        if device is None:
            return
        try:
            action.connect_device(device[1], device[3])
        except Exception:
            shared_state.bulb = None
            theme.set_message(message, f"Can't reach {device[0]}", "error")
            show_power(False)
            return
        theme.set_message(message, "")
        show_power(bool(shared_state.bulb.is_on))
        brightness_var.set(max(1, action.get_brightness() * 100))  # moves the slider only

    def toggle_power():
        was_on = shared_state.bulb is not None and bool(shared_state.bulb.is_on)
        if run(action.Toggle_bulb):
            show_power(not was_on)

    def pick_color(color, name):
        if run(lambda: action.set_color(*color), name):
            brightness_var.set(100)  # a preset is sent at full brightness

    power.configure(command=toggle_power)
    device_var.trace_add("write", select_device)

    # Start with the bulb that is already active, otherwise the first one
    start = next((d for d in devices if d[1] == shared_state.current_ip), devices[0])
    device_var.set(start[0])

    _place_at(window, x, y)
    window.lift()
    window.bind("<Escape>", lambda event: close())
    window.focus_force()


def _make_click_catcher():
    """An invisible full-screen window that receives clicks outside the popup.

    Transparency only takes effect once a window is shown, so it is first shown as a
    single pixel, made transparent, and only then stretched over the screen. If the
    transparency does not take effect, no catcher is used: never a black screen.
    """
    catcher = tk.Toplevel()
    catcher.overrideredirect(True)
    catcher.configure(bg="black")
    catcher.geometry("1x1+0+0")
    catcher.update()
    catcher.attributes("-alpha", 0.01)
    catcher.update()
    if float(catcher.attributes("-alpha")) > 0.05:
        catcher.destroy()
        return None
    catcher.geometry(f"{catcher.winfo_screenwidth()}x{catcher.winfo_screenheight()}+0+0")
    catcher.update_idletasks()
    return catcher


def _open_link(page, window, open_full_app):
    def open_full():
        window.destroy()
        open_full_app()

    ttk.Button(page, text="Open full app  →", style="Link.TButton", command=open_full).pack(anchor="w", pady=(6, 0))


def _place_at(window, x, y):
    """Put the panel next to the tray icon: above it when the panel (taskbar) is at the
    bottom of the screen, below it when it is at the top, and always fully on screen."""
    window.update_idletasks()
    if x is None or y is None:
        x, y = window.winfo_pointerxy()
    scale = float(window.tk.call("tk", "scaling")) / (96 / 72)  # 1.0 at 96 dpi
    width = max(WIDTH, window.winfo_reqwidth())
    height = window.winfo_reqheight()
    screen_w, screen_h = window.winfo_screenwidth(), window.winfo_screenheight()
    gap = round(12 * max(1.0, scale))
    left = max(0, min(x - width // 2, screen_w - width))
    top = y - height - gap if y > screen_h / 2 else y + gap
    top = max(0, min(top, screen_h - height))
    window.geometry(f"{width}x{height}+{left}+{top}")
