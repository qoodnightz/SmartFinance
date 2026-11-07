"""
bank.py - the issuer (NatWest) side of the offline card.

Real in the demo: escrow, signature verification, duplicate rejection,
paying merchants, releasing unused allowance.
Simulated: the customer's account balance and the card itself (chip.py).

Money is stored in PENCE (whole numbers).
"""
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from chip import MAX_ALLOWANCE, OfflineCard, fmt, to_pence, tx_message


class RealAccount:
    """The customer's normal bank card / account."""

    def __init__(self, owner: str, balance_pence: int):
        self.owner = owner
        self.balance = balance_pence
        self.escrow = 0  # total reserved across all offline cards

    def reserve(self, amount: int):
        if amount > self.balance:
            raise ValueError("Not enough money on your real card.")
        self.balance -= amount
        self.escrow += amount


class Bank:
    def __init__(self):
        self._keys = {}              # card_id -> public key, registered when the card is issued
        self._escrow = {}            # card_id -> pence still held for that card
        self._seen = set()           # (card_id, counter) already settled (DB unique constraint later)
        self.merchant_totals = {}    # shop -> pence paid out

    # ---------------- Issuing ----------------
    @staticmethod
    def validate_new_card(account: RealAccount, name, amount_pounds, pin, pin2):
        """Returns an error message, or None if everything is fine."""
        if not name or not name.strip():
            return "Please give the card a name."
        amount = to_pence(amount_pounds)
        if amount <= 0:
            return "Enter an amount above £0."
        if amount > MAX_ALLOWANCE:
            return f"The maximum on an offline card is {fmt(MAX_ALLOWANCE)}."
        if amount > account.balance:
            return "You don't have enough on your real card."
        if not (pin.isdigit() and len(pin) == 4):
            return "PIN must be exactly 4 digits (numbers only)."
        if pin != pin2:
            return "The two PINs don't match."
        return None

    def issue_card(self, account: RealAccount, name, amount_pounds, pin, pin2,
                   source: str = "customer") -> OfflineCard:
        """Moves money into escrow, creates the card and registers its public key.
        source is "customer" or "ai" (was the amount AI-suggested or customer-chosen)."""
        error = self.validate_new_card(account, name, amount_pounds, pin, pin2)
        if error:
            raise ValueError(error)
        amount = to_pence(amount_pounds)
        account.reserve(amount)
        card = OfflineCard(name.strip(), amount, pin, source)
        self._keys[card.card_id] = card.public_key
        self._escrow[card.card_id] = amount
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
        account.escrow -= tx["amount"]
        self.merchant_totals[tx["merchant"]] = self.merchant_totals.get(tx["merchant"], 0) + tx["amount"]
        return "ACCEPTED: merchant paid from escrow"

    # ---------------- After the outage ----------------
    def release_unused(self, account: RealAccount, card: OfflineCard) -> int:
        """Returns whatever is left in escrow to the real balance and closes the card.
        Settle all stored payments first, or they would be left unpaid."""
        unused = self._escrow.get(card.card_id, 0)
        self._escrow[card.card_id] = 0
        account.escrow -= unused
        account.balance += unused
        card.close()
        return unused