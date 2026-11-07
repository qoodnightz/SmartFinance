"""The card team's only required integration point. No payment data or PANs."""
from datetime import date
from uuid import uuid4
from neuroverse.core.events import CARD_TRANSACTION

class CardBridge:
    def __init__(self, bus):
        self.bus = bus

    def record_practice_purchase(self, merchant: str, amount_pence: int, transaction_id=None):
        """Call ONLY for simulated/offline purchases. Negative ledger entry."""
        if type(amount_pence) is not int or amount_pence <= 0:
            raise ValueError('amount_pence must be positive integer pence')
        if not merchant.strip():
            raise ValueError('merchant required')
        self.bus.publish(CARD_TRANSACTION, {
            'id': transaction_id or str(uuid4()),
            'date': date.today().isoformat(),
            'description': merchant.strip(),
            'amount_pence': -amount_pence,
        })
