"""Interactive scenario explorer with accessible chart alternatives."""
import tkinter as tk
from neuroverse.core.events import PROFILE_CHANGED
from neuroverse.services.forecast import project, money, SCENARIO_LABELS
from neuroverse.ui import theme as T
from neuroverse.ui.widgets import Screen, panel, label, button


class TimeTravel(Screen):
    def __init__(self, parent, store, bus, navigate):
        super().__init__(parent, store, bus, navigate, 'Your future, in color ✨',
                         'Try different paths. These are examples, not guaranteed outcomes.')
        label(self, 'CHOOSE YOUR TIMELINE', 9, True, bg=T.BG, color=T.MUTED).pack(anchor='w', pady=(0, 7))
        choices = tk.Frame(self, bg=T.BG)
        choices.pack(fill='x', pady=(0, 12))
        self.selection = tk.StringVar(value='baseline')
        self.choice_buttons = {}
        for i, (key, title) in enumerate(SCENARIO_LABELS.items()):
            icon, subtitle, tint, fg = [
                ('↗', 'Your current plan', '#ebe3f3', T.PRIMARY),
                ('⚡', 'A surprise cost', '#fde4ee', '#a0125f'),
                ('◷', 'Change payment timing', '#dff4ef', '#00775f')
            ][i]
            item = tk.Frame(choices, bg=T.SURFACE, highlightthickness=2,
                            highlightbackground=T.BORDER, padx=12, pady=10, cursor='hand2')
            item.pack(side='left', fill='both', expand=True, padx=(0, 10 if i < 2 else 0))
            icon_label = tk.Label(item, text=icon, bg=tint, fg=fg, width=3,
                                  font=(T.FONT, 20, 'bold'))
            icon_label.pack(anchor='w')
            name_label = label(item, title, 10, True, wraplength=180, justify='left')
            name_label.pack(anchor='w', pady=(6, 0))
            tip = label(item, subtitle, 9, color=T.MUTED)
            tip.pack(anchor='w', pady=(3, 0))
            for widget in (item, icon_label, name_label, tip):
                widget.bind('<Button-1>', lambda e, k=key: self.choose(k))
            self.choice_buttons[key] = item

        forecast_panel = panel(self, '✦  The next 30 days')
        forecast_panel.pack(fill='both', expand=True)
        self.result = label(forecast_panel, '', 15, True)
        self.result.pack(anchor='w', pady=(0, 3))
        self.inspect = label(forecast_panel, 'Move your pointer over the line to explore dates.',
                             10, color=T.MUTED)
        self.inspect.pack(anchor='w', pady=(0, 8))
        self.graph = tk.Canvas(forecast_panel, height=250, bg=T.SURFACE, highlightthickness=0)
        self.graph.pack(fill='both', expand=True)
        self.graph.bind('<Configure>', lambda _: self._draw())
        self.graph.bind('<Motion>', self._hover_graph)
        self.graph.bind('<Leave>', lambda _: self._draw())
        self.baseline = label(forecast_panel, '', 10, color=T.MUTED, wraplength=690, justify='left')
        self.baseline.pack(anchor='w', pady=(9, 0))
        button(self, 'Talk to my future-self guide →',
               lambda: navigate('Future-Self Coach')).pack(anchor='w', pady=(12, 0))
        bus.subscribe(PROFILE_CHANGED, lambda _: self.refresh())
        self._forecast = None
        self._hover_index = None
        self.refresh()

    def choose(self, key):
        self.selection.set(key)
        self._hover_index = None
        self.refresh()

    def refresh(self):
        s = self.store.state
        s.selected_scenario = self.selection.get()
        self._forecast = project(s.balance_pence, s.transactions, scenario=self.selection.get())
        base = project(s.balance_pence, s.transactions)
        low = self._forecast['lowest']
        self.result.config(text=f"Lowest balance: {money(low['balance_pence'])} · {low['date']}",
                           fg=T.DANGER if low['balance_pence'] < 0 else T.PRIMARY)
        self.baseline.config(text=f"Baseline low: {money(base['lowest']['balance_pence'])}. "
                                  'These are fictional projections based on known payments; a different payment date requires provider agreement.')
        for key, widget in self.choice_buttons.items():
            widget.config(highlightbackground=T.PRIMARY if key == self.selection.get() else T.BORDER)
        self._draw()

    def _chart_xy(self):
        c = self.graph
        w, h = max(c.winfo_width(), 310), max(c.winfo_height(), 190)
        points = self._forecast['timeline']
        values = [p['balance_pence'] for p in points] + [0]
        lo, hi = min(values), max(values)
        pad = max(1500, (hi-lo)*0.14)
        lo, hi = lo-pad, hi+pad
        left, right, top, bottom = 65, 18, 13, 39
        def x(i): return left+i*(w-left-right)/(len(points)-1)
        def y(value): return top+(hi-value)*(h-top-bottom)/(hi-lo)
        return w, h, points, x, y, hi, lo

    def _draw(self):
        if self._forecast is None:
            return
        c = self.graph
        c.delete('all')
        w, h, points, x, y, hi, lo = self._chart_xy()
        for ratio in (0, .25, .5, .75, 1):
            val = lo+(hi-lo)*ratio
            yp = y(val)
            c.create_line(65, yp, w-18, yp, fill='#e8e0f0', dash=(3,4))
        zero = y(0)
        c.create_line(65, zero, w-18, zero, fill='#e58aae', dash=(5,4), width=1)
        c.create_text(9, zero, text='£0', anchor='w', fill=T.DANGER, font=T.font(9, 'bold'))
        coords=[]
        for i, point in enumerate(points):
            coords.extend([x(i),y(point['balance_pence'])])
        c.create_polygon(65, h-39, *coords, x(len(points)-1), h-39,
                         fill='#ebe3f3', outline='')
        line_color = T.PINK if self.selection.get() == 'emergency' else (T.GOOD if self.selection.get() == 'bill_shift' else T.PRIMARY)
        c.create_line(*coords, fill=line_color, width=4, smooth=True)
        for index in (0, 10, 20, 30):
            c.create_text(x(index), h-15, text=f'Day {index}', fill=T.MUTED, font=T.font(9))
        if self._hover_index is not None:
            p = points[self._hover_index]
            xp, yp = x(self._hover_index), y(p['balance_pence'])
            c.create_line(xp, 11, xp, h-39, fill='#a98bc7', dash=(3, 3))
            c.create_oval(xp-6,yp-6,xp+6,yp+6,fill=line_color,outline='white',width=2)
            self.inspect.config(text=f"Day {self._hover_index} · {p['date']} · {money(p['balance_pence'])}")
        else:
            self.inspect.config(text='Move your pointer over the line to explore dates and balances.')

    def _hover_graph(self, event):
        if not self._forecast:
            return
        w, h, pts, x, y, hi, lo = self._chart_xy()
        index = round((event.x-65)/(w-65-18)*(len(pts)-1))
        index = max(0,min(len(pts)-1,index))
        if index != self._hover_index:
            self._hover_index=index
            self._draw()
