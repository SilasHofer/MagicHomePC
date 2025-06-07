import sys
import threading
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
from mainWindow import open_window


# Function to create the system tray icon
def create_image():
    # Create an image with PIL (Python Imaging Library)
    width, height = 64, 64
    image = Image.open("pictures\icon.png")
    draw = ImageDraw.Draw(image)

    # Draw a simple circle (could be an icon)
    draw.ellipse((10, 10, width - 10, height - 10), fill=(255, 0, 0))  # Red circle

    return image

# Function to quit the application (stop the icon and exit)
def quit_action(icon):
    icon.stop()
    sys.exit()


# Function to start the system tray
def run_tray():
    icon = Icon(name="Magic Home Control",icon=create_image(),title="Magic Home Control",menu=Menu(
    MenuItem(text="Left-Click-Action",action=open_window,default=True),
    MenuItem(text="Quit", action=quit_action)
))


    # Run the system tray icon
    icon.run()

# Run the system tray in a separate thread
if __name__ == "__main__":
    tray_thread = threading.Thread(target=run_tray)
    tray_thread.start()
