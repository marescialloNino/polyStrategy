import os
from py_clob_client.constants import POLYGON
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import (
    BookParams,
    OpenOrderParams,
    TradeParams,
    ApiCreds,
    OrderArgs,
    MarketOrderArgs,
    OrderType
)
from py_clob_client.order_builder.constants import BUY, SELL

from ..config import (
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
        if not all([POLYMARKET_HOST, POLYMARKET_KEY, POLYMARKET_FUNDER]):
            print("Missing required environment variables: POLYMARKET_HOST, POLYMARKET_KEY, POLYMARKET_FUNDER")
            raise ValueError("Missing required environment variables")

        # Initial client to derive API keys
        initial_client = ClobClient(
            host=POLYMARKET_HOST,
            key=POLYMARKET_KEY,
            chain_id=int(POLYMARKET_CHAIN_ID),
            funder=POLYMARKET_FUNDER,
            signature_type=int(POLYMARKET_SIGNATURE_TYPE)
        )
        

        # Derive API credentials
        try:
            creds = initial_client.derive_api_key()
        except Exception as e:
            print(f"Failed to derive API credentials: {str(e)}")
            raise

        # Initialize the authenticated client
        self.client = ClobClient(
            host=POLYMARKET_HOST,
            key=POLYMARKET_KEY,
            chain_id=int(POLYMARKET_CHAIN_ID),
            funder=POLYMARKET_FUNDER,
            signature_type=int(POLYMARKET_SIGNATURE_TYPE),
            creds=ApiCreds(
                api_key=creds.api_key,
                api_secret=creds.api_secret,
                api_passphrase=creds.api_passphrase,
            )
        )
        print(f"PolymarketClient initialized with address: {self.client.get_address()}")

    # Data retrieval methods…
    def get_order_book(self, token_id: str):
        try:
            return self.client.get_order_book(token_id)
        except Exception as e:
            print(f"Error getting order book for {token_id}: {e}")
            return None

    def get_midpoint_price(self, token_id: str) -> float:
        try:
            midpoint = self.client.get_midpoint(token_id)
            return float(midpoint['mid']) if midpoint else None
        except Exception as e:
            print(f"Error getting midpoint price for {token_id}: {e}")
            return None

    def get_price(self, token_id: str, side: str) -> float:
        try:
            price_data = self.client.get_price(token_id, side)
            return float(price_data['price']) if price_data else None
        except Exception as e:
            print(f"Error getting {side} price for {token_id}: {e}")
            return None

    def get_spread(self, token_id: str) -> float:
        try:
            spread_data = self.client.get_spread(token_id)
            return float(spread_data['spread']) if spread_data else None
        except Exception as e:
            print(f"Error getting spread for {token_id}: {e}")
            return None

    def get_open_orders(self, market: str = None) -> list:
        try:
            params = OpenOrderParams(market=market) if market else None
            orders = self.client.get_orders(params=params)
            return orders
        except Exception as e:
            print(f"Error getting open orders for market {market}: {e}")
            return []

    def get_trades(self, market: str = None, maker_address: str = None) -> list:
        try:
            params = TradeParams(market=market, maker_address=maker_address) if market or maker_address else None
            trades = self.client.get_trades(params=params)
            return trades
        except Exception as e:
            print(f"Error getting trade history for market {market} and maker {maker_address}: {e}")
            return []

    # --- Order Placement Methods ---
    def create_and_post_order(self, order_args: OrderArgs):
        """
        Build, sign, and post an order.
        This method is used in the working API keys notebook.
        """
        try:
            # Create (and sign) the order
            signed_order = self.client.create_order(order_args)
            # Post the signed order
            response = self.client.post_order(signed_order)
            return response
        except Exception as e:
            print(f"Error in create_and_post_order: {e}")
            return None

    def create_order(self, order_args: OrderArgs):
        try:
            return self.client.create_order(order_args)
        except Exception as e:
            print(f"Error creating order for {order_args.token_id}: {e}")
            return None

    def post_order(self, signed_order, orderType=None):
        try:
            if orderType:
                return self.client.post_order(signed_order, orderType=orderType)
            else:
                return self.client.post_order(signed_order)
        except Exception as e:
            print(f"Error posting order: {e}")
            return None

    def create_market_order(self, order_args: MarketOrderArgs):
        try:
            return self.client.create_market_order(order_args)
        except Exception as e:
            print(f"Error creating market order for {order_args.token_id}: {e}")
            return None

    def cancel_order(self, order_id: str):
        try:
            return self.client.cancel(order_id)
        except Exception as e:
            print(f"Error cancelling order {order_id}: {e}")
            return None

    def cancel_all_orders(self):
        try:
            return self.client.cancel_all()
        except Exception as e:
            print(f"Error cancelling all orders: {e}")
            return None
