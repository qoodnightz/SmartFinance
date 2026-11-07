"""Offline card screen (bank-app style).

Top: the customer's real card and balance.
Below: their offline cards, plus a button to create a new one by moving money
from the real card, choosing a name and a 4-digit PIN.

The file keeps its old name and the old class name (CardPlaceholder is an alias)
so app.py does not need to change its import.
"""
import tkinter as tk

from neuroverse.ui import theme as T
from neuroverse.ui.widgets import Screen, panel, label
from neuroverse.integrations.offline_card import state
from neuroverse.integrations.offline_card.chip import (
    MAX_ALLOWANCE, MAX_OFFLINE_PAYMENTS, PER_TXN_LIMIT, fmt,
)

TEAL = "#86f5e1"
INK = "#14211f"
PURPLE = "#6a55dc"
SOFT_PURPLE = "#f1eaff"
RED = "#c0392b"
GREEN = "#1f8a70"


def _round_rect(c, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def draw_card(parent, brand, line_left, line_right, fill, ink, width=340, height=190):
    """A bank-card graphic: brand, chip, contactless symbol and two text lines."""
    c = tk.Canvas(parent, width=width, height=height, bg=T.SURFACE, highlightthickness=0)
    _round_rect(c, 4, 4, width - 4, height - 4, 22, fill=fill, outline="")
    c.create_text(26, 34, text=brand, anchor="w", fill=ink, font=(T.FONT, 17, "bold"))
    _round_rect(c, 26, 68, 70, 100, 6, fill="#e3b866", outline="")
    c.create_text(88, 84, text="))))", anchor="w", fill=ink, font=(T.FONT, 14, "bold"))
    c.create_text(26, height - 30, text=line_left, anchor="w", fill=ink, font=(T.FONT, 12, "bold"))
    c.create_text(width - 26, height - 30, text=line_right, anchor="e", fill=ink, font=(T.FONT, 12, "bold"))
    return c


def pill(parent, text, command, bg=TEAL, fg=INK):
    """A rounded-looking button. (Plain tk.Button ignores colours on macOS, so this is a Label.)"""
    b = tk.Label(parent, text=text, bg=bg, fg=fg, font=(T.FONT, 12, "bold"),
                 padx=22, pady=10, cursor="hand2")
    b.bind("<Button-1>", lambda _e: command())
    return b


class OfflineCardScreen(Screen):
    def __init__(self, parent, store, bus, navigate):
        super().__init__(parent, store, bus, navigate, "Offline card",
                         "Your card keeps working in shops even if the network goes down.")
        outer = panel(self, "▣  Your cards")
        outer.pack(fill="both", expand=True)
        self.body = tk.Frame(outer, bg=T.SURFACE)
        self.body.pack(fill="both", expand=True, padx=6, pady=6)
        self._notice = None          # (text, colour) shown once on the home view
        self.show_home()

    # ---------- helpers ----------
    def _clear(self):
        for w in self.body.winfo_children():
            w.destroy()

    def _pin_validator(self):
        return (self.register(lambda s: s == "" or (s.isdigit() and len(s) <= 4)), "%P")

    def _field(self, text, show=None, validate=None):
        tk.Label(self.body, text=text, bg=T.SURFACE, fg=T.MUTED,
                 font=(T.FONT, 11)).pack(anchor="w", pady=(10, 2))
        kw = {"show": show} if show else {}
        if validate:
            kw.update(validate="key", validatecommand=validate)
        e = tk.Entry(self.body, font=(T.FONT, 13), width=28, **kw)
        e.pack(anchor="w")
        return e

    # ---------- home: real card + offline cards ----------
    def show_home(self):
        self._clear()
        acct = state.account

        draw_card(self.body, "NEUROVERSE", acct.owner, "debit", TEAL, INK).pack(anchor="w", pady=(4, 8))
        label(self.body, f"Real card balance   {fmt(acct.balance)}", 14, True).pack(anchor="w")
        label(self.body, f"Reserved for offline cards   {fmt(acct.escrow)}", 11,
              color=T.MUTED).pack(anchor="w", pady=(2, 14))

        if self._notice:
            text, colour = self._notice
            tk.Label(self.body, text=text, bg=T.SURFACE, fg=colour, font=(T.FONT, 11, "bold"),
                     wraplength=620, justify="left").pack(anchor="w", pady=(0, 10))
            self._notice = None

        label(self.body, "Offline cards", 14, True).pack(anchor="w", pady=(4, 6))
        if not state.cards:
            label(self.body, "No offline cards yet. Create one to keep some money spendable "
                             "in shops if the network ever goes down.",
                  11, color=T.MUTED, wraplength=620, justify="left").pack(anchor="w", pady=(0, 10))

        for card in state.cards:
            row = tk.Frame(self.body, bg=T.SURFACE)
            row.pack(anchor="w", pady=4)
            draw_card(row, "OFFLINE", card.name, f"•••• {card.card_id[-4:]}", PURPLE, "white",
                      width=210, height=120).pack(side="left")
            info = tk.Frame(row, bg=T.SURFACE)
            info.pack(side="left", padx=14)
            label(info, f"{fmt(card.allowance)} allowance", 13, True).pack(anchor="w")
            label(info, f"{card.offline_payments_left} of {MAX_OFFLINE_PAYMENTS} offline payments · "
                        f"{fmt(PER_TXN_LIMIT)} per payment", 10, color=T.MUTED).pack(anchor="w")
            if card.closed:
                label(info, "Closed", 10, True, color=T.MUTED).pack(anchor="w")
            elif card.locked:
                label(info, "Locked after 3 wrong PINs", 10, True, color=RED).pack(anchor="w")

        pill(self.body, "＋  Create offline card", self.show_create).pack(anchor="w", pady=(14, 4))

    # ---------- create offline card ----------
    def show_create(self):
        self._clear()
        label(self.body, "Create offline card", 16, True).pack(anchor="w", pady=(4, 2))
        label(self.body,
              f"Money moves from your real card ({fmt(state.account.balance)} available) into a safe "
              f"reserve. Max {fmt(MAX_ALLOWANCE)} per offline card. Unused money comes back afterwards.",
              11, color=T.MUTED, wraplength=620, justify="left").pack(anchor="w")

        vcmd = self._pin_validator()
        name = self._field("Card name (e.g. Emergency food)")
        amount = self._field("Amount to move (£)")
        pin = self._field("Choose a 4-digit PIN", show="•", validate=vcmd)
        pin2 = self._field("Confirm PIN", show="•", validate=vcmd)

        error = tk.Label(self.body, text="", bg=T.SURFACE, fg=RED, font=(T.FONT, 11, "bold"),
                         wraplength=620, justify="left")
        error.pack(anchor="w", pady=(10, 0))

        def submit():
            try:
                amount_pounds = float(amount.get() or 0)
                card = state.bank.issue_card(state.account, name.get(), amount_pounds,
                                             pin.get(), pin2.get(), source="customer")
            except ValueError as e:
                msg = str(e)
                if "could not convert" in msg:      # float() failed on the amount box
                    msg = "Enter the amount as a number, e.g. 20 or 20.50."
                error.config(text=msg)
                return
            state.cards.append(card)
            self._notice = (f"Offline card '{card.name}' created with {fmt(card.allowance)}.", GREEN)
            self.show_home()

        btns = tk.Frame(self.body, bg=T.SURFACE)
        btns.pack(anchor="w", pady=14)
        pill(btns, "Move money", submit).pack(side="left")
        pill(btns, "Cancel", self.show_home, bg="#e9e9f0", fg=INK).pack(side="left", padx=10)


# Old name, so app.py's existing import and navigation entry keep working.
CardPlaceholder = OfflineCardScreen