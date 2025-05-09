import asyncio
from data_streamer.data_streamer import MarketDataStreamer

async def main():
    
    streamer = MarketDataStreamer(
        slug="Cavaliers_Pacers",            # folder name to store the CSV
        token1="75257668319315408269469801686878365015769536442828459002998616661971033609731",                 # replace token IDs
        token2="106744726778569417882808847688355733040025048364560998914989057253648296994787",
        interval_seconds=10        # how often to pull data
    )


    # This will loop forever until  Ctrl+C
    await streamer.stream()

if __name__ == "__main__":
    asyncio.run(main())

