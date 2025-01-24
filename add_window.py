import csv_controller
import tkinter as tk
from flux_led import WifiLedBulb
import sys
def open_add_device_window(icon, callback=None):
    # Check if the window is already open
    if not hasattr(open_add_device_window, "window_opened") or not open_add_device_window.window_opened(icon):
        open_add_device_window.window_opened = True
            # Create the Tkinter window
        window = tk.Tk()
        window.title("Magic Home Control")

        # Get the current position of the mouse
        x, y = window.winfo_pointerxy()

        # Set the window size
        window_width = 300
        window_height = 150

        # Calculate the position to open the window above the mouse
        # This will place the window slightly above the cursor
        x_position = x - (window_width // 2)  # Center the window over the cursor
        y_position = y - window_height - 10  # Position it above the mouse, with some padding

        # Set the window size and position
        window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

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
        Check_Connection = tk.Button(frame, text="Check", command=lambda: try_to_connect(ip.get()))
        Check_Connection.grid(row=5, column=0, padx=5,pady=5)

        # Quit button for the window
        quit_button = tk.Button(frame, text="Close", command=lambda: on_close())
        quit_button.grid(row=5, column=1, padx=5,pady=5)

        # Check Connection button for the window
        Save = tk.Button(frame, text="Save", command=lambda: save_device(name,ip))
        Save.grid(row=5, column=2, padx=5, pady=5)

        # Add the label to display messages
        message_label = tk.Label(frame, text="", fg="black")
        message_label.grid(row=6, column=1, columnspan=2, pady=5)

        def save_device(name,ip):
            csv_controller.save_to_csv(name.get(),ip.get())
            message_label.config(text="Device Saved", fg="green")

        def try_to_connect(ip):
            try:
                WifiLedBulb(ip)
            except ConnectionRefusedError as e:
                message_label.config(text="Connection Failed", fg="red")
                return
            except Exception as e:
                message_label.config(text="Connection Failed: Invalid IP", fg="red")
                return
            message_label.config(text="Connection Successful", fg="green")
        

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