"""
chip.py - simulates the offline card "chip".

The chip is the tamper-resistant part of the card. It holds the allowance,
checks the PIN itself, enforces its own limits and signs every payment.
Nothing in here talks to the bank - that is bank.py.

Money is stored in PENCE (whole numbers) to avoid float rounding errors.
"""
import hashlib
import hmac
import json
import secrets

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

# ---- Offline parameters loaded onto the chip (brief, section 5) ----
MAX_PIN_ATTEMPTS = 3
MAX_ALLOWANCE = 100_00         # £100 maximum on one offline card
PER_TXN_LIMIT = 25_00          # £25 maximum per payment
MAX_OFFLINE_PAYMENTS = 5       # consecutive offline payments before the chip must go online


# ---- Shared helpers ----
def to_pence(pounds) -> int:
    return round(float(pounds) * 100)


def fmt(pence: int) -> str:
    return f"£{pence / 100:.2f}"


def tx_message(card_id: str, counter: int, amount: int, merchant: str) -> bytes:
    """The exact bytes that get signed. Used by BOTH the chip (to sign) and the
    bank (to verify), so they can never drift apart. JSON keeps the fields
    unambiguous even if a shop name contains odd characters."""
    return json.dumps([card_id, counter, amount, merchant], separators=(",", ":")).encode()


def _hash_pin(pin: str, salt: bytes) -> bytes:
    # The PIN is never stored in plain text, only a salted hash
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200_000)


class OfflineCard:
    """Behaves like the chip."""

    def __init__(self, name: str, amount: int, pin: str, source: str = "customer"):
        digits = "".join(secrets.choice("0123456789") for _ in range(16))
        self.card_id = " ".join(digits[i:i + 4] for i in range(0, 16, 4))
        self.name = name
        self.allowance = amount
        self.initial_allowance = amount
        self.source = source                       # "customer" or "ai" (brief, section 7)
        self.max_offline_payments = MAX_OFFLINE_PAYMENTS
        self.offline_count = 0                     # payments since the chip last went online
        self.counter = 0                           # goes up with every payment, so no two are identical
        self.failed_attempts = 0
        self.locked = False
        self.closed = False                        # set when unused allowance is released
        self._salt = secrets.token_bytes(16)
        self._pin_hash = _hash_pin(pin, self._salt)
        self._private_key = ec.generate_private_key(ec.SECP256R1())  # never leaves the chip
        self.public_key = self._private_key.public_key()             # registered with the bank

    # ---- PIN ----
    def verify_pin(self, pin: str) -> bool:
        if self.locked or self.closed:
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

    @property
    def offline_payments_left(self) -> int:
        return max(0, self.max_offline_payments - self.offline_count)

    # ---- Payment ----
    def pay(self, pin: str, amount: int, merchant: str) -> dict:
        """Returns a signed transaction, or raises ValueError with the decline reason."""
        if self.closed:
            raise ValueError("This card is closed. Its unused allowance was returned.")
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
        if self.offline_count >= self.max_offline_payments:
            raise ValueError(
                f"Offline payment limit of {self.max_offline_payments} reached. "
                "The card must go online once before it can be used offline again."
            )

        self.counter += 1
        self.offline_count += 1
        self.allowance -= amount
        signature = self._private_key.sign(
            tx_message(self.card_id, self.counter, amount, merchant),
            ec.ECDSA(hashes.SHA256()),
        )
        return {
            "card_id": self.card_id,
            "counter": self.counter,
            "amount": amount,
            "merchant": merchant,
            "signature": signature.hex(),
        }

    # ---- Back online ----
    def sync(self):
        """Called when the card reconnects: the offline payment count resets."""
        self.offline_count = 0

    def close(self):
        """Allowance is returned to the customer; the chip stops working."""
        self.allowance = 0
        self.closed = True