"""User-owned actions and achievable emergency-fund planning."""
import tkinter as tk
from tkinter import messagebox
from decimal import Decimal, InvalidOperation
from neuroverse.core.events import ACTION_CHANGED, PROFILE_CHANGED
from neuroverse.services.forecast import project, money
from neuroverse.ui import theme as T
from neuroverse.ui.widgets import Screen, panel, label, button

ACTIONS=[
 ('review_bill','Review the next bill and payment date'),
 ('ask_provider','Ask the provider whether payment arrangements are possible'),
 ('support','Check independent sources for support and eligibility'),
 ('save_buffer','Choose a realistic savings step for this month'),
 ('review_subscriptions','Review optional subscriptions without affecting essentials'),
]

class Actions(Screen):
    def __init__(self,parent,store,bus,navigate):
        super().__init__(parent,store,bus,navigate,'Small steps, lasting resilience ✦',
                         'Your financial plan is a set of choices, not obligations.')
        goal=panel(self,'✦  Build a safety cushion')
        goal.pack(fill='x',pady=(0,14))
        self.goal_summary=label(goal,'',12,True)
        self.goal_summary.pack(anchor='w',pady=(0,8))
        row=tk.Frame(goal,bg=T.SURFACE)
        row.pack(fill='x')
        label(row,'Target  £',10,True).pack(side='left')
        self.target=tk.StringVar()
        tk.Entry(row,textvariable=self.target,width=12,font=(T.FONT,12)).pack(side='left',padx=8)
        button(row,'Set goal',self.save_goal).pack(side='left')
        label(goal,'Goals are examples. The app will not transfer money or set up payments.',9,color=T.MUTED).pack(anchor='w',pady=(8,0))
        content=panel(self,'✓  My one-step action plan')
        content.pack(fill='both',expand=True)
        self.vars={}
        for key,title in ACTIONS:
            var=tk.BooleanVar(value=store.state.actions.get(key,False))
            self.vars[key]=var
            tk.Checkbutton(content,text=title,variable=var,command=lambda k=key,v=var:store.update_action(k,v.get()),
                           anchor='w',bg=T.SURFACE,fg=T.TEXT,activebackground=T.SURFACE,
                           font=(T.FONT,11),selectcolor=T.PRIMARY_LIGHT,wraplength=650).pack(fill='x',anchor='w',pady=8)
        self.progress=label(content,'',11,True,color=T.PRIMARY)
        self.progress.pack(anchor='w',pady=(12,4))
        button(content,'Explore my possible futures →',lambda:navigate('Time Travel'),secondary=True).pack(anchor='w',pady=8)
        bus.subscribe(ACTION_CHANGED,lambda _:self.refresh())
        bus.subscribe(PROFILE_CHANGED,lambda _:self.refresh())
        self.refresh()

    def save_goal(self):
        try:
            x=Decimal(self.target.get().strip())
            if not x.is_finite() or x<0 or x.as_tuple().exponent < -2: raise ValueError
            self.store.set_goal(int(x*100))
        except (InvalidOperation,ValueError):
            messagebox.showerror('Check your goal','Enter a valid non-negative amount (up to 2 decimals).',parent=self)

    def refresh(self):
        state=self.store.state
        self.target.set(f'{state.savings_goal_pence/100:.2f}')
        projected=project(state.balance_pence,state.transactions)
        self.goal_summary.config(text=f"Practice goal: {money(state.savings_goal_pence)}  ·  Lowest 30-day balance: {money(projected['lowest']['balance_pence'])}")
        for key,var in self.vars.items():var.set(state.actions.get(key,False))
        count=sum(bool(state.actions.get(k)) for k,_ in ACTIONS)
        self.progress.config(text=f'{count} of {len(ACTIONS)} steps marked complete')
