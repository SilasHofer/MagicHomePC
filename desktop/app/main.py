import queue
import sys
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageDraw

from . import bulb_actions  # noqa: F401  (import first: avoids the ui_helpers <-> bulb_actions import cycle)
from . import theme
from .mainWindow import open_window
from .quick_panel import open_quick_panel

TITLE = "Magic Home Control"

# Tray clicks happen on the tray's own thread, but Tk may only be used from the thread
# that runs its main loop. So the tray just puts requests here and Tk picks them up.
# Each request is (action, x, y); x and y are the click position in Tk pixels, or None.
requests = queue.Queue()


# Function to create the system tray icon
def create_image():
    # Create an image with PIL (Python Imaging Library)
    width, height = 64, 64
    image = Image.open(Path(__file__).resolve().parents[1] / "assets" / "icon.png")
    draw = ImageDraw.Draw(image)

    # Draw a simple circle (could be an icon)
    draw.ellipse((10, 10, width - 10, height - 10), fill=(255, 0, 0))  # Red circle

    return image


def start_tray(root):
    """Start the tray icon; returns a function that removes it again."""
    if sys.platform.startswith("linux"):
        from . import kde_tray
        if kde_tray.available():
            # KDE Plasma: left-click opens the quick panel at the icon, right-click shows the menu
            scale = kde_tray.screen_scale(root.winfo_screenwidth())

            def to_tk(x, y):
                return round(x * scale), round(y * scale)

            tray = kde_tray.KdeTray(
                TITLE, create_image(),
                on_activate=lambda x, y: requests.put(("quick", *to_tk(x, y))),
                on_context_menu=lambda x, y: requests.put(("menu", *to_tk(x, y))),
            )
            tray.run_in_thread()
            return tray.stop

    # Other systems (e.g. Windows): pystray, where a left-click runs the default item
    import threading
    from pystray import Icon, Menu, MenuItem
    icon = Icon(name=TITLE, icon=create_image(), title=TITLE, menu=Menu(
        MenuItem("Quick controls", lambda icon, item: requests.put(("quick", None, None)), default=True),
        MenuItem("Open Magic Home", lambda icon, item: requests.put(("full", None, None))),
        Menu.SEPARATOR,
        MenuItem("Quit", lambda icon, item: requests.put(("quit", None, None))),
    ))
    threading.Thread(target=icon.run, daemon=True).start()
    return icon.stop


def show_tray_menu(root, x, y):
    menu = tk.Menu(root, tearoff=False, bg=theme.SURFACE, fg=theme.TEXT, activebackground=theme.ACCENT,
                   activeforeground=theme.ACCENT_TEXT, bd=0, relief="flat", font=theme.font(10))
    menu.add_command(label="Quick controls", command=lambda: requests.put(("quick", x, y)))
    menu.add_command(label="Open Magic Home", command=lambda: requests.put(("full", None, None)))
    menu.add_separator()
    menu.add_command(label="Quit", command=lambda: requests.put(("quit", None, None)))
    try:
        menu.tk_popup(x, y)
    finally:
        menu.grab_release()


def main():
    # One hidden Tk root for the whole app; every window is a child of it
    root = tk.Tk()
    root.withdraw()
    theme.apply_theme(root)

    def open_full_app():
        open_window(None)

    def handle_requests():
        try:
            while True:
                action, x, y = requests.get_nowait()
                if action == "quick":
                    open_quick_panel(open_full_app, x, y)
                elif action == "full":
                    open_full_app()
                elif action == "menu":
                    show_tray_menu(root, x, y)
                elif action == "quit":
                    root.quit()
                    return
        except queue.Empty:
            pass
        root.after(50, handle_requests)

    root.after(50, handle_requests)
    stop_tray = start_tray(root)

    root.mainloop()  # runs until Quit (tray menu or the Quit button in the full window)
    stop_tray()
    root.destroy()


if __name__ == "__main__":
    main()
