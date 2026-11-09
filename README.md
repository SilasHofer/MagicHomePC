# Magic Home Control

A local smart-light controller for Flux LED bulbs. The project provides a FastAPI backend, an Angular web interface, and a Tkinter desktop app that lives in the system tray.

## Architecture

```text
Angular web app  ->  FastAPI backend  ->  Flux LED bulbs
Tkinter desktop  ->  local desktop client
                         |
                    shared SQLite database
```

The backend is the API boundary for the web application. The desktop client remains available and shares device configuration through the same SQLite database.

## Features

- Modern responsive web control room
- Dark mode by default, with a saved light-mode option
- Accurate HSV color wheel and RGB controls
- Brightness control that can recover after reaching 0%
- Turn one bulb on or off
- Turn all configured bulbs on or off
- Add, test, and remove devices
- Configurable RGB channel order: RGB, GRB, BGR, GBR, RBG, or BRG
- FastAPI interactive documentation
- Desktop app in the system tray: click the icon for a compact quick-control popup, or open the full window
- Network scan that finds bulbs and adds them in a few clicks (desktop app everywhere, web app on Linux)
- Installable desktop app with an app-menu / Start-menu entry and start at login (Linux and Windows)
- SQLite device storage

## Screenshots

### Web Application

The web application runs as a modern control room with device controls, a color wheel, brightness control, device management, and dark mode.

![Web control room](docs/screenshots/web-control-room.png)

![Web device manager](docs/screenshots/web-device-manager.png)

### Desktop Application

The desktop app lives in the system tray and uses the same dark design and device database as the web app.

**Quick controls.** Clicking the tray icon opens a compact popup just above the taskbar: power switch, brightness, color presets, All on / All off, and a link to the full app. Clicking anywhere else closes it.

![Desktop quick-control popup](docs/screenshots/desktop-quick-popup.png)

**Main window.** Power switch, color wheel with presets and RGB fields, and a brightness slider you can click or drag.

![Desktop main window](docs/screenshots/desktop-main-window.png)

**Devices.** Add a light by IP address, or scan your network and add the bulbs it finds.

![Desktop device manager](docs/screenshots/desktop-device-manager.png)

## Platform Support

| | Linux | Windows | macOS |
| --- | --- | --- | --- |
| Desktop app | Yes, tested on Fedora with KDE Plasma | Yes, not yet tested on a real Windows machine | Runs from source, not tested |
| App menu entry and start at login | Yes | Yes (Start menu and Startup folder) | No |
| Web app (Docker) | Yes, with `compose.yaml` | Yes, with `compose.bridge.yaml` | Yes, with `compose.bridge.yaml` |
| Network scan | Desktop app and web app | Desktop app only | Desktop app only |

The web app's network scan finds bulbs with a UDP broadcast. On Linux the backend container uses the host network, so the broadcast reaches your home network. Docker Desktop on Windows and macOS runs containers inside a virtual machine, where that is not possible; there you add bulbs by IP address in the web app, or scan with the desktop app (both share the same device list when the desktop app runs from this repository).

## Requirements

**Web app (Docker):**

