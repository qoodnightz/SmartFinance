"""Single-owner visual shell. No changes to card or financial contracts."""
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from neuroverse.core.events import EventBus, PREFERENCES_CHANGED, PROFILE_CHANGED, ACTION_CHANGED
from neuroverse.core.state import Store
from neuroverse.ui import theme as T
from neuroverse.ui.widgets import FlatButton, rescale
from neuroverse.ui.screens.dashboard import Dashboard
from neuroverse.ui.screens.time_travel import TimeTravel
from neuroverse.ui.screens.coach import Coach
from neuroverse.ui.screens.actions import Actions
from neuroverse.ui.screens.settings import Settings
from neuroverse.ui.screens.offline_card import OfflineCardScreen
from neuroverse.ui.screens.finances import Finances

SCREENS = {
    'Dashboard': Dashboard,
    'My Finances': Finances,
    'Time Travel': TimeTravel,
    'Future-Self Coach': Coach,
    'Action Plan': Actions,
    'Offline Card': OfflineCardScreen,
    'Accessibility': Settings,
}
NAV_ITEMS = {
    'Dashboard': '⌂    Home',
    'My Finances': '＋    Edit finances',
    'Time Travel': '◷    Explore future',
    'Future-Self Coach': '✦    Ai chatbot',
    'Action Plan': '✓    Small wins',
    'Offline Card': '▣    Offline card',
    'Accessibility': '⚙    Accessibility',
}
HIDDEN_IN_FOCUS_MODE = ('My Finances', 'Action Plan')


class NeuroVerse(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('NeuroVerse ✦ Financial time travel · fictional demo')
        self.geometry('1240x830')
        self.minsize(920, 640)
        self.configure(bg=T.BG)
        ttk.Style(self).configure('Page.TFrame', background=T.BG)
        self.bus = EventBus()
        self.store = Store(self.bus)

        shell = tk.Frame(self, bg=T.BG)
        shell.pack(fill='both', expand=True)
        self.sidebar = tk.Frame(shell, bg=T.NAV, width=232)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        head = tk.Frame(self.sidebar, bg=T.NAV, padx=24, pady=26)
        head.pack(fill='x')
        tk.Label(head, text='✦  neuroverse', bg=T.NAV, fg='#ffffff',
                 font=(T.FONT, 20, 'bold')).pack(anchor='w')
        tk.Label(head, text='MONEY, MADE HUMAN', bg=T.NAV, fg=T.NAV_MUTED,
                 font=(T.FONT, 9, 'bold')).pack(anchor='w', pady=(7, 0))
        tk.Frame(self.sidebar, bg=T.NAV_HOVER, height=1).pack(fill='x', padx=18, pady=(0, 17))
        tk.Label(self.sidebar, text='YOUR SPACE', bg=T.NAV, fg=T.NAV_MUTED,
                 font=(T.FONT, 9, 'bold')).pack(anchor='w', padx=27, pady=(0, 11))
        self.buttons = {}
        for name in SCREENS:
            self.buttons[name] = FlatButton(
                self.sidebar, NAV_ITEMS[name], lambda page=name: self.show(page),
                bg=T.NAV, fg=T.NAV_TEXT, hover_bg=T.NAV_HOVER, hover_fg='#ffffff',
                focus_color=T.FOCUS_ON_DARK, font=(T.FONT, 11, 'bold'),
                anchor='w', padx=16, pady=12)
        bottom = tk.Frame(self.sidebar, bg=T.NAV, padx=20, pady=22)
        bottom.pack(side='bottom', fill='x')
        tk.Label(bottom, text='●  Exploring safely', fg=T.MINT, bg=T.NAV,
                 font=(T.FONT, 10, 'bold')).pack(anchor='w')
        tk.Label(bottom, text='Fictional money · Gemini optional', fg=T.NAV_MUTED, bg=T.NAV,
                 font=(T.FONT, 9)).pack(anchor='w', pady=(4, 0))

        self.content = tk.Frame(shell, bg=T.BG)
        self.content.pack(side='left', fill='both', expand=True)
        self.screens = {name: cls(self.content, self.store, self.bus, self.show)
                        for name, cls in SCREENS.items()}
        self.current = None
        self.bus.subscribe(PREFERENCES_CHANGED, self._apply_preferences)
        # lists get rebuilt when data changes; re-apply the text size to the new widgets
        self.bus.subscribe(PROFILE_CHANGED, lambda _: self._schedule_rescale())
        self.bus.subscribe(ACTION_CHANGED, lambda _: self._schedule_rescale())
        self._apply_preferences(None)
        self.show('Dashboard')

    def _schedule_rescale(self):
        self.after_idle(lambda: rescale(self))

    def _apply_preferences(self, _):
        prefs = self.store.state.preferences
        large = prefs['large_text']
        T.TEXT_SCALE = 1.25 if large else 1.0
        self.sidebar.configure(width=282 if large else 232)

        # Focus mode hides some pages. Re-pack in the original order so nothing jumps around.
        for btn in self.buttons.values():
            btn.pack_forget()
        for name, btn in self.buttons.items():
            if prefs['focus'] and name in HIDDEN_IN_FOCUS_MODE:
                continue
            btn.pack(fill='x', padx=12, pady=3)

        for font_name in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont'):
            tkfont.nametofont(font_name).configure(size=12 if large else 10)
        self._schedule_rescale()
        if self.current:                      # redraw canvas drawings (hero, charts) at the new size
            self.screens[self.current].refresh()

    def show(self, name):
        if self.current:
            self.screens[self.current].pack_forget()
        self.current = name
        screen = self.screens[name]
        screen.pack(fill='both', expand=True)
        screen.refresh()
        for key, btn in self.buttons.items():
            if key == name:
                btn.set_colors(T.NAV_SELECTED, T.PRIMARY_DARK, T.NAV_SELECTED)
            else:
                btn.set_colors(T.NAV, T.NAV_TEXT, T.NAV_HOVER, '#ffffff')
        self._schedule_rescale()


def main():
    NeuroVerse().mainloop()

if __name__ == '__main__':
    main()
