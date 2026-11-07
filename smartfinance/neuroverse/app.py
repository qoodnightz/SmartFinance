"""Single-owner visual shell. No changes to card or financial contracts."""
import tkinter as tk
from tkinter import ttk
from neuroverse.core.events import EventBus, PREFERENCES_CHANGED
from neuroverse.core.state import Store
from neuroverse.ui import theme as T
from neuroverse.ui.screens.dashboard import Dashboard
from neuroverse.ui.screens.time_travel import TimeTravel
from neuroverse.ui.screens.coach import Coach
from neuroverse.ui.screens.actions import Actions
from neuroverse.ui.screens.settings import Settings
from neuroverse.ui.screens.card_placeholder import CardPlaceholder
from neuroverse.ui.screens.finances import Finances

SCREENS = {
    'Dashboard': Dashboard,
    'My Finances': Finances,
    'Time Travel': TimeTravel,
    'Future-Self Coach': Coach,
    'Action Plan': Actions,
    'Card Integration': CardPlaceholder,
    'Accessibility': Settings,
}
NAV_ITEMS = {
    'Dashboard': '⌂    My universe',
    'My Finances': '＋    Edit finances',
    'Time Travel': '◷    Explore futures',
    'Future-Self Coach': '✦    Future-self guide',
    'Action Plan': '✓    Small wins',
    'Card Integration': '▣    Virtual card',
    'Accessibility': '⚙    Accessibility',
}

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
        self.sidebar = tk.Frame(shell, bg=T.NAV, width=232,
                                highlightbackground=T.BORDER, highlightthickness=1)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        head = tk.Frame(self.sidebar, bg=T.NAV, padx=24, pady=26)
        head.pack(fill='x')
        tk.Label(head, text='✦  neuroverse', bg=T.NAV, fg=T.TEXT,
                 font=(T.FONT, 20, 'bold')).pack(anchor='w')
        tk.Label(head, text='MONEY, MADE HUMAN ✨', bg=T.NAV, fg=T.MUTED,
                 font=(T.FONT, 9, 'bold')).pack(anchor='w', pady=(7, 0))
        tk.Frame(self.sidebar, bg=T.BORDER, height=1).pack(fill='x', padx=18, pady=(0, 17))
        tk.Label(self.sidebar, text='YOUR SPACE', bg=T.NAV, fg='#a2a7b4',
                 font=(T.FONT, 9, 'bold')).pack(anchor='w', padx=27, pady=(0, 11))
        self.buttons = {}
        for name in SCREENS:
            btn = tk.Button(self.sidebar, text=NAV_ITEMS[name], anchor='w',
                            font=(T.FONT, 11, 'bold'), bd=0, relief='flat',
                            highlightthickness=0, padx=18, pady=14,
                            bg=T.NAV, fg=T.MUTED, cursor='hand2',
                            activebackground=T.NAV_SELECTED,
                            activeforeground=T.PRIMARY,
                            command=lambda page=name: self.show(page))
            btn.pack(fill='x', padx=12, pady=3)
            btn.bind('<Enter>', lambda e, b=btn, n=name: b.config(bg=T.NAV_SELECTED))
            btn.bind('<Leave>', lambda e, b=btn, n=name: b.config(bg=T.NAV_SELECTED if self.current == n else T.NAV))
            self.buttons[name] = btn
        bottom = tk.Frame(self.sidebar, bg=T.NAV, padx=20, pady=22)
        bottom.pack(side='bottom', fill='x')
        tk.Label(bottom, text='●  Exploring safely', fg=T.GOOD, bg=T.NAV,
                 font=(T.FONT, 10, 'bold')).pack(anchor='w')
        tk.Label(bottom, text='Fictional money · Gemini optional', fg=T.MUTED, bg=T.NAV,
                 font=(T.FONT, 9)).pack(anchor='w', pady=(4, 0))

        self.content = tk.Frame(shell, bg=T.BG)
        self.content.pack(side='left', fill='both', expand=True)
        self.screens = {name: cls(self.content, self.store, self.bus, self.show)
                        for name, cls in SCREENS.items()}
        self.current = None
        self.bus.subscribe(PREFERENCES_CHANGED, self._apply_preferences)
        self._apply_preferences(None)
        self.show('Dashboard')

    def _apply_preferences(self, _):
        focus = self.store.state.preferences['focus']
        for name, btn in self.buttons.items():
            if focus and name in ('My Finances', 'Action Plan'):
                btn.pack_forget()
            elif not btn.winfo_manager():
                btn.pack(fill='x', padx=12, pady=3)
        import tkinter.font as tkfont
        tkfont.nametofont('TkDefaultFont').configure(
            size=12 if self.store.state.preferences['large_text'] else 10)

    def show(self, name):
        if self.current:
            self.screens[self.current].pack_forget()
        self.current = name
        screen = self.screens[name]
        screen.pack(fill='both', expand=True)
        screen.refresh()
        for key, btn in self.buttons.items():
            btn.configure(bg=T.NAV_SELECTED if key == name else T.NAV,
                          fg=T.PRIMARY if key == name else T.MUTED)


def main():
    NeuroVerse().mainloop()

if __name__ == '__main__':
    main()
