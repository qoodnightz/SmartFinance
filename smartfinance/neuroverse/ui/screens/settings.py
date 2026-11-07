"""Accessible settings and explicit local demo reset."""
import tkinter as tk
from tkinter import messagebox
from neuroverse.core.events import PREFERENCES_CHANGED
from neuroverse.ui import theme as T
from neuroverse.ui.widgets import Screen, panel, label, button

SETTINGS=[
 ('simple','Plain-language explanations'),
 ('focus','Focus mode (simplify navigation)'),
 ('large_text','Larger default interface text'),
 ('reduced_motion','Reduce decorative animations'),
]

class Settings(Screen):
    def __init__(self,parent,store,bus,navigate):
        super().__init__(parent,store,bus,navigate,'Make NeuroVerse yours ✦',
                         'Choose what helps you. You never have to disclose a diagnosis.')
        content=panel(self,'✦  Accessibility preferences')
        content.pack(fill='x',pady=(0,14))
        self.vars={}
        for key,title in SETTINGS:
            var=tk.BooleanVar(value=store.state.preferences[key]);self.vars[key]=var
            tk.Checkbutton(content,text=title,variable=var,
                           command=lambda k=key,v=var:store.update_preference(k,v.get()),
                           anchor='w',bg=T.SURFACE,fg=T.TEXT,activebackground=T.SURFACE,
                           font=(T.FONT,11),selectcolor=T.PRIMARY_LIGHT).pack(fill='x',pady=10)
        label(content,'All numeric information remains available as text. Effects are optional. Standard Tkinter accessibility varies by operating system.',
              10,color=T.MUTED,wraplength=650,justify='left').pack(anchor='w',pady=(15,0))
        privacy=panel(self,'◎  Demo privacy and controls')
        privacy.pack(fill='x')
        label(privacy,'Fictional financial data and settings are stored locally in ~/.neuroverse_ai/demo_state.json. '
              'Gemini is optional; when enabled, only the demo financial context and the question are sent to Google.',
              10,color=T.MUTED,wraplength=680,justify='left').pack(anchor='w',pady=(0,14))
        button(privacy,'Reset demo finances and preferences',self.reset,secondary=True).pack(anchor='w')
        bus.subscribe(PREFERENCES_CHANGED,lambda _:self.refresh())

    def reset(self):
        if messagebox.askyesno('Reset NeuroVerse?','Replace all saved fictional transactions, actions and preferences with the initial demo?',parent=self):
            self.store.reset_demo()
            self.refresh()

    def refresh(self):
        for k,var in self.vars.items():var.set(self.store.state.preferences[k])
