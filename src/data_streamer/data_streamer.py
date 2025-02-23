import asyncio
import os
import csv
from datetime import datetime
from core.clob_client import PolymarketClient  # Update with your actual module name

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
                    await asyncio.sleep(1)
                    continue

                row = [timestamp, midpoint,best_buy,best_sell,  spread]
                writer.writerow(row)
                csvfile.flush()
                print(f"Data written at {timestamp} for market {self.market_id}")
                await asyncio.sleep(self.interval_seconds)


class MarketDataStreamer:
    def __init__(self, slug: str, token1: str, token2: str, interval_seconds: int = 60):
        """
        Initialize the MarketDataStreamer for a market identified by its slug.
        This streamer fetches data for both tokens and writes the combined data to one CSV file.

        Args:
            slug (str): The market slug (used as folder name).
            token1 (str): The first token's id.
            token2 (str): The second token's id.
            interval_seconds (int, optional): The streaming interval in seconds. Defaults to 60.
        """
        self.slug = slug
        self.token1 = token1
        self.token2 = token2
        self.interval_seconds = interval_seconds
        self.client = PolymarketClient()

        # Create a folder for this market if it does not exist.
        self.folder = os.path.join(os.getcwd(), slug)
        os.makedirs(self.folder, exist_ok=True)

        # Create the CSV file path for combined data.
        self.filename = os.path.join(self.folder, f"{slug}_combined.csv")

    async def stream(self):
        """
        Starts streaming data for both tokens concurrently and writes a single row for each timestamp.
        """
        with open(self.filename, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            # Write a header row; adjust columns as needed.
            header = [
                "timestamp",
                "token1_midpoint", "token1_best_buy", "token1_best_sell", "token1_spread",
                "token2_midpoint", "token2_best_buy", "token2_best_sell", "token2_spread",
                "token1_orderbook","token2_orderbook"
            ]
            writer.writerow(header)
            csvfile.flush()

            while True:
                timestamp = datetime.utcnow().isoformat()
                try:
                    # Query both tokens concurrently using asyncio.gather.
                    token1_data, token2_data, orderbook_data = await asyncio.gather(
                        asyncio.gather(
                            asyncio.to_thread(self.client.get_midpoint_price, self.token1),
                            asyncio.to_thread(self.client.get_price, self.token1, "BUY"),
                            asyncio.to_thread(self.client.get_price, self.token1, "SELL"),
                            asyncio.to_thread(self.client.get_spread, self.token1),
                        ),
                        asyncio.gather(
                            asyncio.to_thread(self.client.get_midpoint_price, self.token2),
                            asyncio.to_thread(self.client.get_price, self.token2, "BUY"),
                            asyncio.to_thread(self.client.get_price, self.token2, "SELL"),
                            asyncio.to_thread(self.client.get_spread, self.token2),
                        ),
                        asyncio.gather(
                            asyncio.to_thread(self.client.get_order_book, self.token1),
                            asyncio.to_thread(self.client.get_order_book, self.token2),
                        )
                    )
                except Exception as e:
                    print(f"Error fetching data for market {self.slug}: {e}")
                    await asyncio.sleep(1)
                    continue

                # Combine the results into one row.
                row = [timestamp] + token1_data + token2_data + orderbook_data
                writer.writerow(row)
                csvfile.flush()
                print(f"Data written at {timestamp} for market {self.slug}")
                await asyncio.sleep(self.interval_seconds)
