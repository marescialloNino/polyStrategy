# src/bot_manager.py
from bots.base_bot import BaseBot

class BotManager:
    def __init__(self, bots):
        self.bots = bots

    def update_bots(self, order_book, trades):
        """Update all bots with the latest market data."""
        for bot in self.bots:
            bot.update(order_book, trades)