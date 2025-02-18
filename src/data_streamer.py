import asyncio
import csv
from datetime import datetime
from clob_client import PolymarketClient  # Update with your actual module name

class DataStreamer:
    def __init__(self, market_id: str, interval_seconds: int = 60, filename: str = "data_stream.csv"):
        """
        Initialize the DataStreamer for a specific market.

        Args:
            market_id (str): The market/token id to stream data for.
            interval_seconds (int, optional): The time interval between data pulls. Defaults to 60 seconds.
            filename (str, optional): The CSV file name to save the data. Defaults to "data_stream.csv".
        """
        self.market_id = market_id
        self.interval_seconds = interval_seconds
        self.filename = filename
        self.client = PolymarketClient()

    async def stream(self):
        """
        Starts streaming data for the configured market. Data is written to the CSV file.
        """
        # Open the CSV file in append mode; write header once if desired.
        with open(self.filename, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            # Write header row; in a real-world scenario, you might check if file exists
            writer.writerow(["timestamp", "midpoint_price", "best_buy_price", "best_sell_price", "spread"])
            csvfile.flush()
            
            while True:
                timestamp = datetime.utcnow().isoformat()
                try:
                    midpoint = await asyncio.to_thread(self.client.get_midpoint_price, self.market_id)
                    best_buy = await asyncio.to_thread(self.client.get_price, self.market_id, "BUY")
                    best_sell = await asyncio.to_thread(self.client.get_price, self.market_id, "SELL")
                    spread = await asyncio.to_thread(self.client.get_spread, self.market_id)
                except Exception as e:
                    print(f"Error fetching data for market {self.market_id}: {e}")
                    await asyncio.sleep(self.interval_seconds)
                    continue

                row = [timestamp, midpoint,best_buy,best_sell,  spread]
                writer.writerow(row)
                csvfile.flush()
                print(f"Data written at {timestamp} for market {self.market_id}")
                await asyncio.sleep(self.interval_seconds)
