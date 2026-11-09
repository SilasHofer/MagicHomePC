from . import device_repository
import tkinter as tk
from tkinter import ttk
from . import ui_helpers
from . import theme

COLOR_ORDERS = ("RGB", "GRB", "BGR", "GBR", "RBG", "BRG")


def open_add_device_window(icon, callback=None, parent=None):
    # Check if the window is already open
    if not hasattr(open_add_device_window, "window_opened") or not open_add_device_window.window_opened:
        open_add_device_window.window_opened = True
        # A child of the main window, so it closes together with it (the theme comes from the Tk root)
        window = tk.Toplevel(parent)
        window.title("Device manager")
        window.configure(bg=theme.BG)
        window.resizable(False, False)

        # Reset the flag whenever this window is destroyed, including when the main
        # window is closed and takes this window with it (on_close does not run then)
        def on_destroy(event):
            if event.widget is window:
                open_add_device_window.window_opened = False

        window.bind("<Destroy>", on_destroy)

        # Open the window at the mouse position
        x, y = window.winfo_pointerxy()
        window.geometry(f"+{x}+{y}")  # the size follows the content

        root = ttk.Frame(window, padding=(20, 18))
        root.pack(fill="both", expand=True)

        # --- Header ---
        ttk.Label(root, text="DEVICE MANAGER", style="Kicker.TLabel").pack(anchor="w")
        ttk.Label(root, text="Devices", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Add a light or scan your network", style="Muted.TLabel").pack(anchor="w", pady=(0, 14))

        # --- Form card ---
        card = ttk.Frame(root, style="Card.TFrame", padding=16)
        card.pack(fill="x")
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="NAME", style="CardMuted.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        name = ttk.Entry(card)
        name.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 10))

        ttk.Label(card, text="IP ADDRESS", style="CardMuted.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Label(card, text="COLOR ORDER", style="CardMuted.TLabel").grid(row=2, column=1, sticky="w", padx=(10, 0))
        ip = ttk.Entry(card)
        ip.grid(row=3, column=0, sticky="ew", pady=(4, 14))

        color_order_var = tk.StringVar(value="RGB")
        color_order_dropdown = ttk.Combobox(card, textvariable=color_order_var, state="readonly",
                                            values=COLOR_ORDERS, width=8)
        color_order_dropdown.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(4, 14))
        color_order_dropdown.current(0)

        buttons = ttk.Frame(card, style="Card.TFrame", padding=0)
        buttons.configure(borderwidth=0)
        buttons.grid(row=4, column=0, columnspan=2, sticky="ew")
        buttons.columnconfigure((0, 1, 2), weight=1, uniform="buttons")

        Scan = ttk.Button(buttons, text="Scan network",
                          command=lambda: ui_helpers.scan_network(window, tree, message_label, Scan))
        Scan.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ttk.Button(buttons, text="Test",
                   command=lambda: ui_helpers.try_to_connect(ip.get(), message_label)
                   ).grid(row=0, column=1, sticky="ew", padx=4)

        ttk.Button(buttons, text="Save", style="Accent.TButton",
                   command=lambda: ui_helpers.save_device(name, ip, color_order_var, message_label, tree)
                   ).grid(row=0, column=2, sticky="ew", padx=(4, 0))

        # --- Status line ---
        message_label = theme.message_label(root)
        message_label.pack(fill="x", pady=(10, 10))

        # --- Device table ---
        ttk.Label(root, text="YOUR DEVICES", style="Kicker.TLabel").pack(anchor="w", pady=(0, 6))
        table = ttk.Frame(root)
        table.pack(fill="both", expand=True)

        tree = ttk.Treeview(table, columns=("Name", "IP", "Order", "Action"), show="headings",
                            height=7, selectmode="browse")
        tree.pack(fill="both", expand=True)  # scrolls with the mouse wheel

        for column, title, width, anchor in (
            ("Name", "NAME", 110, "w"),
            ("IP", "IP ADDRESS", 120, "w"),
            ("Order", "ORDER", 80, "center"),
            ("Action", "", 76, "center"),
        ):
            tree.heading(column, text=title, anchor=anchor)
            tree.column(column, width=width, anchor=anchor, stretch=column == "Name")

        theme.style_tree_rows(tree)
        ui_helpers.update_device_list(tree)

        # Clicking the "Action" column deletes a saved device or fills the form with a scanned one
        def on_item_click(event):
            region = tree.identify("region", event.x, event.y)
            if region == "cell":
                col = tree.identify_column(event.x)
                row_id = tree.identify_row(event.y)
                if col == "#4":  # This is the "Action" column
                    action_text = str(tree.item(row_id)['values'][3]).lower()
                    device_ip = tree.item(row_id)['values'][1]  # Get the IP of the clicked row
                    if "delete" in action_text:
                        if device_repository.remove_from_csv(device_ip):
                            ui_helpers.update_device_list(tree)
                            theme.set_message(message_label, f"Removed {device_ip}", "info")
                    if "add" in action_text:
                        found_name = tree.item(row_id)['values'][0]
                        name.delete(0, tk.END)
                        name.insert(0, found_name)
                        ip.delete(0, tk.END)
                        ip.insert(0, device_ip)
                        theme.set_message(message_label, f"Press Save to add {device_ip} (color order: {color_order_var.get()})", "info")

        tree.bind("<ButtonRelease-1>", on_item_click)

        # --- Footer ---
        ttk.Button(root, text="Close", command=lambda: on_close()).pack(anchor="e", pady=(12, 0))

        # Handle window close event
        def on_close():
            open_add_device_window.window_opened = False  # Reset the flag when the window is closed
            window.destroy()  # Close the window
            if callback:
                callback()

        window.protocol("WM_DELETE_WINDOW", on_close)

    else:
        print("Window is already open.")
