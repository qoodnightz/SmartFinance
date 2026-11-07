"""
state.py - the one shared bank + account + list of offline cards for the app.

Every screen imports from here so they all see the same money.
Later this can be wired to the main app's store / card_bridge.py instead of the demo values.
"""
from .bank import Bank, RealAccount

account = RealAccount("Margaret", 500_00)   # demo: £500 on the real card
bank = Bank()
cards = []                                  # OfflineCard objects created by the user