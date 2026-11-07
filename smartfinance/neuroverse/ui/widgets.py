import tkinter as tk
from tkinter import ttk
from . import theme as T


def label(parent, text, size=11, bold=False, color=None, bg=None, **kwargs):
    return tk.Label(parent, text=text, font=(T.FONT, size, 'bold' if bold else 'normal'),
                    fg=color or T.TEXT, bg=bg or T.SURFACE, anchor='w', **kwargs)


def panel(parent, title=None):
    outer = tk.Frame(parent, bg=T.SURFACE, highlightbackground=T.BORDER,
                     highlightthickness=1, padx=20, pady=16)
    if title:
        label(outer, title, 13, True).pack(anchor='w', pady=(0, 11))
    return outer


def button(parent, text, command, secondary=False):
    b = tk.Button(parent, text=text, command=command,
                  font=(T.FONT, 10, 'bold'), bd=0, padx=17, pady=11,
                  cursor='hand2', relief='flat', highlightthickness=0,
                  bg=T.PRIMARY_LIGHT if secondary else T.PRIMARY,
                  fg=T.PRIMARY if secondary else '#ffffff',
                  activebackground='#ddd7ff' if secondary else '#4b43db',
                  activeforeground=T.PRIMARY if secondary else '#ffffff')
    normal = b['bg']
    hover = '#ddd7ff' if secondary else '#4b43db'
    b.bind('<Enter>', lambda e: b.config(bg=hover))
    b.bind('<Leave>', lambda e: b.config(bg=normal))
    return b


class Screen(ttk.Frame):
    def __init__(self, parent, store, bus, navigate, title, subtitle):
        super().__init__(parent, style='Page.TFrame', padding=25)
        self.store = store
        self.bus = bus
        self.navigate = navigate
        label(self, title, 25, True, bg=T.BG).pack(anchor='w', pady=(0, 3))
        label(self, subtitle, 10, color=T.MUTED, bg=T.BG).pack(anchor='w', pady=(0, 17))

    def refresh(self):
        pass


def hex_rgb(value):
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(rgb):
    return '#%02x%02x%02x' % tuple(max(0, min(255, round(v))) for v in rgb)


def interpolate(c1, c2, p):
    a, b = hex_rgb(c1), hex_rgb(c2)
    return rgb_hex(tuple(x + (y - x) * p for x, y in zip(a, b)))


def gradient(canvas, width, height, start, end, stripes=70):
    """Canvas background gradient, drawn without Pillow or external dependencies."""
    for i in range(stripes):
        x1 = width * i / stripes
        x2 = width * (i + 1) / stripes + 1
        canvas.create_rectangle(x1, 0, x2, height, fill=interpolate(start, end, i / max(stripes-1,1)), outline='')
