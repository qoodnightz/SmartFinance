import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from . import theme as T


def label(parent, text, size=11, bold=False, color=None, bg=None, **kwargs):
    return tk.Label(parent, text=text, font=(T.FONT, size, 'bold' if bold else 'normal'),
                    fg=color or T.TEXT, bg=bg or T.SURFACE, anchor='w', **kwargs)


def panel(parent, title=None):
    outer = tk.Frame(parent, bg=T.SURFACE, highlightbackground=T.BORDER,
                     highlightthickness=1, padx=20, pady=16)
    if title:
        label(outer, title, 13, True, color=T.PRIMARY_DARK).pack(anchor='w', pady=(0, 11))
    return outer


class FlatButton(tk.Label):
    """A coloured button that works the same on every OS and can be used with the keyboard.

    (Plain tk.Button ignores colours on macOS, which is why the old buttons looked grey.)
    Tab moves to it, Enter or Space presses it, and a coloured ring shows where the focus is.
    """

    def __init__(self, parent, text, command, *, bg, fg, hover_bg, hover_fg=None,
                 focus_color=None, font=None, padx=18, pady=11, anchor='center', **kw):
        super().__init__(parent, text=text, bg=bg, fg=fg, font=font or (T.FONT, 10, 'bold'),
                         padx=padx, pady=pady, anchor=anchor, cursor='hand2', takefocus=1,
                         highlightthickness=2, highlightbackground=bg,
                         highlightcolor=focus_color or T.FOCUS,
                         disabledforeground=T.MUTED, **kw)
        self._command = command
        self.set_colors(bg, fg, hover_bg, hover_fg)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', lambda _e: self.invoke())
        for key in ('<Return>', '<KP_Enter>', '<space>'):
            self.bind(key, lambda _e: self.invoke())

    def set_colors(self, bg, fg, hover_bg, hover_fg=None):
        self._bg, self._fg, self._hover_bg, self._hover_fg = bg, fg, hover_bg, hover_fg or fg
        self.configure(bg=bg, fg=fg, highlightbackground=bg)

    def _enabled(self):
        return str(self.cget('state')) != 'disabled'

    def _on_enter(self, _e):
        if self._enabled():
            self.configure(bg=self._hover_bg, fg=self._hover_fg, highlightbackground=self._hover_bg)

    def _on_leave(self, _e):
        self.configure(bg=self._bg, fg=self._fg, highlightbackground=self._bg)

    def invoke(self):
        if self._enabled() and self._command:
            self._command()
        return 'break'


def button(parent, text, command, secondary=False, danger=False, **kw):
    if danger:
        colors = dict(bg='#fbe9ee', fg=T.DANGER, hover_bg='#f5cfd9')
    elif secondary:
        colors = dict(bg=T.PRIMARY_LIGHT, fg=T.PRIMARY, hover_bg='#dccdeb')
    else:
        colors = dict(bg=T.PRIMARY, fg='#ffffff', hover_bg=T.PRIMARY_DARK)
    return FlatButton(parent, text, command, **colors, **kw)


class Screen(ttk.Frame):
    def __init__(self, parent, store, bus, navigate, title, subtitle):
        super().__init__(parent, style='Page.TFrame', padding=25)
        self.store = store
        self.bus = bus
        self.navigate = navigate
        label(self, title, 25, True, color=T.PRIMARY_DARK, bg=T.BG).pack(anchor='w', pady=(0, 3))
        label(self, subtitle, 10, color=T.MUTED, bg=T.BG).pack(anchor='w', pady=(0, 17))

    def refresh(self):
        pass


# ---------- larger text (accessibility) ----------
_BASE_FONTS = {}


def _walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


def _font_tuple(base, scale):
    family, size, weight, slant = base
    style = [] if weight == 'normal' else [weight]
    if slant != 'roman':
        style.append('italic')
    return (family, max(7, round(size * scale)), *style)


def _base_of(widget, key, spec):
    base = _BASE_FONTS.get(key)
    if base is None:
        actual = tkfont.Font(root=widget, font=spec).actual()
        base = (actual['family'], abs(int(actual['size'])), actual['weight'], actual['slant'])
        _BASE_FONTS[key] = base
    return base


def rescale(root):
    """Re-size the text of every widget under `root` to match theme.TEXT_SCALE.

    The first time a widget is seen its normal size is remembered, so switching larger
    text on and off always goes back to the exact original sizes. Canvas drawings use
    theme.font() instead. A problem with one widget never stops the rest.
    """
    scale = T.TEXT_SCALE
    for widget in _walk(root):
        try:
            if isinstance(widget, tk.Canvas):
                continue
            key = str(widget)
            if isinstance(widget, tk.Text):
                for tag in widget.tag_names():
                    spec = widget.tag_cget(tag, 'font')
                    if spec:
                        widget.tag_configure(tag, font=_font_tuple(_base_of(widget, (key, tag), spec), scale))
            spec = widget.cget('font')
            if spec:
                widget.configure(font=_font_tuple(_base_of(widget, key, spec), scale))
        except Exception:
            continue


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
