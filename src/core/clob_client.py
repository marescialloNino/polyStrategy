
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

# Import your config variables
from src.config import (
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
        self.client = ClobClient(
            host=POLYMARKET_HOST,
            key=POLYMARKET_KEY,
            chain_id=POLYGON,
            funder=POLYMARKET_FUNDER,
            signature_type=POLYMARKET_SIGNATURE_TYPE,
            creds=ApiCreds(
                api_key=POLYMARKET_API_KEY,
                api_secret=POLYMARKET_API_SECRET,
                api_passphrase=POLYMARKET_API_PASSPHRASE,
            )
        )

    def get_order_book(self, token_id: str):
        """
        Retrieves the order book for a specific token.

        Args:
            token_id (str): The ID of the token to get the order book for.

        Returns:
            The order book object as returned by the ClobClient.
        """
        try:
            orderbook = self.client.get_order_book(token_id)
            return orderbook  # Return the native order book object
        except Exception as e:
            print(f"Error getting order book for {token_id}: {e}")
            return None

    def get_multiple_order_books(self, token_ids: list[str]):
        """
        Retrieves multiple order books for a list of token IDs.

        Args:
            token_ids (list[str]): A list of token IDs to retrieve order books for.

        Returns:
            A list of order book objects as returned by the ClobClient.
        """
        try:
            params = [BookParams(token_id=token_id) for token_id in token_ids]
            orderbooks = self.client.get_order_books(params)
            return orderbooks  # Return the native order book objects
        except Exception as e:
            print(f"Error getting multiple order books: {e}")
            return []

    def get_last_trade_price(self, token_id: str) -> float:
        """
        Retrieves the last trade price for a specific token.

        Args:
            token_id (str): The ID of the token.

        Returns:
            dict: {'price': , 'side': }.
        """
        try:
            last_trade = self.client.get_last_trade_price(token_id)
            return last_trade if last_trade else None
        except Exception as e:
            print(f"Error getting last trade price for {token_id}: {e}")
            return None

    def get_multiple_last_trade_prices(self, token_ids: list[str]) -> dict[str, float]:
        """
        Retrieves the last trade prices for a list of token IDs.

        Args:
            token_ids (list[str]): A list of token IDs.

        Returns:
            dict[str, float]: A dictionary mapping token IDs to their last trade prices.
        """
        try:
            params = [BookParams(token_id=token_id) for token_id in token_ids]
            prices = self.client.get_last_trades_prices(params)
            return {item['token_id']: float(item['price']) for item in prices}
        except Exception as e:
            print(f"Error getting multiple last trade prices: {e}")
            return {}

    def get_open_orders(self, market: str = None) -> list:
        """
        Retrieves open orders for a specific market (or all markets if market is None).
        Requires API Key authentication.

        Args:
            market (str, optional): The market (token ID) to filter orders by.

        Returns:
            list: A list of open order objects.
        """
        try:
            params = OpenOrderParams(market=market) if market else None
            orders = self.client.get_orders(params=params)
            return orders
        except Exception as e:
            print(f"Error getting open orders for market {market}: {e}")
            return []

    def get_trades(self, market: str = None, maker_address: str = None) -> list:
        """
        Retrieves trade history for a specific market and/or maker address.
        Requires API Key authentication.

        Args:
            market (str, optional): The market (token ID) to filter trades by.
            maker_address (str, optional): The maker address to filter trades by.

        Returns:
            list: A list of trade objects.
        """
        try:
            params = TradeParams(market=market, maker_address=maker_address) if market or maker_address else None
            trades = self.client.get_trades(params=params)
            return trades
        except Exception as e:
            print(f"Error getting trade history for market {market} and maker {maker_address}: {e}")
            return []

    def get_midpoint_price(self, token_id: str) -> float:
        """
        Retrieves the midpoint price for a specific token.

        Args:
            token_id (str): The ID of the token.

        Returns:
            float: The midpoint price.
        """
        try:
            midpoint = self.client.get_midpoint(token_id)
            return float(midpoint['mid']) if midpoint else None
        except Exception as e:
            print(f"Error getting midpoint price for {token_id}: {e}")
            return None

    def get_multiple_midpoint_prices(self, token_ids: list[str]) -> dict[str, float]:
        """
        Retrieves the midpoint prices for a list of token IDs.

        Args:
            token_ids (list[str]): A list of token IDs.

        Returns:
            dict[str, float]: A dictionary mapping token IDs to their midpoint prices.
        """
        try:
            params = [BookParams(token_id=token_id) for token_id in token_ids]
            midpoints = self.client.get_midpoints(params)
            return {item['token_id']: float(item['mid']) for item in midpoints}
        except Exception as e:
            print(f"Error getting multiple midpoint prices: {e}")
            return {}

    def get_markets(self) -> list:
        """
        Retrieves available markets.

        Returns:
            list: A list of market objects.
        """
        try:
            markets = self.client.get_simplified_markets()  # Alternatively, self.client.get_markets() for detailed info
            return markets
        except Exception as e:
            print(f"Error getting markets: {e}")
            return []

    def get_price(self, token_id: str, side: str) -> float:
        """
        Retrieves the best bid or ask price for a specific token.

        Args:
            token_id (str): The ID of the token.
            side (str): 'BUY' or 'SELL'.

        Returns:
            float: The best bid or ask price.
        """
        try:
            price_data = self.client.get_price(token_id, side)
            return float(price_data['price']) if price_data else None
        except Exception as e:
            print(f"Error getting {side} price for {token_id}: {e}")
            return None

    def get_multiple_prices(self, token_ids: list[str], side: str) -> dict[str, float]:
        """
        Retrieves the best bid or ask prices for a list of token IDs.

        Args:
            token_ids (list[str]): A list of token IDs.
            side (str): 'BUY' or 'SELL'.

        Returns:
            dict[str, float]: A dictionary mapping token IDs to their best bid or ask prices.
        """
        try:
            params = [BookParams(token_id=token_id, side=side) for token_id in token_ids]
            prices = self.client.get_prices(params)
            return {item['token_id']: float(item['price']) for item in prices}
        except Exception as e:
            print(f"Error getting multiple {side} prices: {e}")
            return {}

    def get_spread(self, token_id: str) -> float:
        """
        Retrieves the spread for a specific token.

        Args:
            token_id (str): The ID of the token.

        Returns:
            float: The spread.
        """
        try:
            spread_data = self.client.get_spread(token_id)
            return float(spread_data['spread']) if spread_data else None
        except Exception as e:
            print(f"Error getting spread for {token_id}: {e}")
            return None

    def get_multiple_spreads(self, token_ids: list[str]) -> dict[str, float]:
        """
        Retrieves the spreads for a list of token IDs.

        Args:
            token_ids (list[str]): A list of token IDs.

        Returns:
            dict[str, float]: A dictionary mapping token IDs to their spreads.
        """
        try:
            params = [BookParams(token_id=token_id) for token_id in token_ids]
            spreads = self.client.get_spreads(params)
            return {item['token_id']: float(item['spread']) for item in spreads}
        except Exception as e:
            print(f"Error getting multiple spreads: {e}")
            return {}
        

    # ==========================
    # Order Placement Methods
    # ==========================
    def place_limit_order(self, token_id: str, price: float, size: float, side: str):
        """
        Places a limit order.
        Args:
            token_id (str): The token ID for which the order is placed.
            price (float): The limit price.
            size (float): The size (number of tokens) to order.
            side (str): 'BUY' or 'SELL'.
        Returns:
            dict: Response from the order placement.
        """
        try:
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=side,
            )
            signed_order = self.client.create_order(order_args)

            response = self.client.post_order(signed_order, OrderType.FOK)
            print(f"Limit order placed: {response}")
            return response
        except Exception as e:
            print(f"Error placing limit order for {token_id}: {e}")
            return None

    def place_market_order(self, token_id: str, amount: float, side: str):
        """
        Places a market order.
        Args:
            token_id (str): The token ID for which the order is placed.
            amount (float): For BUY orders, the collateral amount to spend.
                            For SELL orders, the number of shares to sell.
            side (str): 'BUY' or 'SELL'.
        Returns:
            dict: Response from the order placement.
        """
        try:
            order_args = MarketOrderArgs(
                token_id=token_id,
                amount=amount,
                side=side,
            )
            signed_order = self.client.create_market_order(order_args)
            response = self.client.post_order(signed_order, orderType=OrderType.FOK)
            print(f"Market order placed: {response}")
            return response
        except Exception as e:
            print(f"Error placing market order for {token_id}: {e}")
            return None

    def cancel_order(self, order_id: str):
        """
        Cancels an existing order.
        Args:
            order_id (str): The ID of the order to cancel.
        Returns:
            dict: Response from the cancellation request.
        """
        try:
            response = self.client.cancel(order_id)
            print(f"Order {order_id} cancelled: {response}")
            return response
        except Exception as e:
            print(f"Error cancelling order {order_id}: {e}")
            return None

    def cancel_all_orders(self):
        """
        Cancels all orders for the current API credentials.
        Returns:
            dict: Response from the cancellation request.
        """
        try:
            response = self.client.cancel_all()
            print(f"All orders cancelled: {response}")
            return response
        except Exception as e:
            print(f"Error cancelling all orders: {e}")
            return None