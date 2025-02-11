# bots/base_bot.py
class BaseBot:
    def __init__(self, name):
        self.name = name

    def update(self, order_book, trades):
        """Update the bot with the latest market data."""
        raise NotImplementedError("Subclasses must implement this method.")