"""Editable demo financial profile — owned by the UI team, not the card team."""
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from neuroverse.core.events import PROFILE_CHANGED
from neuroverse.services.forecast import money
from neuroverse.ui import theme as T
from neuroverse.ui.widgets import Screen, panel, label, button


def to_pence(value):
    try:
        amount = Decimal(str(value).replace('£','').replace(',','').strip())
        if not amount.is_finite() or amount.as_tuple().exponent < -2:
            raise ValueError
        return int(amount * 100)
    except (InvalidOperation, ValueError):
        raise ValueError('Enter a valid amount with up to two decimal places.')

class Finances(Screen):
    def __init__(self, parent, store, bus, navigate):
        super().__init__(parent, store, bus, navigate, 'Build your money map ✦',
                         'Edit your fictional balance, income and upcoming bills. No real account is connected.')
        top = panel(self, '✦  Practice account')
        top.pack(fill='x', pady=(0, 14))
        row = tk.Frame(top, bg=T.SURFACE)
        row.pack(fill='x')
        label(row, 'Starting balance  £', 11, True).pack(side='left')
        self.balance = tk.StringVar()
        tk.Entry(row, textvariable=self.balance, width=16, font=(T.FONT, 14), relief='solid', bd=1).pack(side='left', padx=(10, 12))
        button(row, 'Update balance', self.update_balance).pack(side='left')
        label(top, 'The starting balance represents money available today; future dated entries are applied by the forecast.',
              9, color=T.MUTED, wraplength=700, justify='left').pack(anchor='w', pady=(10,0))

        form = panel(self, '＋  Add a future income or expense')
        form.pack(fill='x', pady=(0, 14))
        fields = tk.Frame(form, bg=T.SURFACE)
        fields.pack(fill='x')
        self.description = tk.StringVar()
        self.amount = tk.StringVar()
        self.date_var = tk.StringVar(value=(date.today() + timedelta(days=5)).isoformat())
        self.kind = tk.StringVar(value='Expense')
        for col,(caption,var,width) in enumerate([('Description',self.description,22), ('Amount (£)',self.amount,12),('Date YYYY-MM-DD',self.date_var,15)]):
            group = tk.Frame(fields,bg=T.SURFACE)
            group.pack(side='left', padx=(0,12))
            label(group,caption,9,True,color=T.MUTED).pack(anchor='w')
            tk.Entry(group,textvariable=var,width=width,font=(T.FONT,11)).pack(pady=(5,0))
        ttk.Combobox(fields, textvariable=self.kind, values=['Expense','Income'], state='readonly', width=11).pack(side='left', pady=(20,0))
        button(form, 'Add to my forecast  →', self.add_item).pack(anchor='w', pady=(13,0))

        entries = panel(self, 'Upcoming items · click Remove to delete')
        entries.pack(fill='both', expand=True)
        self.list_frame = tk.Frame(entries, bg=T.SURFACE)
        self.list_frame.pack(fill='both', expand=True)
        bus.subscribe(PROFILE_CHANGED, lambda _: self.refresh())
        self.refresh()

    def update_balance(self):
        try:
            self.store.set_balance(to_pence(self.balance.get()))
        except ValueError as exc:
            messagebox.showerror('Check your balance', str(exc), parent=self)

    def add_item(self):
        try:
            value = abs(to_pence(self.amount.get()))
            if value == 0: raise ValueError('Amount must be greater than zero.')
            amount = value if self.kind.get() == 'Income' else -value
            self.store.add_transaction(self.date_var.get(), self.description.get(), amount)
            self.description.set('')
            self.amount.set('')
        except ValueError as exc:
            messagebox.showerror('Check the new item', str(exc), parent=self)

    def remove_item(self, txn_id):
        self.store.remove_transaction(txn_id)

    def refresh(self):
        s = self.store.state
        self.balance.set(f'{s.balance_pence/100:.2f}')
        for widget in self.list_frame.winfo_children(): widget.destroy()
        entries = sorted(s.transactions, key=lambda t:t.date)
        for t in entries[:9]:
            row = tk.Frame(self.list_frame,bg=T.SURFACE,pady=5)
            row.pack(fill='x')
            label(row, f'{t.date}    {t.description}',10,True).pack(side='left',fill='x',expand=True)
            if t.source != 'card':
                button(row,'Remove',lambda tx=t:self.remove_item(tx.id),secondary=True,
                       padx=10,pady=4).pack(side='right',padx=(12,0))
            label(row, money(t.amount_pence), 10, True, color=T.GOOD if t.amount_pence>0 else T.TEXT).pack(side='right')
        if len(entries)>9:
            label(self.list_frame,f'+ {len(entries)-9} more entries',9,color=T.MUTED).pack(anchor='w')
