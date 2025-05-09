import asyncio
from src.data_streamer import MarketDataStreamer

async def main():
    
    streamer = MarketDataStreamer(
        slug="ETH-DAI",            # folder name to store the CSV
        token1="",                 # replace token IDs
        token2="0",
        interval_seconds=60        # how often to pull data
    )

    # This will loop forever until  Ctrl+C
    await streamer.stream()

if __name__ == "__main__":
    asyncio.run(main())

