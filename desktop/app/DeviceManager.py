from . import device_repository
import tkinter as tk
from tkinter import ttk
from . import ui_helpers
from . import theme
from .widgets import scaler

COLOR_ORDERS = ("RGB", "GRB", "BGR", "GBR", "RBG", "BRG")
MIN_WIDTH = 420  # design units, scaled with the display


class DeviceList(ttk.Frame):
    """A modern list of devices: one row per bulb with its details and an action button.

    It offers the few Treeview methods ui_helpers uses (insert, delete, get_children, item
    and the `discovered` attribute), so update_device_list / scan_network / save_device
    work with it unchanged. Row values are (name, ip, color order, action), where the
    action is "Delete" for saved devices and "+ Add" for bulbs found by a scan.
    """

    def __init__(self, parent, px, on_action):
        super().__init__(parent, style="Panel.TFrame")
        self.px = px
        self.on_action = on_action
        self.rows = {}
        self.discovered = []
        self.empty = ttk.Label(self, text="No devices yet. Scan your network or add one above.",
                               style="Card.TLabel", foreground=theme.MUTED, font=theme.font(9))
        self._update_empty()

    # --- Treeview-compatible API ---
    def get_children(self):
        return list(self.rows)

    def delete(self, row_id):
        row = self.rows.pop(row_id, None)
        if row is not None:
            row["frame"].destroy()
        self._update_empty()

    def item(self, row_id):
        return {"values": self.rows[row_id]["values"]}

    def insert(self, parent, index, values, tags=()):
        name, ip, order, action = values
        found = "add" in str(action).lower()
        px = self.px

        frame = ttk.Frame(self, style="Panel.TFrame")
        if self.rows:
            ttk.Separator(frame).pack(fill="x")
        body = ttk.Frame(frame, style="Panel.TFrame", padding=(0, px(10)))
        body.pack(fill="x")

        # Status dot: filled coral for saved lights, a coral ring for bulbs found by a scan
        size = px(10)
        dot = tk.Canvas(body, width=size, height=size, bg=theme.SURFACE, highlightthickness=0)
        dot.create_oval(1, 1, size - 1, size - 1, fill=theme.SURFACE if found else theme.ACCENT,
                        outline=theme.ACCENT, width=2 if found else 1)
        dot.pack(side="left", padx=(0, px(12)))

        texts = ttk.Frame(body, style="Panel.TFrame")
        texts.pack(side="left", fill="x", expand=True)
        ttk.Label(texts, text=name, style="Card.TLabel", font=theme.font(10, "bold")).pack(anchor="w")
        detail = f"{ip}  ·  Found on your network" if found else f"{ip}  ·  {order}"
        ttk.Label(texts, text=detail, style="Card.TLabel", foreground=theme.MUTED, font=theme.font(8)).pack(anchor="w")

        row_id = f"row{id(frame)}"
        if found:
            button = ttk.Button(body, text="Add", style="Small.Accent.TButton",
                                command=lambda: self.on_action("add", self.rows[row_id]["values"]))
        else:
            button = ttk.Button(body, text="Remove", style="CardDanger.TButton",
                                command=lambda: self.on_action("delete", self.rows[row_id]["values"]))
        button.pack(side="right")

        frame.pack(fill="x")
        self.rows[row_id] = {"frame": frame, "values": tuple(values)}
        self._update_empty()
        return row_id

    def _update_empty(self):
        if self.rows:
            self.empty.pack_forget()
        else:
            self.empty.pack(anchor="w", pady=(self.px(8), self.px(4)))


