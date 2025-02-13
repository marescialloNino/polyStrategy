# src/data_streamer.py

from clob_client import PolymarketClient
from data_processor import DataProcessor

class DataStreamer:
    def __init__(self, api_key, api_secret, market_id):
        self.client = PolymarketClient(api_key, api_secret)
        self.market_id = market_id
        self.processor = DataProcessor()

    async def start_streaming(self):
        """Start streaming data and pass it to the processor."""
        def callback(order_book, trades):
            self.processor.process_order_book(order_book)
            self.processor.process_trades(trades)

        await self.client.stream_market_data(self.market_id, callback)