# Magic Home Control

A Python-based GUI application to control smart WiFi LED bulbs using the `flux_led` library. The application provides a system tray icon, a graphical interface to manage and control connected bulbs, and the ability to save and load device configurations.

## Features
- **System Tray Control:** Run the app from the system tray with quick actions.
- **GUI for Device Management:** Add, remove, and manage smart bulbs.
- **Color and Brightness Adjustment:** Change bulb colors and brightness dynamically.
- **Bulk Control:** Turn all bulbs on or off at once.
- **Persistent Device Storage:** Saves device configurations in a CSV file.
- **Connection Testing:** Check connectivity to bulbs before saving them.

## Installation
### Prerequisites
- Python 3.x
- Required dependencies:
  ```bash
  pip install pillow pystray flux_led numpy
  ```

### Running the Application
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Magic-Home-Control.git
   cd Magic-Home-Control
   ```
2. Run the main script:
   ```bash
   python main.py
   ```

## Usage
- **Adding a Device:** Open the device manager and enter the bulb's name and IP address.
- **Turning Lights On/Off:** Click the system tray icon or use the GUI window.
- **Changing Colors:** Use the GUI color wheel to set RGB values.
- **Adjusting Brightness:** Modify brightness levels with the slider.

## File Structure
```
Magic-Home-Control/
│── main.py                 # Entry point for the application
│── main_window.py           # GUI for light control
│── Device_manager_window.py # GUI for managing connected bulbs
│── bulb_actions.py          # Functions for controlling bulb states
│── csv_controller.py        # Handles reading/writing device information
│── help_funktions.py        # Helper functions for UI and logic
│── shared_state.py          # Stores global states for the app
│── pictures/
│   └── icon.png             # Application icon
│── README.md                # This documentation
│── .gitignore               # Files to ignore in version control
```

## Future Improvements
- [ ] Add support for scheduling lights
- [ ] Enhance UI for better user experience
- [ ] Implement more smart home integrations

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing
Contributions are welcome! Feel free to submit a pull request or open an issue.
