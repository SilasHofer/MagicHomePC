"""System tray icon that talks to KDE Plasma directly (StatusNotifierItem over D-Bus).

pystray's AppIndicator backend always shows a menu on left-click. Plasma's own
protocol instead calls Activate(x, y) on a left-click and ContextMenu(x, y) on a
right-click, with the click position, so the app can open its quick panel right
at the icon. Uses Gio from the system's PyGObject (python3-gobject).
"""
import json
import os
import subprocess
import threading

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

WATCHER = "org.kde.StatusNotifierWatcher"
ITEM_PATH = "/StatusNotifierItem"
INTERFACE_XML = """
<node>
  <interface name="org.kde.StatusNotifierItem">
    <property name="Category" type="s" access="read"/>
    <property name="Id" type="s" access="read"/>
    <property name="Title" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="WindowId" type="i" access="read"/>
    <property name="IconName" type="s" access="read"/>
    <property name="IconPixmap" type="a(iiay)" access="read"/>
    <property name="ItemIsMenu" type="b" access="read"/>
    <property name="Menu" type="o" access="read"/>
    <property name="ToolTip" type="(sa(iiay)ss)" access="read"/>
    <method name="Activate"><arg name="x" type="i" direction="in"/><arg name="y" type="i" direction="in"/></method>
    <method name="SecondaryActivate"><arg name="x" type="i" direction="in"/><arg name="y" type="i" direction="in"/></method>
    <method name="ContextMenu"><arg name="x" type="i" direction="in"/><arg name="y" type="i" direction="in"/></method>
    <method name="Scroll"><arg name="delta" type="i" direction="in"/><arg name="orientation" type="s" direction="in"/></method>
    <signal name="NewIcon"/>
    <signal name="NewTitle"/>
    <signal name="NewToolTip"/>
    <signal name="NewStatus"><arg name="status" type="s"/></signal>
  </interface>
</node>
"""


def available():
    """True when a StatusNotifierItem host (KDE Plasma, and some other desktops) is running."""
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        result = bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
                               "NameHasOwner", GLib.Variant("(s)", (WATCHER,)), GLib.VariantType("(b)"),
                               Gio.DBusCallFlags.NONE, 1000, None)
        return bool(result.unpack()[0])
    except Exception:
        return False


def screen_scale(tk_screen_width):
    """Factor from Plasma's logical coordinates to the X/Tk pixels the windows use.

    With display scaling (e.g. 160%), Plasma reports clicks in logical pixels while
    Tk (running on XWayland) positions windows in physical pixels.
    """
    try:
        data = json.loads(subprocess.run(["kscreen-doctor", "-j"], capture_output=True, text=True,
                                         timeout=3).stdout)
        logical_width = max(
            output["pos"]["x"] + output["size"]["width"] / (output.get("scale") or 1)
            for output in data["outputs"] if output.get("enabled")
        )
        return tk_screen_width / logical_width if logical_width else 1.0
    except Exception:
        return 1.0


def _pixmaps(image):
    """PIL image -> the a(iiay) icon format: ARGB32 in network byte order, a few sizes."""
    icons = []
    for size in (22, 32, 64):
        rgba = image.convert("RGBA").resize((size, size)).tobytes()
        argb = bytearray(len(rgba))
        argb[0::4], argb[1::4], argb[2::4], argb[3::4] = rgba[3::4], rgba[0::4], rgba[1::4], rgba[2::4]
        icons.append((size, size, bytes(argb)))
    return icons


class KdeTray:
    def __init__(self, title, image, on_activate, on_context_menu):
        """on_activate(x, y) / on_context_menu(x, y) run on the tray's own thread."""
        self.title = title
        self.icons = _pixmaps(image)
        self.on_activate = on_activate
        self.on_context_menu = on_context_menu
        self.loop = None
        self._connection = None
        self._registration = None
        self._name_id = None

    # --- D-Bus handlers ---
    def _method_call(self, connection, sender, path, interface, method, parameters, invocation):
        if method in ("Activate", "SecondaryActivate"):
            x, y = parameters.unpack()
            self.on_activate(x, y)
        elif method == "ContextMenu":
            x, y = parameters.unpack()
            self.on_context_menu(x, y)
        invocation.return_value(None)

    def _get_property(self, connection, sender, path, interface, name):
        values = {
            "Category": GLib.Variant("s", "Hardware"),
            "Id": GLib.Variant("s", "magic-home-control"),
            "Title": GLib.Variant("s", self.title),
            "Status": GLib.Variant("s", "Active"),
            "WindowId": GLib.Variant("i", 0),
            "IconName": GLib.Variant("s", ""),
            "IconPixmap": GLib.Variant("a(iiay)", self.icons),
            "ItemIsMenu": GLib.Variant("b", False),  # left-click = Activate, not a menu
            "Menu": GLib.Variant("o", "/NO_DBUSMENU"),  # right-click = ContextMenu
            "ToolTip": GLib.Variant("(sa(iiay)ss)", ("", [], self.title, "Click for quick controls")),
        }
        return values.get(name)

    def _on_name_acquired(self, connection, name):
        connection.call(WATCHER, "/StatusNotifierWatcher", WATCHER, "RegisterStatusNotifierItem",
                        GLib.Variant("(s)", (name,)), None, Gio.DBusCallFlags.NONE, -1, None, None, None)

    # --- Lifecycle ---
    def run(self):
        """Blocking: registers the icon and runs the D-Bus loop until stop()."""
        context = GLib.MainContext.new()
        context.push_thread_default()
        self._connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        interface = Gio.DBusNodeInfo.new_for_xml(INTERFACE_XML).interfaces[0]
        self._registration = self._connection.register_object(
            ITEM_PATH, interface, self._method_call, self._get_property, None)
        name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
        self._name_id = Gio.bus_own_name_on_connection(
            self._connection, name, Gio.BusNameOwnerFlags.NONE, self._on_name_acquired, None)
        self.loop = GLib.MainLoop.new(context, False)
        self.loop.run()
        Gio.bus_unown_name(self._name_id)
        self._connection.unregister_object(self._registration)
        context.pop_thread_default()

    def run_in_thread(self):
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread

    def stop(self):
        if self.loop is not None:
            self.loop.quit()
