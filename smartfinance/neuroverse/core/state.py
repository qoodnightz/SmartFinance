"""Persistent fictional ledger. Card team's event contract remains unchanged."""
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from pathlib import Path
import json
import os
import uuid
from .events import CARD_TRANSACTION, PROFILE_CHANGED, PREFERENCES_CHANGED, ACTION_CHANGED

DATA_PATH = Path(os.getenv('NEUROVERSE_DATA_FILE', str(Path.home() / '.neuroverse_ai' / 'demo_state.json')))

@dataclass(frozen=True)
class Transaction:
    id: str
    date: str
    description: str
    amount_pence: int
    source: str = 'manual'

@dataclass
class AppState:
    balance_pence: int = 45000
    transactions: list[Transaction] = field(default_factory=list)
    preferences: dict = field(default_factory=lambda: {'simple': True, 'focus': False, 'large_text': False, 'reduced_motion': True})
    selected_scenario: str = 'baseline'
    actions: dict = field(default_factory=dict)
    savings_goal_pence: int = 30000

class Store:
    def __init__(self, bus, path=DATA_PATH):
        self.bus = bus
        self.path = Path(path) if path is not None else None
        self.state = AppState()
        self._seen_ids = set()
        if not self._load():
            self._seed_transactions()
        self._seen_ids = {t.id for t in self.state.transactions}
        self.bus.subscribe(CARD_TRANSACTION, self._apply_card_transaction)

    def _seed_transactions(self):
        now = date.today()
        demo = [(3, -26000, 'Rent'), (7, -9500, 'Utilities'), (12, 32000, 'Part-time pay'),
                (18, -5500, 'Groceries'), (24, -1200, 'Subscriptions')]
        for days, amount, name in demo:
            self.state.transactions.append(Transaction(f'scheduled-{days}', (now + timedelta(days=days)).isoformat(), name, amount, 'scheduled'))

    def _load(self):
        if self.path is None or not self.path.exists():
            return False
        try:
            payload = json.loads(self.path.read_text(encoding='utf-8'))
            saved = payload.get('state', {})
            txns = []
            for obj in saved.get('transactions', []):
                date.fromisoformat(obj['date'])
                if type(obj['amount_pence']) is not int:
                    raise ValueError('Invalid amount')
                txns.append(Transaction(**obj))
            state = AppState()
            state.balance_pence = int(saved['balance_pence'])
            state.transactions = txns
            state.preferences.update({k: bool(v) for k, v in saved.get('preferences', {}).items() if k in state.preferences})
            state.actions = {str(k): bool(v) for k, v in saved.get('actions', {}).items()}
            state.savings_goal_pence = max(0, int(saved.get('savings_goal_pence', 30000)))
            state.selected_scenario = saved.get('selected_scenario', 'baseline')
            self.state = state
            return True
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            return False

    def save(self):
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix('.tmp')
        temp.write_text(json.dumps({'version': 1, 'state': asdict(self.state)}, indent=2), encoding='utf-8')
        temp.replace(self.path)

    def _notify(self):
        self.save()
        self.bus.publish(PROFILE_CHANGED)

    def _apply_card_transaction(self, data):
        """Accepted card event: id, date, description, amount_pence (negative integer).

        Must be published on Tk main thread. Never include card credentials.
        """
        if not isinstance(data, dict):
            return
        try:
            transaction_id, description = data['id'], data['description']
            amount, when = data['amount_pence'], data['date']
            if not isinstance(transaction_id, str) or not transaction_id.strip(): return
            if not isinstance(description, str) or not description.strip(): return
            if type(amount) is not int or amount >= 0: return
            date.fromisoformat(when)
        except (KeyError, TypeError, ValueError):
            return
        if transaction_id in self._seen_ids:
            return
        self._seen_ids.add(transaction_id)
        self.state.balance_pence += amount
        self.state.transactions.append(Transaction(transaction_id, when, description, amount, 'card'))
        self._notify()

    def add_transaction(self, when, description, amount_pence, source='scheduled'):
        date.fromisoformat(when)
        if not description.strip() or type(amount_pence) is not int or amount_pence == 0:
            raise ValueError('Provide a name and a nonzero amount.')
        if source not in ('scheduled', 'manual'):
            raise ValueError('Invalid source')
        txn = Transaction(str(uuid.uuid4()), when, description.strip()[:90], amount_pence, source)
        self.state.transactions.append(txn)
        self._seen_ids.add(txn.id)
        self._notify()
        return txn

    def remove_transaction(self, txn_id):
        found = next((t for t in self.state.transactions if t.id == txn_id), None)
        if not found or found.source == 'card':
            return False
        self.state.transactions.remove(found)
        self._notify()
        return True

    def set_balance(self, pence):
        if type(pence) is not int:
            raise ValueError('Invalid amount')
        self.state.balance_pence = pence
        self._notify()

    def set_goal(self, pence):
        self.state.savings_goal_pence = max(0, int(pence))
        self._notify()

    def update_preference(self, key, value):
        if key not in self.state.preferences: return
        self.state.preferences[key] = bool(value)
        self.save()
        self.bus.publish(PREFERENCES_CHANGED)

    def update_action(self, action_id, is_done):
        self.state.actions[action_id] = bool(is_done)
        self.save()
        self.bus.publish(ACTION_CHANGED)

    def reset_demo(self):
        self.state = AppState()
        self._seed_transactions()
        self._seen_ids = {t.id for t in self.state.transactions}
        self._notify()
        self.bus.publish(PREFERENCES_CHANGED)
        self.bus.publish(ACTION_CHANGED)
