"""Dark theme for the desktop app, matching the web app's colors.

Only depends on tkinter so it can be imported from anywhere without
running into the ui_helpers <-> bulb_actions circular import.
"""
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# Palette (same as the web app's dark mode)
BG = "#151916"
SURFACE = "#202721"
SURFACE_HOVER = "#2c352e"
BUTTON = "#2c352e"
BUTTON_HOVER = "#38433a"
FIELD = "#151916"
BORDER = "#353d37"
BORDER_STRONG = "#485149"
TEXT = "#f4f5ed"
MUTED = "#9aa49b"
ACCENT = "#ff8266"
ACCENT_HOVER = "#ff9b83"
ACCENT_TEXT = "#202522"
ERROR = "#ff9a82"
SUCCESS = "#a9db8b"
WARNING = "#f2c66d"

MESSAGE_COLORS = {"info": MUTED, "success": SUCCESS, "warning": WARNING, "error": ERROR}

_FONT_CANDIDATES = ("Inter", "Cantarell", "Noto Sans", "Segoe UI", "Helvetica")
FONT_FAMILY = "TkDefaultFont"


def _pick_font(root):
    available = set(tkfont.families(root))
    for family in _FONT_CANDIDATES:
        if family in available:
            return family
    return "TkDefaultFont"


def font(size=10, weight="normal"):
    return (FONT_FAMILY, size, weight)


def apply_theme(root):
    """Style every ttk widget under this Tk root. Call once, right after tk.Tk()."""
    global FONT_FAMILY
    FONT_FAMILY = _pick_font(root)

    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use("clam")

    base = font(10)
    style.configure(".", background=BG, foreground=TEXT, font=base,
                    bordercolor=BORDER, lightcolor=BG, darkcolor=BG,
                    troughcolor=BORDER, focuscolor=ACCENT,
                    selectbackground=ACCENT, selectforeground=ACCENT_TEXT,
                    insertcolor=TEXT, fieldbackground=FIELD)

    # Frames
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=SURFACE, relief="solid", borderwidth=1,
                    bordercolor=BORDER)

    # Labels
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=font(15, "bold"))
    style.configure("Kicker.TLabel", background=BG, foreground=ACCENT, font=font(8, "bold"))
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=font(9))
    style.configure("Card.TLabel", background=SURFACE, foreground=TEXT)
    style.configure("CardMuted.TLabel", background=SURFACE, foreground=MUTED, font=font(8, "bold"))
    style.configure("Value.TLabel", background=SURFACE, foreground=ACCENT, font=font(10, "bold"))

    # Buttons
    style.configure("TButton", background=BUTTON, foreground=TEXT, bordercolor=BORDER_STRONG,
                    lightcolor=BUTTON, darkcolor=BUTTON, padding=(8, 7), font=font(9, "bold"),
                    focusthickness=0, relief="flat")
    style.map("TButton",
              background=[("disabled", SURFACE), ("pressed", BORDER), ("active", BUTTON_HOVER)],
              foreground=[("disabled", MUTED)],
              lightcolor=[("disabled", SURFACE), ("active", BUTTON_HOVER)],
              darkcolor=[("disabled", SURFACE), ("active", BUTTON_HOVER)])

    style.configure("Accent.TButton", background=ACCENT, foreground=ACCENT_TEXT, bordercolor=ACCENT,
                    lightcolor=ACCENT, darkcolor=ACCENT)
    style.map("Accent.TButton",
              background=[("disabled", BORDER), ("pressed", ACCENT), ("active", ACCENT_HOVER)],
              foreground=[("disabled", MUTED)],
              bordercolor=[("active", ACCENT_HOVER)],
              lightcolor=[("active", ACCENT_HOVER)], darkcolor=[("active", ACCENT_HOVER)])

    style.configure("Big.Accent.TButton", padding=(12, 11), font=font(10, "bold"))

    style.configure("Danger.TButton", background=BG, foreground=ERROR, bordercolor=BORDER,
                    lightcolor=BG, darkcolor=BG)
    style.map("Danger.TButton",
              background=[("pressed", BORDER), ("active", SURFACE)],
              lightcolor=[("active", SURFACE)], darkcolor=[("active", SURFACE)])

    # Inputs
    style.configure("TEntry", fieldbackground=FIELD, foreground=TEXT, bordercolor=BORDER_STRONG,
                    lightcolor=FIELD, darkcolor=FIELD, padding=(8, 6), insertcolor=TEXT)
    style.map("TEntry", bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)])

    style.configure("TCombobox", fieldbackground=FIELD, background=SURFACE, foreground=TEXT,
                    arrowcolor=TEXT, bordercolor=BORDER_STRONG, lightcolor=FIELD, darkcolor=FIELD,
                    padding=(8, 6))
    style.map("TCombobox",
              fieldbackground=[("readonly", FIELD)],
              foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", FIELD)],
              selectforeground=[("readonly", TEXT)],
              background=[("active", SURFACE_HOVER)],
              bordercolor=[("focus", ACCENT)])
    # The dropdown list of a combobox is a plain Tk listbox
    root.option_add("*TCombobox*Listbox.background", SURFACE)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", ACCENT_TEXT)
    root.option_add("*TCombobox*Listbox.font", base)
    root.option_add("*TCombobox*Listbox.borderWidth", 0)

    # Slider
    style.configure("Horizontal.TScale", background=ACCENT, troughcolor=BORDER,
                    bordercolor=SURFACE, lightcolor=ACCENT, darkcolor=ACCENT,
                    sliderlength=20, sliderthickness=20, gripcount=0, borderwidth=0)
    style.map("Horizontal.TScale", background=[("active", ACCENT_HOVER)])

    # Device table
    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=SURFACE, darkcolor=SURFACE,
                    rowheight=28, font=font(9))
    style.map("Treeview",
              background=[("selected", SURFACE_HOVER)],
              foreground=[("selected", TEXT)])
    style.configure("Treeview.Heading", background=BG, foreground=MUTED, bordercolor=BORDER,
                    lightcolor=BG, darkcolor=BG, relief="flat", font=font(8, "bold"), padding=(6, 6))
    style.map("Treeview.Heading", background=[("active", BG)])



def message_label(parent):
    """A status line. Uses tk.Label so its color can change per message."""
    return tk.Label(parent, text="", bg=BG, fg=MUTED, font=font(9), anchor="w", justify="left")


def set_message(label, text, kind="info"):
    """Show a status message; kind is info, success, warning or error."""
    label.config(text=text, fg=MESSAGE_COLORS.get(kind, MUTED))


def style_tree_rows(tree):
    tree.tag_configure("odd", background=SURFACE)
    tree.tag_configure("even", background="#1b211c")
    tree.tag_configure("found", foreground=ACCENT)
