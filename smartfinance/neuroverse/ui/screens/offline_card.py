"""Offline card screen.

Top: the customer's real card and balances (the same total Home shows).
Below: their offline cards, each with a Delete button that returns the money,
and a Create offline card form (name, amount, 4-digit PIN). There is no maximum amount.
"""
import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import messagebox

from neuroverse.core.events import PROFILE_CHANGED
from neuroverse.integrations.offline_card import state
from neuroverse.integrations.offline_card.chip import MAX_OFFLINE_PAYMENTS, PER_TXN_LIMIT, fmt
from neuroverse.ui import theme as T
from neuroverse.ui.widgets import Screen, panel, label, button, rescale, interpolate

NOTICE_STYLES = {'good': ('#e6f6f2', '#00604d'), 'info': (T.PRIMARY_LIGHT, T.PRIMARY_DARK)}


def parse_amount(text) -> int:
    """'20', '20.5', '£1,250.00' -> pence. Raises ValueError with a friendly message."""
    try:
        value = Decimal(str(text).replace('£', '').replace(',', '').strip())
        if not value.is_finite():
            raise ValueError
    except (InvalidOperation, ValueError):
        raise ValueError("Enter the amount as a number, for example 20 or 20.50.")
    if value.as_tuple().exponent < -2:
        raise ValueError("Use at most 2 decimal places (pence).")
    return int(value * 100)


