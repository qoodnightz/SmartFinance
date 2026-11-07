"""
chip.py - simulates the offline card "chip" and the bank-side checks.

Money is stored in PENCE (whole numbers) to avoid float rounding errors.
"""
import hashlib
import hmac
import secrets

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

MAX_PIN_ATTEMPTS = 3
MAX_ALLOWANCE = 100_00      # £100 maximum on one offline card
PER_TXN_LIMIT = 25_00       # £25 maximum per payment


def to_pence(pounds) -> int:
    return round(float(pounds) * 100)


def fmt(pence: int) -> str:
    return f"£{pence / 100:.2f}"


def _hash_pin(pin: str, salt: bytes) -> bytes:
    # PIN is never stored in plain text, only a salted hash
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200_000)


class RealAccount:
    """The customer's normal bank card / account inside the app."""

    def __init__(self, owner: str, balance_pence: int):
        self.owner = owner
        self.balance = balance_pence
        self.escrow = 0  # money reserved for offline cards

    def reserve(self, amount: int):
        if amount > self.balance:
            raise ValueError("Not enough money on your real card.")
        self.balance -= amount
        self.escrow += amount


class OfflineCard:
    """Behaves like the chip: holds the allowance, checks the PIN itself,
    enforces its own limits and signs every payment."""

    def __init__(self, name: str, amount: int, pin: str):
        digits = "".join(secrets.choice("0123456789") for _ in range(16))
        self.card_id = " ".join(digits[i:i + 4] for i in range(0, 16, 4))
        self.name = name
        self.allowance = amount
        self.initial_allowance = amount
        self.counter = 0              # goes up with every payment, so no two are identical
        self.failed_attempts = 0
        self.locked = False
        self._salt = secrets.token_bytes(16)
        self._pin_hash = _hash_pin(pin, self._salt)
        self._private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self._private_key.public_key()  # shared with the bank

    # ---- PIN ----
    def verify_pin(self, pin: str) -> bool:
        if self.locked:
            return False
        ok = hmac.compare_digest(_hash_pin(pin, self._salt), self._pin_hash)
        if ok:
            self.failed_attempts = 0
        else:
            self.failed_attempts += 1
            if self.failed_attempts >= MAX_PIN_ATTEMPTS:
                self.locked = True
        return ok

    @property
    def attempts_left(self) -> int:
        return max(0, MAX_PIN_ATTEMPTS - self.failed_attempts)

    # ---- Payment ----
    def pay(self, pin: str, amount: int, merchant: str) -> dict:
        """Returns a signed transaction, or raises ValueError with the decline reason."""
        if self.locked:
            raise ValueError("Card is locked after too many wrong PINs.")
        if not self.verify_pin(pin):
            raise ValueError("Wrong PIN.")
        if amount <= 0:
            raise ValueError("Amount must be more than zero.")
        if amount > PER_TXN_LIMIT:
            raise ValueError(f"Over the per-payment limit of {fmt(PER_TXN_LIMIT)}.")
        if amount > self.allowance:
            raise ValueError("Not enough offline allowance left.")

        self.counter += 1
        self.allowance -= amount
        message = f"{self.card_id}|{self.counter}|{amount}|{merchant}".encode()
        signature = self._private_key.sign(message, ec.ECDSA(hashes.SHA256()))
        return {
            "card_id": self.card_id,
            "counter": self.counter,
            "amount": amount,
            "merchant": merchant,
            "signature": signature.hex(),
        }


def verify_transaction(public_key, tx: dict, seen_counters: set) -> str:
    """Bank side, at settlement. Rejects fakes, altered amounts and replays."""
    message = f"{tx['card_id']}|{tx['counter']}|{tx['amount']}|{tx['merchant']}".encode()
    try:
        public_key.verify(bytes.fromhex(tx["signature"]), message, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return "REJECTED: invalid signature"
    key = (tx["card_id"], tx["counter"])
    if key in seen_counters:
        return "REJECTED: duplicate / replay"
    seen_counters.add(key)
    return "ACCEPTED"


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


def create_offline_card(account: RealAccount, name, amount_pounds, pin, pin2) -> OfflineCard:
    error = validate_new_card(account, name, amount_pounds, pin, pin2)
    if error:
        raise ValueError(error)
    amount = to_pence(amount_pounds)
    account.reserve(amount)  # moves money from the real card into escrow
    return OfflineCard(name.strip(), amount, pin)