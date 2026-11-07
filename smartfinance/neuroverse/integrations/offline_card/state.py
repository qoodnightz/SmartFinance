"""
state.py - the one shared bank + account + list of offline cards for the app.

Every screen imports from here so they all see the same money. The real card is linked to the
app's main balance (the one Home shows) by bind_store(), so the two can never disagree.
Offline cards live in memory: if the app is restarted they disappear and the reserved money is
simply available again, because the main balance never changed.
"""
from .bank import Bank, RealAccount

account = RealAccount("Margaret", 45000)   # replaced by the app's real balance via bind_store()
bank = Bank()
cards = []                                  # OfflineCard objects created by the user


def bind_store(store):
    """Make the real card read its total from the main app's balance."""
    account.link_total(lambda: store.state.balance_pence)
