"""Vibrant dashboard; never reaches into the virtual-card module."""
import math
import tkinter as tk
from datetime import date
from neuroverse.core.events import PROFILE_CHANGED, PREFERENCES_CHANGED
from neuroverse.services.forecast import project, money
from neuroverse.ui import theme as T
from neuroverse.ui.widgets import Screen, panel, label, button, gradient


class Dashboard(Screen):
    def __init__(self, parent, store, bus, navigate):
        super().__init__(parent, store, bus, navigate, 'Make your money make sense',
                         'A little clarity today, more possibilities tomorrow.')
        self.animation_phase = 0
        self._animation_job = None
        self.hero = tk.Canvas(self, height=194, bg=T.HERO_BOTTOM, highlightthickness=0, bd=0)
        self.hero.pack(fill='x', pady=(0, 14))
        self.hero.bind('<Configure>', lambda _: self._draw_hero())
        self.hero.bind('<Map>', lambda _: self._start_hero_animation())
        self.hero.bind('<Unmap>', lambda _: self._stop_hero_animation())

        actions = tk.Frame(self, bg=T.BG)
        actions.pack(fill='x', pady=(0, 14))
        for i, (title, detail, page, sym, color, tint) in enumerate([
            ('Time travel', 'Explore futures', 'Time Travel', '◷', T.PRIMARY, '#ebe3f3'),
            ('Offline card', 'Spend without signal', 'Offline Card', '▣', T.TEAL, '#d9f1ef'),
            ('AI guide', 'Ask anything', 'Future-Self Coach', '✦', '#a0125f', '#fde4ee'),
            ('My steps', 'Small wins', 'Action Plan', '✓', '#8a5a00', '#fff2d1'),
        ]):
            tile = tk.Frame(actions, bg=T.SURFACE, highlightbackground=T.BORDER,
                            highlightthickness=1, padx=13, pady=10, cursor='hand2')
            tile.pack(side='left', expand=True, fill='both', padx=(0, 0 if i == 3 else 10))
            mark = tk.Label(tile, text=sym, bg=tint, fg=color,
                            font=(T.FONT, 19, 'bold'), width=3, pady=5)
            mark.pack(anchor='w')
            title_label = label(tile, title, 11, True)
            title_label.pack(anchor='w', pady=(7, 0))
            detail_label = label(tile, detail, 9, color=T.MUTED)
            detail_label.pack(anchor='w', pady=(3, 0))
            for widget in (tile, mark, title_label, detail_label):
                widget.bind('<Button-1>', lambda e, page=page: navigate(page))
                widget.bind('<Enter>', lambda e, t=tile: t.configure(highlightbackground=T.PRIMARY))
                widget.bind('<Leave>', lambda e, t=tile: t.configure(highlightbackground=T.BORDER))

        self.alert = tk.Frame(self, bg='#e6f6f2', padx=16, pady=11)
        self.alert.pack(fill='x', pady=(0, 13))
        self.alert_heading = label(self.alert, '', 11, True, bg='#e6f6f2', color='#00604d')
        self.alert_heading.pack(anchor='w')
        self.alert_detail = label(self.alert, '', 10, bg='#e6f6f2', color='#00604d',
                                  justify='left', wraplength=665)
        self.alert_detail.pack(anchor='w', pady=(4, 0))

        body = tk.Frame(self, bg=T.BG)
        body.pack(fill='both', expand=True)
        activity = panel(body, '↗  Your money moments')
        activity.pack(side='left', fill='both', expand=True, padx=(0, 12))
        self.events = tk.Frame(activity, bg=T.SURFACE)
        self.events.pack(fill='both', expand=True)

        insight = panel(body, '✧  Your future pulse')
        insight.configure(width=260)
        insight.pack(side='left', fill='both')
        insight.pack_propagate(False)
        label(insight, 'LOWEST BALANCE · 30 DAYS', 9, True, color=T.MUTED).pack(anchor='w', pady=(6, 2))
        self.low_balance = label(insight, '', 23, True)
        self.low_balance.pack(anchor='w', pady=(0, 8))
        self.spark = tk.Canvas(insight, height=83, bg=T.SURFACE, highlightthickness=0)
        self.spark.pack(fill='x', pady=(0, 7))
        self.spark.bind('<Configure>', lambda _: self._draw_sparkline())
        label(insight, 'A snapshot based on the bills and income in your practice account.',
              9, color=T.MUTED, wraplength=210, justify='left').pack(anchor='w', pady=(0, 9))
        button(insight, 'See my futures  →', lambda: navigate('Time Travel'), secondary=True).pack(fill='x')
        bus.subscribe(PROFILE_CHANGED, lambda _: self.refresh())
        bus.subscribe(PREFERENCES_CHANGED, lambda _: self._start_hero_animation())
        self.refresh()

    def _start_hero_animation(self):
        self._stop_hero_animation()
        self._draw_hero()
        if not self.store.state.preferences['reduced_motion'] and self.hero.winfo_ismapped():
            self._animation_job = self.after(65, self._tick)

    def _stop_hero_animation(self):
        if self._animation_job is not None:
            self.after_cancel(self._animation_job)
            self._animation_job = None

    def _tick(self):
        self._animation_job = None
        if not self.hero.winfo_ismapped() or self.store.state.preferences['reduced_motion']:
            return
        self.animation_phase += .10
        self._draw_hero()
        self._animation_job = self.after(65, self._tick)

    def _draw_hero(self):
        c = self.hero
        if not c.winfo_exists():
            return
        c.delete('all')
        w, h = max(440, c.winfo_width()), 194
        gradient(c, w, h, T.HERO_TOP, T.HERO_END, stripes=85)
        shift = math.sin(self.animation_phase) * 14
        c.create_oval(w*.57, -140+shift, w+130, 165+shift, fill='#7a3b9e', outline='')
        c.create_oval(w*.81, -115-shift*.7, w+220, 230-shift*.7, fill='#42145f', outline='')
        c.create_oval(w*.67, 124, w*.73, 178, fill=T.YELLOW, outline='')
        c.create_oval(w*.72, 142, w*.75, 170, fill=T.MINT, outline='')
        c.create_text(30, 25, anchor='nw', text='YOUR PRACTICE BALANCE',
                      fill='#f6efff', font=T.font(10, 'bold'))
        c.create_text(30, 56, anchor='nw', text=money(self.store.state.balance_pence),
                      fill='white', font=T.font(36, 'bold'))
        c.create_text(32, 125, anchor='nw', text='Little steps, brighter futures',
                      fill='white', font=T.font(11, 'bold'))
        c.create_text(31, 171, anchor='sw', text='●  PRACTICE MODE · NO REAL MONEY',
                      fill='#f9eaff', font=T.font(9, 'bold'))
        c.create_text(w-25, 171, anchor='se', text='NEUROVERSE  ✦',
                      fill='white', font=T.font(10, 'bold'))

    def _draw_sparkline(self):
        if not hasattr(self, '_forecast'):
            return
        c = self.spark
        c.delete('all')
        pts = [p['balance_pence'] for p in self._forecast['timeline']]
        if len(pts) < 2:
            return
        w, h = max(120, c.winfo_width()), 83
        top, bottom = max(pts), min(pts)
        span = max(1, top-bottom)
        coords=[]
        for i, v in enumerate(pts):
            coords.extend((5+(w-10)*i/(len(pts)-1), 8+(h-20)*(top-v)/span))
        c.create_line(*coords, fill=T.PINK if min(pts)<0 else T.PRIMARY, width=3, smooth=True)
        c.create_oval(coords[-2]-4, coords[-1]-4, coords[-2]+4, coords[-1]+4,
                      fill=T.PINK, outline='white', width=2)

    def refresh(self):
        s = self.store.state
        self._forecast = project(s.balance_pence, s.transactions)
        self._draw_hero()
        self._draw_sparkline()
        low = self._forecast['lowest']['balance_pence']
        self.low_balance.config(text=money(low), fg=T.DANGER if low < 0 else T.TEXT)
        if self._forecast['shortfall']:
            bg, fg = '#fde4ee', '#8c0f4a'
            title = '✦  Heads up — a future balance dip'
            detail = f"Under these assumptions, your balance could go below £0 on {self._forecast['shortfall']['date']}. You can explore alternatives."
        else:
            bg, fg = '#e6f6f2', '#00604d'
            title = '✦  Your next 30 days look steady'
            detail = 'Your known scheduled payments do not produce a negative balance in the current practice forecast.'
        self.alert.configure(bg=bg)
        self.alert_heading.config(bg=bg, fg=fg, text=title)
        self.alert_detail.config(bg=bg, fg=fg, text=detail)
        for child in self.events.winfo_children():
            child.destroy()
        ordered = sorted(s.transactions, key=lambda x: x.date, reverse=True)
        colors = [('#ebe3f3', '#5a287d'), ('#dff4ef', '#00775f'), ('#fde4ee', '#b3123b'), ('#fff2d1', '#8a5a00')]
        for i, txn in enumerate(ordered[:5]):
            bg, fg = colors[i % len(colors)]
            row = tk.Frame(self.events, bg=T.SURFACE)
            row.pack(fill='x', pady=7)
            mark = '↓' if txn.amount_pence > 0 else ('▣' if txn.source == 'card' else '↑')
            tk.Label(row, text=mark, bg=bg, fg=fg, font=(T.FONT, 16, 'bold'), width=3, pady=5).pack(side='left', padx=(0, 11))
            meta = tk.Frame(row, bg=T.SURFACE)
            meta.pack(side='left', fill='x', expand=True)
            label(meta, txn.description, 10, True).pack(anchor='w')
            label(meta, f'{txn.date} · {"Practice card" if txn.source == "card" else "Scheduled"}',
                  9, color=T.MUTED).pack(anchor='w', pady=(2, 0))
            label(row, money(txn.amount_pence), 11, True,
                  color=T.GOOD if txn.amount_pence > 0 else T.TEXT).pack(side='right')
