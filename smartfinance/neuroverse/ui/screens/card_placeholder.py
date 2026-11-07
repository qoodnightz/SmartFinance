"""Intentionally EMPTY card module. Card teammates own the future implementation."""
import tkinter as tk
from neuroverse.ui import theme as T
from neuroverse.ui.widgets import Screen, panel, label

class CardPlaceholder(Screen):
    def __init__(self,parent,store,bus,navigate):
        super().__init__(parent,store,bus,navigate,'FutureCard · coming soon',
                         'This page is intentionally reserved for the virtual-card team.')
        card = panel(self,'▣  Virtual card integration placeholder')
        card.pack(fill='both',expand=True)
        canvas = tk.Canvas(card, height=230, bg=T.SURFACE, highlightthickness=0)
        canvas.pack(fill='x',pady=15)
        canvas.create_rectangle(100,15,540,212,fill='#6a55dc',outline='')
        canvas.create_text(130,48,text='✦  FUTURECARD',anchor='w',fill='white',font=(T.FONT,17,'bold'))
        canvas.create_text(130,164,text='TEAM INTEGRATION PENDING',anchor='w',fill='#f1eaff',font=(T.FONT,12,'bold'))
        label(card,'Your teammates can insert their own Tkinter screen later. No purchase buttons or card logic are implemented here.',
              11, color=T.MUTED,wraplength=720,justify='left').pack(anchor='w',pady=(5,12))
        label(card,'Existing integration boundary: neuroverse/integrations/card_bridge.py',
              10,True,color=T.PRIMARY).pack(anchor='w')
