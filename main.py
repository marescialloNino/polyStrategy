# main.py
import asyncio
from src.data_streamer import DataStreamer
from src.bot_manager import BotManager
from bots.example_bot import ExampleBot

async def main():
    api_key = "your_api_key"
    api_secret = "your_api_secret"
    market_id = "your_market_id"

    # Initialize bots
    bots = [ExampleBot("ExampleBot1")]
    bot_manager = BotManager(bots)

    # Initialize and start the data streamer
    streamer = DataStreamer(api_key, api_secret, market_id)
    await streamer.start_streaming()

if __name__ == "__main__":
    asyncio.run(main())