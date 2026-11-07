import unittest
from datetime import date
from neuroverse.core.events import EventBus, CARD_TRANSACTION
from neuroverse.core.state import Store
from neuroverse.integrations.card_bridge import CardBridge
from neuroverse.services.forecast import project

class CoreTests(unittest.TestCase):
    def test_forecast_baseline(self):
        store = Store(EventBus(), path=None)
        r = project(store.state.balance_pence, store.state.transactions)
        self.assertEqual(r['lowest']['balance_pence'], 9500)
        self.assertIsNone(r['shortfall'])

    def test_emergency_scenario(self):
        store = Store(EventBus(), path=None)
        b = project(store.state.balance_pence, store.state.transactions)
        e = project(store.state.balance_pence, store.state.transactions, scenario='emergency')
        self.assertEqual(e['end_balance_pence'], b['end_balance_pence'] - 15000)

    def test_card_bridge_and_dedupe(self):
        bus = EventBus()
        store = Store(bus, path=None)
        bridge = CardBridge(bus)
        bridge.record_practice_purchase('Sample shop', 1250, transaction_id='once')
        self.assertEqual(store.state.balance_pence, 43750)
        bridge.record_practice_purchase('Sample shop', 1250, transaction_id='once')
        self.assertEqual(store.state.balance_pence, 43750)

    def test_reject_bad_card_event(self):
        bus = EventBus()
        store = Store(bus, path=None)
        bus.publish(CARD_TRANSACTION, {'id': 'invalid', 'description': 'Bad', 'amount_pence': '100', 'date': date.today().isoformat()})
        self.assertEqual(store.state.balance_pence, 45000)

if __name__ == '__main__':
    unittest.main()
