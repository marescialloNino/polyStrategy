# src/clob_client.py
from py_clob_client.client import ClobClient

class PolymarketClient:
    def __init__(self, api_key, api_secret, base_url="https://clob.polymarket.com"):
        self.client = ClobClient(api_key, api_secret, base_url)

    async def get_order_book(self, market_id):
        """Fetch the order book for a specific market."""
        return await self.client.get_order_book(market_id)

    async def get_trades(self, market_id):
        """Fetch recent trades for a specific market."""
        return await self.client.get_trades(market_id)

    async def stream_market_data(self, market_id, callback):
        """Stream live market data and pass it to a callback function."""
        while True:
            order_book = await self.get_order_book(market_id)
            trades = await self.get_trades(market_id)
            callback(order_book, trades)
            await asyncio.sleep(1)  # Adjust the interval as needed