"""Main-thread event bus. Only publish from Tk callbacks, not worker threads."""
from collections import defaultdict

CARD_TRANSACTION = 'card.transaction'
PROFILE_CHANGED = 'profile.changed'
PREFERENCES_CHANGED = 'preferences.changed'
ACTION_CHANGED = 'action.changed'

class EventBus:
    def __init__(self):
        self._listeners = defaultdict(list)

    def subscribe(self, topic, handler):
        self._listeners[topic].append(handler)
        return lambda: self.unsubscribe(topic, handler)

    def unsubscribe(self, topic, handler):
        if handler in self._listeners[topic]:
            self._listeners[topic].remove(handler)

    def publish(self, topic, payload=None):
        for handler in tuple(self._listeners[topic]):
            handler(payload)
