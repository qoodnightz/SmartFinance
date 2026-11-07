import tempfile
import unittest
from pathlib import Path
from datetime import date, timedelta
from neuroverse.core.events import EventBus
from neuroverse.core.state import Store
from neuroverse.services.forecast import project
from neuroverse.services.gemini_agent import build_context
from neuroverse.ui.screens.finances import to_pence

class FeatureTests(unittest.TestCase):
    def test_persistence_and_delete(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.json'
            s=Store(EventBus(),path=path)
            s.set_balance(50000)
            t=s.add_transaction((date.today()+timedelta(days=2)).isoformat(),'Test expense',-1200)
            s.update_preference('simple',False)
            s.update_action('review_bill',True)
            s.set_goal(10000)
            new=Store(EventBus(),path=path)
            self.assertEqual(new.state.balance_pence,50000)
            self.assertEqual(new.state.savings_goal_pence,10000)
            self.assertFalse(new.state.preferences['simple'])
            self.assertTrue(new.state.actions['review_bill'])
            self.assertTrue(any(x.id==t.id for x in new.state.transactions))
            self.assertTrue(new.remove_transaction(t.id))
            self.assertFalse(any(x.id==t.id for x in Store(EventBus(),path=path).state.transactions))

    def test_money_validation(self):
        self.assertEqual(to_pence('12.50'),1250)
        self.assertEqual(to_pence('£0.01'),1)
        for bad in ['12.345','nan','abc']:
            with self.assertRaises(ValueError):to_pence(bad)

    def test_agent_context(self):
        s=Store(EventBus(),path=None)
        ctx=build_context(s)
        self.assertIn('lowest_balance',ctx)
        self.assertEqual(ctx['scenario'],'Current plan')
        self.assertLessEqual(len(ctx['known_upcoming_transactions']),12)

if __name__=='__main__': unittest.main()
