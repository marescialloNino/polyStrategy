# main.py

import asyncio
from clob_client import PolymarketClient
from gamma_client import GammaMarketsClient

# Example callback function
def market_data_callback(order_book, trades):
    print("Order Book:", order_book)
    print("Recent Trades:", trades)

async def main():

    clob_client = PolymarketClient()
    gamma_client = GammaMarketsClient()

    # Fetch active events with high liquidity and volume
    markets = gamma_client.get_markets(
        closed=False,  # Exclude closed markets
        liquidity_num_min=100000.0,  # Minimum liquidity
        volume_num_min=50000.0,  # Minimum trading volume
        start_date_min="2025-01-20",  # Markets starting after this date
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

    market_id = "26913206576615123658281612537020791932768401561050089403305718432907195908129"

    # print(client.get_available_markets())
    # Fetch order book
    ob = clob_client.get_order_book(market_id)
    print("Order Book:", ob)


    # Fetch recent trades
    #t = await client.get_trades(market_id)
    #print("Trades:", t)

    # Or stream data
    # await client.stream_market_data(market_id, market_data_callback)
    


if __name__ == "__main__":
    asyncio.run(main())
