# main.py

import asyncio
from core.clob_client import PolymarketClient
from core.gamma_client import GammaMarketsClient
from src.data_streamer.data_streamer import DataStreamer, MarketDataStreamer

async def main():

    clob_client = PolymarketClient()
    gamma_client = GammaMarketsClient()

    # Fetch active events with high liquidity and volume
    markets = gamma_client.get_markets(
        closed=False,  # Exclude closed markets
        liquidity_num_min=10000.0,  # Minimum liquidity
        volume_num_min=5000.0,  # Minimum trading volume
        start_date_min="2025-02-10",  # Markets starting after this date
        tag_id=1,  # Filter by a specific tag
    )

    if markets:
        print(f"Total markets found: {len(markets)}")
        for market in markets:
            # Safely access keys using .get() to avoid KeyError
            question = market.get("question", "N/A")
            event_id = market.get("id", "N/A")
            volume = market.get("volume", "N/A")  # Use .get() to handle missing keys
            active = market.get("active", "N/A")
            closed = market.get("closed", "N/A")
            clobTokenIds = market.get("clobTokenIds")
            orderBook = market.get("enableOrderBook", "N/A")
            print(f"Question: {question}, Event ID: {event_id}, Volume: {volume}, Active: {active}, Enabled Order book: {orderBook}")
            print(f"clobTokenIds  {clobTokenIds},")
    else:
        print("No markets found matching the criteria.")

    # print(markets[0])

    market_id = "112744708863056390222838400251590316345033278599357903193546628977027180579530"

    print(clob_client.get_last_trade_price(market_id))

    print(clob_client.get_order_book(market_id))

    print(clob_client.get_open_orders(market_id))

    


if __name__ == "__main__":
    asyncio.run(main())
    interval = 10 # Stream data every 60 seconds
    suns_id = "57360352396802137544290321106506088581975742199052649300200327070104342247071"
    bulls_id= "107290854000493755594037749211376113676959582156642033507609208497293404636891"
    market_slug="suns-bulls"
    # Create a DataStreamer instance for the market.
    streamer = MarketDataStreamer(slug=market_slug, token1=suns_id, token2=bulls_id, interval_seconds=interval)
    asyncio.run(streamer.stream())
