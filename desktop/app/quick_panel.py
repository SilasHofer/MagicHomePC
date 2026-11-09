"""Compact quick-control popup opened from the tray icon.

A small borderless, rounded card just above the taskbar - deliberately much smaller
than the main window: bulb name and state with a power switch, brightness, color
presets, All on/off and a link to the full app. It is a child of the app's hidden
Tk root (see main.py).
"""
import ctypes
import ctypes.util
import subprocess
import tkinter as tk
from tkinter import ttk

from . import bulb_actions as action
from . import device_repository
from . import shared_state
from . import theme
from .widgets import ColorDots, Slider, ToggleSwitch, scaler

WIDTH = 250    # design units, scaled with the display
RADIUS = 14    # corner radius of the card


def open_quick_panel(open_full_app, x=None, y=None):
    """Show the panel just above the taskbar, near the tray icon; if it is open, close it.

    open_full_app: called (after this panel closes) when "Open app" is clicked.
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
    window.configure(bg=theme.SURFACE)
    px = scaler(window)

    def close():
        if window.winfo_exists():
            window.destroy()

    # The catcher goes away with the popup, however the popup is closed
    window.bind("<Destroy>", lambda event: catcher.destroy()
                if event.widget is window and catcher is not None and catcher.winfo_exists() else None)

    # The card: a canvas draws the rounded background and border, the content sits on top.
    # The content is inset a little so its square corners don't paint over the rounded border.
    card = tk.Canvas(window, bg=theme.SURFACE, highlightthickness=0, bd=0)
    card.pack(fill="both", expand=True)
    card.inset = px(RADIUS) * 3 // 10 + 1
    pad = px(12) - card.inset
    content = ttk.Frame(card, style="Panel.TFrame", padding=(pad, pad, pad, px(8) - card.inset))
    card.create_window(card.inset, card.inset, window=content, anchor="nw", tags="content")

    devices = device_repository.read_from_csv()

    # --- Header: icon, bulb name (or picker) with its state, power switch ---
    header = ttk.Frame(content, style="Panel.TFrame")
    header.pack(fill="x")
    logo = _app_icon(window, px(22))
    if logo is not None:
        ttk.Label(header, image=logo, style="Card.TLabel").pack(side="left", padx=(0, px(8)))
        window.logo = logo  # keep a reference
    titles = ttk.Frame(header, style="Panel.TFrame")
    titles.pack(side="left", fill="x", expand=True)
    device_var = tk.StringVar(window)
    name_label = ttk.Label(titles, text="Magic Home", style="Card.TLabel", font=theme.font(10, "bold"))
    state_label = tk.Label(titles, text="", bg=theme.SURFACE, fg=theme.MUTED, font=theme.font(8), anchor="w")

    if not devices:
        name_label.pack(anchor="w")
        state_label.configure(text="No devices yet")
        state_label.pack(anchor="w")
        _footer(content, window, open_full_app, px, None)
        _finish(window, card, content, x, y, px, close)
        return

    if len(devices) > 1:
        ttk.Combobox(titles, textvariable=device_var, state="readonly", width=12,
                     values=[device[0] for device in devices]).pack(anchor="w", fill="x")
    else:
        name_label.pack(anchor="w")
    state_label.pack(anchor="w", fill="x")

    switch = ToggleSwitch(header, px, command=lambda: toggle_power(), width=36, height=20)
    switch.pack(side="right", padx=(px(8), 0))

    # --- Brightness: icon, slider and value on one row ---
    row = ttk.Frame(content, style="Panel.TFrame")
    row.pack(fill="x", pady=(px(10), 0))
    ttk.Label(row, text="☀", style="Card.TLabel", foreground=theme.MUTED, font=theme.font(10)).pack(side="left")
    value_label = ttk.Label(row, text="", style="Card.TLabel", font=theme.font(8, "bold"), width=4, anchor="e")
    value_label.pack(side="right")
    slider = Slider(row, px, on_change=lambda value: run(lambda: action.set_brightness(value)),
                    height=18, thickness=4)
    slider.pack(side="left", fill="x", expand=True, padx=px(6))
    slider.on_display = lambda value: value_label.config(text=f"{round(value)}%")

    # --- Color presets ---
    dots = ColorDots(content, px, on_pick=lambda color, name: pick_color(color, name), size=18)
    dots.pack(fill="x", pady=(px(8), 0))

    _footer(content, window, open_full_app, px,
            lambda on: run(lambda: (action.turn_on_all_bulbs if on else action.turn_off_all_bulbs)(
                device_repository.read_from_csv()), "All lights " + ("on" if on else "off")))

    # --- Behaviour ---
    current = {"name": "", "on": False, "reset": None}

    def show_state():
        state_label.configure(text="On" if current["on"] else "Off", fg=theme.MUTED)

    def flash(text, kind):
        """Show a short status message where the state is, then go back to the state."""
        state_label.configure(text=text, fg=theme.MESSAGE_COLORS.get(kind, theme.MUTED))
        if current["reset"]:
            window.after_cancel(current["reset"])
        current["reset"] = window.after(2500, show_state)

    def run(command, success=None):
        """Run a bulb command and show an error instead of crashing if the bulb is unreachable."""
        if shared_state.bulb is None:
            flash("No bulb connected", "error")
            return False
        try:
            command()
        except Exception:
            flash("Bulb did not respond", "error")
            return False
        if success:
            flash(success, "success")
        return True

    def select_device(*args):
        device = next((d for d in devices if d[0] == device_var.get()), None)
        if device is None:
            return
        current["name"] = device[0]
        name_label.configure(text=device[0])
        try:
            action.connect_device(device[1], device[3])
        except Exception:
            shared_state.bulb = None
            switch.set(False)
            state_label.configure(text="Offline", fg=theme.ERROR)
            return
        current["on"] = bool(shared_state.bulb.is_on)
        switch.set(current["on"])
        show_state()
        slider.set(max(1, action.get_brightness() * 100))  # moves the slider only
        dots.select(None)

    def toggle_power():
        was_on = current["on"]
        if run(action.Toggle_bulb):
            current["on"] = not was_on
            show_state()
        switch.set(current["on"])

    def pick_color(color, name):
        if run(lambda: action.set_color(*color)):
            slider.set(100)  # a preset is sent at full brightness
            dots.select(name)

    device_var.trace_add("write", select_device)

    # Start with the bulb that is already active, otherwise the first one
    start = next((d for d in devices if d[1] == shared_state.current_ip), devices[0])
    device_var.set(start[0])

    _finish(window, card, content, x, y, px, close)


def _footer(content, window, open_full_app, px, all_lights):
    """Small text buttons: All on / All off on the left, Open app on the right."""
    ttk.Separator(content).pack(fill="x", pady=(px(10), px(2)))
    footer = ttk.Frame(content, style="Panel.TFrame")
    footer.pack(fill="x")
    if all_lights is not None:
        ttk.Button(footer, text="All on", style="CardGhost.TButton",
                   command=lambda: all_lights(True)).pack(side="left")
        ttk.Button(footer, text="All off", style="CardGhost.TButton",
                   command=lambda: all_lights(False)).pack(side="left")

    def open_full():
        window.destroy()
        open_full_app()

    ttk.Button(footer, text="Open app ↗", style="CardLink.TButton", command=open_full).pack(side="right")


def _finish(window, card, content, x, y, px, close):
    """Size the card to its content, draw it, place it above the taskbar and round it."""
    width = px(WIDTH)
    card.itemconfigure("content", width=width - 2 * card.inset)
    window.update_idletasks()
    height = content.winfo_reqheight() + 2 * card.inset
    card.configure(width=width, height=height)
    _draw_card(card, width, height, px(RADIUS))
    _place_above_taskbar(window, width, height, x, y, px)
    window.update_idletasks()
    _round_corners(window, width, height, px(RADIUS))
    window.lift()
    window.bind("<Escape>", lambda event: close())
    window.focus_force()


def _app_icon(widget, size):
    try:
        return tk.PhotoImage(master=widget, data=theme.icon_png(size))
    except Exception:
        return None


def _draw_card(card, width, height, radius):
    """Rounded rectangle background with a 1px border (drawn below the content)."""
    r, w, h = radius, width - 1, height - 1
    points = [r, 0, w - r, 0, w, 0, w, r, w, h - r, w, h, w - r, h, r, h, 0, h, 0, h - r, 0, r, 0, 0]
    card.create_polygon(points, smooth=True, fill=theme.SURFACE, outline=theme.BORDER_STRONG, width=1)
    card.tag_lower("all")
    card.tag_raise("content")


def _work_area(window):
    """The usable screen area without the taskbar (x, y, width, height), from the window manager."""
    try:
        output = subprocess.run(["xprop", "-root", "_NET_WORKAREA"], capture_output=True, text=True,
                                timeout=2).stdout
        values = [int(v) for v in output.split("=", 1)[1].split(",")[:4]]
        if values[2] > 0 and values[3] > 0:
            return values
    except Exception:
        pass
    return 0, 0, window.winfo_screenwidth(), window.winfo_screenheight()


def _place_above_taskbar(window, width, height, x, y, px):
    """Next to the tray icon, just above the taskbar (or below it when the taskbar is at the top)."""
    if x is None or y is None:
        x, y = window.winfo_pointerxy()
    area_x, area_y, area_w, area_h = _work_area(window)
    gap = px(8)
    left = max(area_x + gap, min(x - width // 2, area_x + area_w - width - gap))
    if y > area_y + area_h / 2:
        top = area_y + area_h - height - gap   # taskbar at the bottom
    else:
        top = area_y + gap                     # taskbar at the top
    window.geometry(f"{width}x{height}+{left}+{top}")


class _XRectangle(ctypes.Structure):
    _fields_ = [("x", ctypes.c_short), ("y", ctypes.c_short),
                ("width", ctypes.c_ushort), ("height", ctypes.c_ushort)]


def _round_corners(window, width, height, radius):
    """Cut the window to a rounded rectangle with the X Shape extension (Linux/X11 only)."""
    if window.tk.call("tk", "windowingsystem") != "x11":
        return
    try:
        x11 = ctypes.CDLL(ctypes.util.find_library("X11"))
        xext = ctypes.CDLL(ctypes.util.find_library("Xext"))
    except (OSError, TypeError):
        return
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XFlush.argtypes = [ctypes.c_void_p]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    xext.XShapeCombineRectangles.argtypes = [
        ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(_XRectangle), ctypes.c_int, ctypes.c_int, ctypes.c_int]

    # One rectangle per row inside the corner curves, plus one for the middle
    rects = []
    for row in range(radius):
        dy = radius - row - 0.5
        inset = round(radius - (radius * radius - dy * dy) ** 0.5)
        rects.append(_XRectangle(inset, row, width - 2 * inset, 1))
        rects.append(_XRectangle(inset, height - 1 - row, width - 2 * inset, 1))
    rects.append(_XRectangle(0, radius, width, height - 2 * radius))
    array = (_XRectangle * len(rects))(*rects)

    x11.XQueryTree.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong),
                               ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.POINTER(ctypes.c_ulong)),
                               ctypes.POINTER(ctypes.c_uint)]
    x11.XFree.argtypes = [ctypes.c_void_p]

    display = x11.XOpenDisplay(None)
    if not display:
        return
    try:
        # Tk wraps the window in its own parent window; the one that is actually shown on
        # screen is the top one (a direct child of the root), so shape every window up to it.
        window_id = int(window.wm_frame(), 16)
        while window_id:
            xext.XShapeCombineRectangles(display, window_id, 0, 0, 0, array, len(rects), 0, 0)  # Bounding, Set
            root, parent = ctypes.c_ulong(), ctypes.c_ulong()
            children, count = ctypes.POINTER(ctypes.c_ulong)(), ctypes.c_uint()
            if not x11.XQueryTree(display, window_id, ctypes.byref(root), ctypes.byref(parent),
                                  ctypes.byref(children), ctypes.byref(count)):
                break
            if children:
                x11.XFree(children)
            window_id = parent.value if parent.value != root.value else 0
        x11.XFlush(display)
    finally:
        x11.XCloseDisplay(display)


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
