# main.py

import asyncio
from core.clob_client import PolymarketClient
from core.gamma_client import GammaMarketsClient
from data_streamer.data_streamer import DataStreamer, MarketDataStreamer

async def main():

    clob_client = PolymarketClient()
    gamma_client = GammaMarketsClient()

    # Fetch active events with high liquidity and volume
    markets = gamma_client.get_markets(
        closed=False,  # Exclude closed markets
        liquidity_num_min=30000.0,  # Minimum liquidity
        volume_num_min=5000.0,  # Minimum trading volume
        start_date_min="2025-04-20",  # Markets starting after this date
        tag_id=1,  # Filter by a specific tag
    )

    nba_markets = clob_client.filter_markets_by_slug_keyword(markets=markets,keyword="nba")

    if nba_markets:
        print(f"Total markets found: {len(nba_markets)}")
        for market in nba_markets:
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

    

    print(nba_markets[3])

    market_id = "53681121737188904508898102030817879322057417525669935097908373985792992196557"


    # print(clob_client.get_order_book(market_id))

    # print(clob_client.get_open_orders(market_id)) 

    


if __name__ == "__main__":
    asyncio.run(main())
    