def open_add_device_window(icon, callback=None, parent=None):
    # Check if the window is already open
    if not hasattr(open_add_device_window, "window_opened") or not open_add_device_window.window_opened:
        open_add_device_window.window_opened = True
        # A child of the main window, so it closes together with it (the theme comes from the Tk root)
        window = tk.Toplevel(parent)
        window.title("Devices")
        window.configure(bg=theme.BG)
        window.resizable(False, False)
        open_add_device_window.window = window
        px = scaler(window)

        # Reset the flag whenever this window is destroyed, including when the main
        # window is closed and takes this window with it (on_close does not run then)
        def on_destroy(event):
            if event.widget is window:
                open_add_device_window.window_opened = False

        window.bind("<Destroy>", on_destroy)

        page = ttk.Frame(window, padding=(px(20), px(18)))
        page.pack(fill="both", expand=True)

        # --- Header ---
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
        ttk.Label(titles, text="Devices", font=theme.font(14, "bold")).pack(anchor="w")
        ttk.Label(titles, text="Add a light or scan your network", style="Muted.TLabel").pack(anchor="w")

        # --- Footer (packed first so it always stays visible) ---
        footer = ttk.Frame(page)
        footer.pack(fill="x", side="bottom", pady=(px(14), 0))
        ttk.Button(footer, text="Done", command=lambda: on_close()).pack(side="right")

        # --- Add a light card ---
        form = ttk.Frame(page, style="Card.TFrame", padding=px(16))
        form.pack(fill="x", pady=(px(16), 0))
        form.columnconfigure(0, weight=3)
        form.columnconfigure(1, weight=2)

        heading = ttk.Frame(form, style="Panel.TFrame")
        heading.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, px(12)))
        ttk.Label(heading, text="Add a light", style="Card.TLabel", font=theme.font(10, "bold")).pack(anchor="w")
        ttk.Label(heading, text="Enter its IP address, or pick one from a scan below",
                  style="Card.TLabel", foreground=theme.MUTED, font=theme.font(8)).pack(anchor="w")

        def field_label(text, row, column, padx=(0, 0)):
            ttk.Label(form, text=text, style="Card.TLabel", foreground=theme.MUTED,
                      font=theme.font(8, "bold")).grid(row=row, column=column, sticky="w", padx=padx)

        field_label("Name", 1, 0)
        name = ttk.Entry(form)
        name.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(px(4), px(10)))

        field_label("IP address", 3, 0)
        field_label("Color order", 3, 1, padx=(px(10), 0))
        ip = ttk.Entry(form)
        ip.grid(row=4, column=0, sticky="ew", pady=(px(4), 0))
        color_order_var = tk.StringVar(value="RGB")
        color_order_dropdown = ttk.Combobox(form, textvariable=color_order_var, state="readonly",
                                            values=COLOR_ORDERS, width=6)
        color_order_dropdown.grid(row=4, column=1, sticky="ew", padx=(px(10), 0), pady=(px(4), 0))
        color_order_dropdown.current(0)

        buttons = ttk.Frame(form, style="Panel.TFrame")
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(px(14), 0))
        ttk.Button(buttons, text="Test connection",
                   command=lambda: ui_helpers.try_to_connect(ip.get(), message_label)).pack(side="left")
        ttk.Button(buttons, text="Save light", style="Accent.TButton",
                   command=lambda: ui_helpers.save_device(name, ip, color_order_var, message_label, tree)
                   ).pack(side="left", padx=(px(8), 0))

        # --- Status line ---
        message_label = theme.message_label(page)
        message_label.pack(fill="x", pady=(px(10), 0))

        # --- Your lights card ---
        lights = ttk.Frame(page, style="Card.TFrame", padding=(px(16), px(14), px(16), px(8)))
        lights.pack(fill="both", expand=True, pady=(px(10), 0))
        lights_heading = ttk.Frame(lights, style="Panel.TFrame")
        lights_heading.pack(fill="x", pady=(0, px(4)))
        ttk.Label(lights_heading, text="Your lights", style="Card.TLabel",
                  font=theme.font(10, "bold")).pack(side="left")
        Scan = ttk.Button(lights_heading, text="Scan network",
                          command=lambda: ui_helpers.scan_network(window, tree, message_label, Scan))
        Scan.pack(side="right")

        def on_action(action_name, values):
            device_name, device_ip = values[0], values[1]
            if action_name == "delete":
                if device_repository.remove_from_csv(device_ip):
                    ui_helpers.update_device_list(tree)
                    theme.set_message(message_label, f"Removed {device_name}", "info")
            elif action_name == "add":
                # Fill the form with the scanned bulb; the user can rename it, then saves
                name.delete(0, tk.END)
                name.insert(0, device_name)
                ip.delete(0, tk.END)
                ip.insert(0, device_ip)
                name.focus_set()
                theme.set_message(message_label,
                                  f"Name it if you like, then press Save light (color order: {color_order_var.get()})",
                                  "info")

        tree = DeviceList(lights, px, on_action)
        tree.pack(fill="both", expand=True)
        ui_helpers.update_device_list(tree)

        # Keep a minimum width; the height follows the content (it grows when a scan finds bulbs)
        ttk.Frame(page, width=px(MIN_WIDTH) - 2 * px(20), height=1).pack(side="bottom")

        # Center over the main window (or the screen)
        window.update_idletasks()
        width, height = window.winfo_reqwidth(), window.winfo_reqheight()
        if parent is not None and parent.winfo_viewable():
            x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - height) // 3
        else:
            x = (window.winfo_screenwidth() - width) // 2
            y = (window.winfo_screenheight() - height) // 2
        window.geometry(f"+{max(0, x)}+{max(0, y)}")

        # Handle window close event
        def on_close():
            open_add_device_window.window_opened = False  # Reset the flag when the window is closed
            window.destroy()  # Close the window
            if callback:
                callback()

        window.protocol("WM_DELETE_WINDOW", on_close)

    else:
        # Already open: bring it to the front instead
        window = open_add_device_window.window
        window.deiconify()
        window.lift()
        window.focus_force()
