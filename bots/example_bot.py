# bots/example_bot.py
from bots.base_bot import BaseBot

class ExampleBot(BaseBot):
    def __init__(self, name):
        super().__init__(name)

    def update(self, order_book, trades):
        """Example strategy: Print the latest trade price."""
        if not trades.empty:
            latest_trade = trades.iloc[-1]
            print(f"{self.name}: Latest trade price - {latest_trade['price']}")