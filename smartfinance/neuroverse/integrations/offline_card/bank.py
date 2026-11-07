"""
bank.py - the issuer (NatWest) side of the offline card.

Real in the demo: escrow, signature verification, duplicate rejection,
paying merchants, releasing unused allowance.
Simulated: the card itself (chip.py).

The customer's real card is NOT stored here. RealAccount reads the total from the main app's
balance, so Home and the Offline card screen always show the same money.

Money is stored in PENCE (whole numbers).
"""
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from .chip import OfflineCard, fmt, tx_message


class RealAccount:
    """The customer's normal bank card / account.

    total     = everything the customer owns (what Home shows). Includes money reserved offline.
    escrow    = the part of the total currently reserved on offline cards.
    balance   = what is still available on the real card (total - escrow).

    `total` can be a number (stand-alone use) or a function that returns the current total,
    which is how the app links it to its main balance.
    """

    def __init__(self, owner: str, total):
        self.owner = owner
        self.escrow = 0
        self.link_total(total)

    def link_total(self, total):
        if callable(total):
            self._fixed = None
            self._total = total
        else:
            self._fixed = int(total)
            self._total = lambda: self._fixed

    @property
    def total(self) -> int:
        return self._total()

    @property
    def balance(self) -> int:
        return max(0, self.total - self.escrow)

    def reserve(self, amount: int):
        if amount > self.balance:
            raise ValueError(f"You only have {fmt(self.balance)} available on your real card.")
        self.escrow += amount

    def release(self, amount: int):
        """Reserved money becomes available on the real card again."""
        self.escrow = max(0, self.escrow - amount)

    def pay_out(self, amount: int):
        """Reserved money was spent. The app's main balance goes down through CardBridge;
        in stand-alone mode the fixed total is reduced here."""
        self.escrow = max(0, self.escrow - amount)
        if self._fixed is not None:
            self._fixed -= amount


class Bank:
    def __init__(self):
        self._keys = {}              # card_id -> public key, registered when the card is issued
        self._escrow = {}            # card_id -> pence still held for that card
        self._seen = set()           # (card_id, counter) already settled (DB unique constraint later)
        self.merchant_totals = {}    # shop -> pence paid out

    # ---------------- Issuing ----------------
    @staticmethod
    def validate_new_card(account: RealAccount, name, amount_pence, pin, pin2):
        """Returns an error message, or None if everything is fine. There is no maximum amount."""
        if not name or not name.strip():
            return "Please give the card a name."
        if len(name.strip()) > 30:
            return "Keep the card name to 30 characters or fewer."
        if amount_pence <= 0:
            return "Enter an amount above £0."
        if amount_pence > account.balance:
            return f"You only have {fmt(account.balance)} available on your real card."
        if not (pin.isdigit() and len(pin) == 4):
            return "PIN must be exactly 4 digits (numbers only)."
        if pin != pin2:
            return "The two PINs don't match."
        return None

    def issue_card(self, account: RealAccount, name, amount_pence: int, pin, pin2,
                   source: str = "customer") -> OfflineCard:
        """Reserves the money, creates the card and registers its public key.
        source is "customer" or "ai" (was the amount AI-suggested or customer-chosen)."""
        error = self.validate_new_card(account, name, amount_pence, pin, pin2)
        if error:
            raise ValueError(error)
        account.reserve(amount_pence)
        card = OfflineCard(name.strip(), amount_pence, pin, source)
        self._keys[card.card_id] = card.public_key
        self._escrow[card.card_id] = amount_pence
        return card

    def escrow_for(self, card_id: str) -> int:
        return self._escrow.get(card_id, 0)

    # ---------------- Settlement ----------------
    def settle(self, account: RealAccount, tx: dict) -> str:
        """Called for each stored payment once the network is back.
        Rejects fakes, altered amounts and replays; pays the merchant from escrow."""
        card_id = tx.get("card_id")
        public_key = self._keys.get(card_id)      # the bank's own copy, never the one in the payment
        if public_key is None:
            return "REJECTED: unknown card"

        try:
            message = tx_message(card_id, tx["counter"], tx["amount"], tx["merchant"])
            public_key.verify(bytes.fromhex(tx["signature"]), message, ec.ECDSA(hashes.SHA256()))
        except (InvalidSignature, KeyError, ValueError):
            return "REJECTED: invalid signature"

        key = (card_id, tx["counter"])
        if key in self._seen:
            return "REJECTED: duplicate / replay (merchant already paid once)"
        if tx["amount"] > self._escrow[card_id]:
            return "REJECTED: more than the escrow held for this card"

        self._seen.add(key)
        self._escrow[card_id] -= tx["amount"]
        account.pay_out(tx["amount"])
        self.merchant_totals[tx["merchant"]] = self.merchant_totals.get(tx["merchant"], 0) + tx["amount"]
        return "ACCEPTED: merchant paid from escrow"

    # ---------------- Deleting a card ----------------
    def release_unused(self, account: RealAccount, card: OfflineCard) -> int:
        """Deleting a card: whatever is left in escrow goes back to the real card and the
        card is closed. Settle all stored payments first, or they would be left unpaid."""
        unused = self._escrow.get(card.card_id, 0)
        self._escrow[card.card_id] = 0
        account.release(unused)
        card.close()
        return unused
