import argparse
import os
import queue
import sys
import tempfile
import tkinter as tk


from . import bulb_actions  # noqa: F401  (import first: avoids the ui_helpers <-> bulb_actions import cycle)
from . import theme
from .mainWindow import open_window
from .quick_panel import open_quick_panel

TITLE = "Magic Home Control"

# Tray clicks happen on the tray's own thread, but Tk may only be used from the thread
# that runs its main loop. So the tray just puts requests here and Tk picks them up.
# Each request is (action, x, y); x and y are the click position in Tk pixels, or None.
requests = queue.Queue()


def create_image():
    """The app icon (tray and windows)."""
    return theme.app_icon_image()


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
    # Window icon for every window of the app (title bar, task switcher)
    root.window_icons = [tk.PhotoImage(master=root, data=theme.icon_png(size)) for size in (64, 32, 16)]
    root.iconphoto(True, *root.window_icons)

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


def acquire_single_instance():
    """Return a lock that stays held while this app runs, or None if another copy already runs.

    With autostart and an app-menu launcher it is easy to start the app twice, which would
    put two icons in the tray. The operating system releases the lock when the app exits,
    even after a crash.
    """
    folder = os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()
    lock_file = open(os.path.join(folder, "magic-home.lock"), "a+")
    try:
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock_file.close()
        return None
    return lock_file


def cli(argv=None):
    """The `magic-home` command."""
    parser = argparse.ArgumentParser(
        prog="magic-home",
        description="Magic Home Control: control your Magic Home / Flux LED lights from the system tray.")
    parser.add_argument("--install-desktop-entry", action="store_true",
                        help="Linux: add Magic Home to the app menu and start it at login")
    parser.add_argument("--no-autostart", action="store_true",
                        help="with --install-desktop-entry: add it to the app menu only, don't start at login")
    parser.add_argument("--uninstall-desktop-entry", action="store_true",
                        help="Linux: remove the app menu and start-at-login entries again")
    args = parser.parse_args(argv)

    if args.install_desktop_entry or args.uninstall_desktop_entry:
        from . import desktop_entry
        if args.uninstall_desktop_entry:
            return desktop_entry.uninstall()
        return desktop_entry.install(autostart=not args.no_autostart)

    lock = acquire_single_instance()
    if lock is None:
        print("Magic Home is already running. Look for its icon in the system tray.")
        return 1
    try:
        main()
    finally:
        lock.close()
    return 0


if __name__ == "__main__":
    sys.exit(cli())