- Linux: [Docker Engine](https://docs.docker.com/engine/install/) with the Compose plugin (`docker compose`). Use the native engine, not Docker Desktop for Linux: the backend needs the host network for the scan.
- Windows and macOS: [Docker Desktop](https://www.docker.com/products/docker-desktop/).
- The bulbs must be on the same local network as the computer running Docker.

**Desktop app:**

- Python 3.11 or newer.
- Linux: Tkinter and PyGObject from your distribution (Fedora: `python3-tkinter python3-gobject`, Debian/Ubuntu: `python3-tk python3-gi`). PyGObject is used for the KDE Plasma tray icon.
- Windows: the installer from [python.org](https://www.python.org/downloads/) already includes Tkinter. To install the app straight from GitHub you also need [Git](https://git-scm.com/download/win).

## Run The Web Application

**Linux**, from the repository root:

```bash
docker compose up --build
```

The backend runs as user and group 1000 so that `data/devices.db` stays writable for the desktop app. If your own user ID is different (check with `id -u`), tell Docker once before starting:

```bash
printf 'UID=%s\nGID=%s\n' "$(id -u)" "$(id -g)" > .env
```

**Windows and macOS** (Docker Desktop), from the repository root:

```powershell
docker compose -f compose.bridge.yaml up --build
```

Open the applications here:

- Web frontend: http://localhost:8080
- API documentation: http://localhost:8000/docs
- API health check: http://localhost:8000/api/health

Run the services in the background by adding `-d`, for example `docker compose up -d --build`. Useful commands (add `-f compose.bridge.yaml` after `docker compose` on Windows and macOS):

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
```

## Install The Desktop App

The desktop app can be installed like a normal application: you get a `magic-home` command, an entry in the app menu (Linux) or Start menu (Windows), and it starts when you log in. It does not need Docker.

### Linux

Tested on Fedora with KDE Plasma:

```bash
sudo dnf install pipx python3-tkinter python3-gobject      # Debian/Ubuntu: sudo apt install pipx python3-tk python3-gi
pipx install --system-site-packages git+https://github.com/SilasHofer/MagicHomePC.git
magic-home --install-desktop-entry
```

- `pipx` installs the app into its own isolated environment and puts the `magic-home` command on your PATH. `--system-site-packages` lets it use the system's Tkinter and PyGObject.
- `magic-home --install-desktop-entry` adds **Magic Home** to the app menu and starts it when you log in. Add `--no-autostart` for the app menu only.

### Windows

1. Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/) and [Git](https://git-scm.com/download/win).
2. In PowerShell or Command Prompt, install pipx and add its folder to your PATH:

   ```powershell
   py -m pip install --user pipx
   py -m pipx ensurepath
   ```

3. Close the terminal and open a new one (so the PATH change applies), then install the app and add it to the Start menu:

   ```powershell
   pipx install git+https://github.com/SilasHofer/MagicHomePC.git
   magic-home --install-desktop-entry
   ```

`--install-desktop-entry` creates a **Magic Home** shortcut in the Start menu and one in your Startup folder, so it starts when you log in (add `--no-autostart` to skip that). The shortcuts start the app without a console window. Running `magic-home` in a terminal also works; the terminal then stays open while the app runs.

### Updating and removing

| | Command |
| --- | --- |
| Update to the latest version | `pipx reinstall magic-home-control` |
| Install from a local checkout | `pipx install --system-site-packages .` in the repository folder (Windows: without `--system-site-packages`); add `--force` to replace an existing install |
| Remove the menu and autostart entries | `magic-home --uninstall-desktop-entry` |
| Uninstall the app | `pipx uninstall magic-home-control` (run the line above first) |

Only one copy of the app runs at a time; starting it again just reports that it is already in the system tray.

### Where your devices are stored

The installed app keeps its own device list per user:

| System | Location |
| --- | --- |
| Linux | `~/.local/share/magic-home/devices.db` |
| Windows | `%APPDATA%\Magic Home\devices.db` |
| macOS | `~/Library/Application Support/Magic Home/devices.db` |

When you run the app from a checkout of this repository (see below), it keeps using the repository's `data/devices.db`, which the web app uses too. To make the installed app share that database, set the environment variable `MAGIC_HOME_DEVICES_DB` to the full path of `data/devices.db`. To take your current devices into the installed app instead, copy `data/devices.db` to the location above.

## Run The Desktop App From Source

For development, run the app straight from this repository. Create a virtual environment and install the app in editable mode, so code changes apply immediately.

**Linux** (`--system-site-packages` lets it use the system's Tkinter and PyGObject):

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -e .
.venv/bin/python -m desktop.app.main
```

**Windows:**

```powershell
py -m venv .venv
.venv\Scripts\pip install -e .
.venv\Scripts\python -m desktop.app.main
```

The app adds an icon to the system tray:

- **Left-click** the icon: open or close the quick-control popup.
- **Right-click** the icon: menu with Quick controls, Open Magic Home, and Quit.
- **Open app** in the popup (or **Open Magic Home** in the menu) opens the full window. Its **Devices** button opens the device manager.

On KDE Plasma the app talks to the Plasma tray directly, so a left-click opens the popup right at the icon. On other systems (for example Windows or GNOME) it uses `pystray`, where a left-click opens the quick controls as well. On GNOME a tray icon needs the AppIndicator extension.

Run from source, the desktop app uses the repository's `data/devices.db`, so devices added in the web app also appear here and the other way around.

## Device Configuration

Add bulbs in the web app with **Manage devices**, or in the desktop app with **Devices**. A device must be reachable before it can be saved.

### Scan for devices

Instead of typing an IP address, you can search the local network for Flux LED bulbs:

- **Desktop:** open the full app, click **Devices**, then **Scan network** in the *Your lights* card. Bulbs that are not saved yet appear with an **Add** button that fills in the form; rename the light if you like, pick the color order and click **Save light**.
- **Web (Linux only):** open **Manage devices** and click **Scan network**. Click **Use** next to a bulb to fill in the form, pick the channel order, then click **Add device**. On Windows and macOS the scan finds nothing (see [Platform Support](#platform-support)); add bulbs by IP address there.

The web app stores its devices in `data/devices.db` (created on the first backend start). The API returns HTTP 504 when a registered or new device is unreachable: the bulb must be powered on and on the same network as the computer running Docker.

## API Overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/devices` | List devices |
| POST | `/api/devices` | Test and add a device |
| POST | `/api/devices/check` | Check an IP address |
| DELETE | `/api/devices/{ip}` | Remove a device |
| GET | `/api/devices/{ip}/state` | Read power, color, and brightness |
| POST | `/api/devices/{ip}/on` | Turn one device on |
| POST | `/api/devices/{ip}/off` | Turn one device off |
| POST | `/api/devices/all/on` | Turn all devices on |
| POST | `/api/devices/all/off` | Turn all devices off |
| PUT | `/api/devices/{ip}/color` | Set RGB color |
| PUT | `/api/devices/{ip}/brightness` | Set brightness from 0 to 100 |

## Project Structure

```text
MagicHomePC/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI routes
│   │   ├── bulb_service.py      Flux bulb operations
│   │   ├── repository.py        SQLite persistence
│   │   └── models.py            API models
│   ├── tests/                   Backend tests
│   └── Dockerfile
├── frontend/
│   ├── src/app/                 Angular application
│   ├── Dockerfile
│   └── nginx.conf
├── desktop/
│   ├── app/                     Tkinter and tray client
│   │   ├── main.py              Entry point and `magic-home` command
│   │   ├── kde_tray.py          KDE Plasma tray icon (left-click popup, right-click menu)
│   │   ├── quick_panel.py       Quick-control popup
│   │   ├── mainWindow.py        Main window
│   │   ├── DeviceManager.py     Device manager window
│   │   ├── widgets.py           Shared controls: switch, slider, color presets
│   │   ├── theme.py             Colors, styles and app icon
│   │   ├── desktop_entry.py     App menu / Start menu and autostart entries
│   │   ├── paths.py             Where the device database is stored
│   │   └── device_repository.py SQLite persistence adapter
│   ├── assets/                  App icon
│   └── tests/                   Desktop tests
├── docs/screenshots/            README screenshots
├── data/
│   ├── devices.csv              Migration seed file
│   └── devices.db               Runtime SQLite database
├── compose.yaml                 Docker setup for Linux (host network)
├── compose.bridge.yaml          Docker setup for Windows and macOS
├── pyproject.toml               Desktop app package (pipx / pip)
└── README.md
```

## Testing

The tests also run automatically on GitHub for every push and pull request (`.github/workflows/tests.yml`).

Desktop tests, from the repository root (with the virtual environment from [Run The Desktop App From Source](#run-the-desktop-app-from-source)):

```bash
.venv/bin/pip install pytest
.venv/bin/python -m pytest desktop/tests -q          # Windows: .venv\Scripts\pip install pytest, then .venv\Scripts\python -m pytest desktop/tests -q
```

Backend tests, in their own virtual environment:

```bash
python3 -m venv .venv-backend
.venv-backend/bin/pip install -r backend/requirements.txt pytest
.venv-backend/bin/python -m pytest backend/tests -q
```

Validate the Python source:

```bash
python3 -m compileall -q backend desktop
```

## Security

This application is intended for a trusted local network. Do not expose the API directly to the internet. Add authentication, HTTPS, and stronger network controls before remote access.

## License

This project is licensed under the MIT License. See `LICENSE`.
