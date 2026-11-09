"""Custom modern controls drawn on a canvas, shared by the quick popup and the main window."""
import tkinter as tk

from . import theme

# (name, (R, G, B)) presets shown as color dots
PRESETS = (
    ("Warm white", (255, 170, 90)),
    ("Cool white", (255, 255, 255)),
    ("Red", (255, 0, 0)),
    ("Orange", (255, 110, 0)),
    ("Green", (0, 255, 60)),
    ("Blue", (0, 90, 255)),
    ("Purple", (150, 0, 255)),
    ("Pink", (255, 0, 150)),
)


def scaler(widget):
    """Convert design sizes to pixels for this display (1.0 at 96 dpi, ~1.6 on a HiDPI laptop)."""
    scale = max(1.0, float(widget.tk.call("tk", "scaling")) / (96 / 72))
    return lambda value: round(value * scale)


class ToggleSwitch(tk.Canvas):
    """A pill-shaped on/off switch: coral with the knob on the right when on."""

    def __init__(self, parent, px, command, width=44, height=24, bg=theme.SURFACE):
        self.w, self.h = px(width), px(height)
        super().__init__(parent, width=self.w, height=self.h, bg=bg, highlightthickness=0, cursor="hand2")
        self.px = px
        self.on = False
        self.command = command
        self.bind("<Button-1>", lambda event: self._click())
        self._draw()

    def set(self, on):
        self.on = bool(on)
        self._draw()

    def _click(self):
        self.set(not self.on)  # immediate feedback; the command may set it back on failure
        self.command()

    def _draw(self):
        self.delete("all")
        h, w = self.h, self.w
        color = theme.ACCENT if self.on else theme.BORDER_STRONG
        self.create_oval(0, 0, h, h, fill=color, outline=color)
        self.create_oval(w - h, 0, w, h, fill=color, outline=color)
        self.create_rectangle(h / 2, 0, w - h / 2, h, fill=color, outline=color)
        inset = max(2, round(h * 0.13))
        knob_x = w - h if self.on else 0
        self.create_oval(knob_x + inset, inset, knob_x + h - inset, h - inset, fill=theme.TEXT, outline=theme.TEXT)


class Slider(tk.Canvas):
    """Rounded slider from 1 to 100. Click anywhere to jump there, or drag.

    on_change(value) runs only when the user moves it and the value really changes;
    set(value) moves it without calling on_change. on_display(value) runs on every redraw.
    """

    def __init__(self, parent, px, on_change, height=22, thickness=6, bg=theme.SURFACE):
        self.h = px(height)
        super().__init__(parent, height=self.h, bg=bg, highlightthickness=0, cursor="hand2")
        self.px = px
        self.thickness = px(thickness)
        self.value = 100
        self.sent = None
        self.on_change = on_change
        self.on_display = None
        self.bind("<Configure>", lambda event: self._draw())
        self.bind("<Button-1>", self._drag)
        self.bind("<B1-Motion>", self._drag)

    def set(self, value):
        self.value = max(1, min(100, round(value)))
        self.sent = self.value
        self._draw()

    def _track(self):
        knob = self.h / 2
        return knob, max(knob + 1, self.winfo_width() - knob)

    def _drag(self, event):
        left, right = self._track()
        self.value = max(1, min(100, round(1 + (event.x - left) / (right - left) * 99)))
        self._draw()
        if self.value != self.sent:
            self.sent = self.value
            self.on_change(self.value)

    def _draw(self):
        self.delete("all")
        left, right = self._track()
        mid = self.h / 2
        x = left + (self.value - 1) / 99 * (right - left)
        self.create_line(left, mid, right, mid, width=self.thickness, fill=theme.BORDER_STRONG, capstyle="round")
        self.create_line(left, mid, x, mid, width=self.thickness, fill=theme.ACCENT, capstyle="round")
        r = self.h / 2 - max(1, self.px(2))
        self.create_oval(x - r, mid - r, x + r, mid + r, fill=theme.TEXT, outline=theme.ACCENT,
                         width=max(1, self.px(2)))
        if self.on_display:
            self.on_display(self.value)


class ColorDots(tk.Canvas):
    """A row of preset colors spread over the full width; the picked one gets a coral ring."""

    def __init__(self, parent, px, on_pick, size=26, bg=theme.SURFACE):
        self.size = px(size)
        self.ring = max(3, px(size * 0.15))
        super().__init__(parent, height=self.size + 2 * self.ring, bg=bg, highlightthickness=0, cursor="hand2")
        self.selected = None
        self.on_pick = on_pick
        self.bind("<Configure>", lambda event: self._draw())

    def select(self, name):
        self.selected = name
        self._draw()

    def _draw(self):
        self.delete("all")
        count = len(PRESETS)
        step = (self.winfo_width() - 2 * self.ring - self.size) / (count - 1)
        for index, (name, color) in enumerate(PRESETS):
            left, top = self.ring + index * step, self.ring
            if name == self.selected:
                self.create_oval(left - self.ring + 1, top - self.ring + 1, left + self.size + self.ring - 1,
                                 top + self.size + self.ring - 1, outline=theme.ACCENT, width=2)
            item = self.create_oval(left, top, left + self.size, top + self.size,
                                    fill="#{:02x}{:02x}{:02x}".format(*color), outline=theme.BORDER_STRONG)
            self.tag_bind(item, "<Button-1>", lambda event, c=color, n=name: self.on_pick(c, n))
