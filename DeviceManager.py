import csv_controller
import tkinter as tk
from tkinter import ttk
import ui_helpers

def open_add_device_window(icon, callback=None):
    # Check if the window is already open
    if not hasattr(open_add_device_window, "window_opened") or not open_add_device_window.window_opened:
        open_add_device_window.window_opened = True
            # Create the Tkinter window
        window = tk.Tk()
        window.title("Device manager")

        # Get the current position of the mouse
        x, y = window.winfo_pointerxy()

        # Set the window size
        window_width = 300
        window_height = 350

        # Set the window size and position
        window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        frame = tk.Frame(window)
        frame.pack(pady=5)

        name = tk.Entry(frame)
        name.grid(row=1, column=1, padx=5)

        # Label for RGB
        tk.Label(frame, text="Name:").grid(row=0, column=1, padx=5)

        ip = tk.Entry(frame)
        ip.grid(row=3, column=1, padx=5)

        # Label for RGB
        tk.Label(frame, text="IP:").grid(row=2, column=1, padx=5)

        # Check Connection button for the window
        Check_Connection = tk.Button(frame, text="Check", command=lambda: ui_helpers.try_to_connect(ip.get(),message_label))
        Check_Connection.grid(row=5, column=0, padx=5,pady=5)

        # Check Connection button for the window
        Scan_devices = tk.Button(frame, text="Scan", command=lambda: ui_helpers.Scan_tuya_devices(tree))
        Scan_devices.grid(row=5, column=1, padx=5,pady=5)


        # Quit button for the window
        quit_button = tk.Button(frame, text="Close", command=lambda: on_close())
        quit_button.grid(row=8, column=1, padx=5,pady=5)

        # Save button
        Save = tk.Button(
            frame,
            text="Save",
            command=lambda: (
                ui_helpers.save_device(name, ip, message_label, tree)
            )
        )
        Save.grid(row=5, column=2, padx=5, pady=5)

        # Add the label to display messages
        message_label = tk.Label(frame, text="", fg="black")
        message_label.grid(row=6, column=1, columnspan=2, pady=5)

       # Add a Treeview (table-like) to display devices
        tree = ttk.Treeview(frame, columns=("Name", "IP","Type","Action"), show="headings", height=5)
        tree.grid(row=7, column=0, columnspan=3,padx=5, pady=5)

        # Define columns for the Treeview (table)
        tree.heading("Name", text="Name")
        tree.heading("IP", text="IP")
        tree.heading("Type", text="Type")
        tree.heading("Action", text="Action")

        tree.column("Name", width=75)
        tree.column("IP", width=75)
        tree.column("Type", width=75)
        tree.column("Action", width=50)

        ui_helpers.update_device_list(tree)


        # Bind button to "Actions" column in each row
        def on_item_click(event):
            region = tree.identify("region", event.x, event.y)
            if region == "cell":
                col = tree.identify_column(event.x)
                row_id = tree.identify_row(event.y)
                if col == "#4":  # This is the "Actions" column
                    action_text = tree.item(row_id)['values'][3].lower()
                    device_ip = tree.item(row_id)['values'][1]  # Get the IP of the clicked row
                    if(action_text == "delete"):
                        if csv_controller.remove_from_csv(device_ip):
                            ui_helpers.update_device_list(tree)
                    if(action_text == "add"):
                        ui_helpers.add_tuya_device(tree,row_id)

        # Bind click event to the treeview
        tree.bind("<ButtonRelease-1>", on_item_click)


        # Handle window close event
        def on_close():
            open_add_device_window.window_opened = False  # Reset the flag when the window is closed
            window.destroy()  # Close the window
            if callback:
                callback() 

        # Bind the window close event to the on_close function
        window.protocol("WM_DELETE_WINDOW", on_close)
        # Start the Tkinter main loop
        window.mainloop()

    else:
        print("Window is already open.")