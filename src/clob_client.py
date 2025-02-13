
import asyncio
from py_clob_client.constants import POLYGON
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds


# Import your config variables
from config import (
    POLYMARKET_HOST,
    POLYMARKET_KEY,
    POLYMARKET_CHAIN_ID,
    POLYMARKET_FUNDER,
    POLYMARKET_SIGNATURE_TYPE,
    POLYMARKET_API_KEY,
    POLYMARKET_API_SECRET,
    POLYMARKET_API_PASSPHRASE
)

class PolymarketClient:
    def __init__(self, base_url=POLYMARKET_HOST):
        self.client = ClobClient(
            host=POLYMARKET_HOST,
            key=POLYMARKET_KEY,
            chain_id=POLYMARKET_CHAIN_ID,
            funder=POLYMARKET_FUNDER,
            signature_type=POLYMARKET_SIGNATURE_TYPE,
            creds=ApiCreds(
                api_key=POLYMARKET_API_KEY,
                api_secret=POLYMARKET_API_SECRET,
                api_passphrase=POLYMARKET_API_PASSPHRASE,
            )
        )

    def get_available_markets(self):
        return self.client.get_markets(next_cursor = "")

    def get_order_book(self, market_id):
        """Fetch the order book for a specific market."""
        return self.client.get_order_book(market_id)

    async def get_trades(self, market_id):
        """Fetch recent trades for a specific market."""
        return await self.client.get_trades(market_id)

    async def stream_market_data(self, market_id, callback):
        """
        Stream live market data and pass it to a callback function.
        Adjust the `await asyncio.sleep(1)` interval as needed.
        """
        while True:
            order_book = await self.get_order_book(market_id)
            trades = await self.get_trades(market_id)
            callback(order_book, trades)
            await asyncio.sleep(1)