def _round_rect(c, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def draw_card(parent, brand, line_left, line_right, fill, accent, width=300, height=170):
    """A bank-card graphic. The figures are shown as text next to it, so nothing depends on this picture."""
    c = tk.Canvas(parent, width=width, height=height, bg=T.SURFACE, highlightthickness=0)
    _round_rect(c, 3, 3, width - 3, height - 3, 20, fill=fill, outline="")
    c.create_oval(width - 112, height - 84, width - 58, height - 30, fill=accent, outline="")
    c.create_oval(width - 82, height - 84, width - 28, height - 30,
                  fill=interpolate(fill, "#ffffff", .4), outline="")
    c.create_text(24, 30, text=brand, anchor="w", fill="#ffffff", font=(T.FONT, 15, "bold"))
    _round_rect(c, 24, 58, 62, 86, 5, fill="#e8c36a", outline="")
    c.create_text(76, 72, text="))))", anchor="w", fill="#ffffff", font=(T.FONT, 13, "bold"))
    c.create_text(24, height - 26, text=line_left, anchor="w", fill="#ffffff", font=(T.FONT, 11, "bold"))
    c.create_text(width - 24, 30, text=line_right, anchor="e", fill="#ffffff", font=(T.FONT, 11, "bold"))
    return c


class OfflineCardScreen(Screen):
    def __init__(self, parent, store, bus, navigate):
        super().__init__(parent, store, bus, navigate, "Offline card",
                         "Keep some of your money spendable in shops, even if the network goes down.")
        state.bind_store(store)                     # real card = the same balance Home shows
        self.mode = "home"
        self._notice = None                         # (text, style) shown once on the home view
        self.body = tk.Frame(self, bg=T.BG)
        self.body.pack(fill="both", expand=True)
        bus.subscribe(PROFILE_CHANGED, lambda _: self._on_profile_changed())
        self.show_home()

    # ---------- helpers ----------
    def _clear(self):
        for w in self.body.winfo_children():
            w.destroy()

    def _finish(self):
        self.after_idle(lambda: rescale(self))      # apply the larger-text preference to new widgets

    def _on_profile_changed(self):
        if self.mode == "home":
            self.show_home()

    def refresh(self):
        if self.mode == "home":
            self.show_home()

    # ---------- home ----------
    def show_home(self):
        self.mode = "home"
        self._clear()
        acct = state.account

        if self._notice:
            text, style = self._notice
            bg, fg = NOTICE_STYLES[style]
            banner = tk.Frame(self.body, bg=bg, padx=16, pady=11)
            banner.pack(fill="x", pady=(0, 12))
            label(banner, text, 11, True, bg=bg, color=fg, wraplength=760, justify="left").pack(anchor="w")
            self._notice = None

        # real card + balances
        top = panel(self.body)
        top.pack(fill="x", pady=(0, 14))
        row = tk.Frame(top, bg=T.SURFACE)
        row.pack(fill="x")
        draw_card(row, "NEUROVERSE", acct.owner, "debit", T.PRIMARY_DARK, T.PINK).pack(side="left", padx=(0, 26))
        stats = tk.Frame(row, bg=T.SURFACE)
        stats.pack(side="left", fill="x", expand=True)
        label(stats, "YOUR REAL CARD · AVAILABLE", 9, True, color=T.MUTED).pack(anchor="w")
        label(stats, fmt(acct.balance), 30, True, color=T.PRIMARY_DARK).pack(anchor="w", pady=(2, 8))
        label(stats, f"On offline cards:  {fmt(acct.escrow)}", 12, True).pack(anchor="w")
        label(stats, f"Total balance:  {fmt(acct.total)}  (the same total as on Home)", 10,
              color=T.MUTED).pack(anchor="w", pady=(4, 0))

        # offline cards
        cards_panel = panel(self.body, "Your offline cards")
        cards_panel.pack(fill="both", expand=True)
        if not state.cards:
            label(cards_panel, "You have no offline cards yet. Create one to keep some money spendable "
                               "in shops if the network ever goes down. Delete it at any time to move "
                               "the money back to your real card.",
                  11, color=T.MUTED, wraplength=760, justify="left").pack(anchor="w", pady=(0, 12))

        grid = tk.Frame(cards_panel, bg=T.SURFACE)
        grid.pack(anchor="w")
        for i, card in enumerate(state.cards):
            cell = tk.Frame(grid, bg=T.SURFACE, padx=4, pady=8)
            cell.grid(row=i // 2, column=i % 2, sticky="nw", padx=(0, 22))
            draw_card(cell, "OFFLINE", card.name, f"•••• {card.card_id[-4:]}", T.TEAL, T.YELLOW,
                      width=280, height=160).pack(anchor="w")
            label(cell, f"{fmt(card.allowance)} on this card", 14, True, color=T.PRIMARY_DARK).pack(anchor="w", pady=(8, 0))
            label(cell, f"{card.offline_payments_left} of {MAX_OFFLINE_PAYMENTS} offline payments left · "
                        f"{fmt(PER_TXN_LIMIT)} per payment", 9, color=T.MUTED,
                  wraplength=270, justify="left").pack(anchor="w", pady=(2, 0))
            if card.locked:
                label(cell, "Locked after 3 wrong PINs", 10, True, color=T.DANGER).pack(anchor="w")
            button(cell, "Delete card", lambda c=card: self.delete_card(c),
                   danger=True, padx=14, pady=7).pack(anchor="w", pady=(8, 0))

        button(cards_panel, "＋  Create offline card", self.show_create).pack(anchor="w", pady=(14, 0))
        self._finish()

    # ---------- delete ----------
    def delete_card(self, card):
        amount = state.bank.escrow_for(card.card_id)
        if not messagebox.askyesno(
                "Delete offline card?",
                f"Delete '{card.name}'?\n\n{fmt(amount)} will go back to your real card.",
                parent=self):
            return
        returned = state.bank.release_unused(state.account, card)
        state.cards.remove(card)
        self._notice = (f"'{card.name}' was deleted. {fmt(returned)} is back on your real card.", "good")
        self.show_home()

    # ---------- create ----------
    def _field(self, parent, caption, show=None, validate=None, width=26):
        box = tk.Frame(parent, bg=T.SURFACE)
        box.pack(anchor="w", pady=(10, 0))
        label(box, caption, 10, True, color=T.MUTED).pack(anchor="w")
        kw = {"show": show} if show else {}
        if validate:
            kw.update(validate="key", validatecommand=validate)
        entry = tk.Entry(box, font=(T.FONT, 13), width=width, relief="solid", bd=1,
                         highlightthickness=2, highlightbackground=T.BORDER,
                         highlightcolor=T.PRIMARY, **kw)
        entry.pack(side="left", pady=(4, 0), ipady=5)
        return box, entry

    def show_create(self):
        self.mode = "create"
        self._clear()
        acct = state.account

        form = panel(self.body, "Create offline card")
        form.pack(fill="x")
        label(form, f"Money moves from your real card ({fmt(acct.balance)} available) into this card. "
                    "There is no maximum. Delete the card whenever you like and the unused money comes back.",
              11, color=T.MUTED, wraplength=760, justify="left").pack(anchor="w")

        pin_check = (self.register(lambda s: s == "" or (s.isdigit() and len(s) <= 4)), "%P")
        _, name = self._field(form, "Card name (for example: Emergency food)")
        amount_box, amount = self._field(form, "Amount to move (£)")
        button(amount_box, "Move all", lambda: (amount.delete(0, "end"), amount.insert(0, f"{acct.balance / 100:.2f}")),
               secondary=True, padx=12, pady=6).pack(side="left", padx=(10, 0), pady=(4, 0))
        _, pin = self._field(form, "Choose a 4-digit PIN", show="•", validate=pin_check, width=10)
        _, pin2 = self._field(form, "Confirm PIN", show="•", validate=pin_check, width=10)

        error = label(form, "", 11, True, color=T.DANGER, wraplength=760, justify="left")
        error.pack(anchor="w", pady=(12, 0))

        def submit(_event=None):
            try:
                pence = parse_amount(amount.get())
                card = state.bank.issue_card(state.account, name.get(), pence,
                                             pin.get(), pin2.get(), source="customer")
            except ValueError as exc:
                error.config(text=str(exc))
                return
            state.cards.append(card)
            self._notice = (f"Offline card '{card.name}' created with {fmt(card.allowance)}. "
                            f"{fmt(state.account.balance)} is left on your real card.", "good")
            self.show_home()

        for entry in (name, amount, pin, pin2):
            entry.bind("<Return>", submit)

        row = tk.Frame(form, bg=T.SURFACE)
        row.pack(anchor="w", pady=(14, 0))
        button(row, "Move money", submit).pack(side="left")
        button(row, "Cancel", self.show_home, secondary=True).pack(side="left", padx=(10, 0))
        name.focus_set()
        self._finish()
