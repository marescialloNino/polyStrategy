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

from config import (
    POLYMARKET_HOST,
    POLYMARKET_KEY,
    POLYMARKET_CHAIN_ID,
    POLYMARKET_FUNDER,
    POLYMARKET_SIGNATURE_TYPE,
    POLYMARKET_API_KEY,
    POLYMARKET_API_SECRET,
    POLYMARKET_API_PASSPHRASE
)

import logging

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

    def search_markets_by_keyword(self, keyword, market_status=None, limit=None):
        """
        Search for markets containing a specific keyword in their slug.
        
        Args:
            keyword (str): The keyword to search for in market slugs
            market_status (str, optional): Filter by market status (e.g., 'open', 'closed')
            limit (int, optional): Maximum number of markets to return
            
        Returns:
            list: Markets matching the keyword in their slug
        """
        try:
            # First get all markets (potentially filtered by status)
            all_markets = self.client.get_markets(status=market_status, limit=limit)
            
            # Then filter these markets by keyword in the slug
            matching_markets = []
            for market in all_markets:
                slug = market.get('slug', '').lower()
                if keyword.lower() in slug:
                    matching_markets.append(market)
            
            logging.info(f"Found {len(matching_markets)} markets matching keyword '{keyword}'")
            return matching_markets
            
        except Exception as e:
            logging.error(f"Error searching markets with keyword '{keyword}': {e}")
            return []

    def filter_markets(self, 
                   keyword=None, 
                   market_status=None, 
                   min_volume=None, 
                   max_volume=None,
                   min_liquidity=None,
                   category=None,
                   token_id=None,
                   limit=None):
        """
        Filter markets by multiple criteria including keyword in slug.
        
        Args:
            keyword (str, optional): Keyword to search for in market slugs
            market_status (str, optional): Market status filter (e.g. 'open', 'closed')
            min_volume (float, optional): Minimum trading volume
            max_volume (float, optional): Maximum trading volume
            min_liquidity (float, optional): Minimum liquidity
            category (str, optional): Market category
            token_id (str, optional): Specific token ID to look for
            limit (int, optional): Maximum number of markets to return
            
        Returns:
            list: Markets matching all specified criteria
        """
        try:
            # Get all markets (potentially filtered by status)
            all_markets = self.client.get_markets(status=market_status, limit=limit)
            
            # Apply additional filters
            filtered_markets = []
            
            for market in all_markets:
                # Start with the assumption that the market matches
                matches = True
                
                # Apply keyword filter on slug if specified
                if keyword and keyword.lower() not in market.get('slug', '').lower():
                    matches = False
                    
                # Apply volume filter if specified
                if matches and min_volume is not None:
                    volume = float(market.get('volume', 0))
                    if volume < min_volume:
                        matches = False
                        
                if matches and max_volume is not None:
                    volume = float(market.get('volume', 0))
                    if volume > max_volume:
                        matches = False
                        
                # Apply liquidity filter if specified
                if matches and min_liquidity is not None:
                    liquidity = float(market.get('liquidity', 0))
                    if liquidity < min_liquidity:
                        matches = False
                        
                # Apply category filter if specified
                if matches and category is not None:
                    if market.get('category') != category:
                        matches = False
                        
                # Apply token_id filter if specified
                if matches and token_id is not None:
                    tokens = market.get('tokens', [])
                    token_found = any(token.get('token_id') == token_id for token in tokens)
                    if not token_found:
                        matches = False
                    
                # If market passed all filters, add it to results
                if matches:
                    filtered_markets.append(market)
                    
            logging.info(f"Found {len(filtered_markets)} markets matching all criteria")
            return filtered_markets
            
        except Exception as e:
            logging.error(f"Error filtering markets: {e}")
            return []

    def get_market_by_slug_keyword(self, keyword):
        """
        Get a specific market by searching for a keyword in its slug.
        Returns the first match if multiple markets contain the keyword.
        
        Args:
            keyword (str): Keyword to search for in market slugs
            
        Returns:
            dict: Market data for the first matching market, or None if not found
        """
        matching_markets = self.search_markets_by_keyword(keyword)
        
        if matching_markets:
            if len(matching_markets) > 1:
                logging.warning(f"Multiple markets found with keyword '{keyword}'. Returning the first match.")
                for idx, market in enumerate(matching_markets):
                    logging.info(f"Match {idx+1}: {market.get('slug')} - {market.get('question')}")
            
            return matching_markets[0]
        else:
            logging.warning(f"No markets found with keyword '{keyword}'")
            return None

    def get_tokens_for_market_by_keyword(self, keyword):
        """
        Get token IDs for a market found by keyword search in its slug.
        
        Args:
            keyword (str): Keyword to search for in market slugs
            
        Returns:
            tuple: (market_slug, token1_id, token2_id) or (None, None, None) if not found
        """
        market = self.get_market_by_slug_keyword(keyword)
        
        if market and 'tokens' in market and len(market['tokens']) >= 2:
            slug = market.get('slug')
            token1_id = market['tokens'][0]['token_id']
            token2_id = market['tokens'][1]['token_id']
            
            logging.info(f"Found tokens for market '{slug}':")
            logging.info(f"Token1 ID: {token1_id}")
            logging.info(f"Token2 ID: {token2_id}")
            
            return slug, token1_id, token2_id
        else:
            logging.warning(f"Could not find tokens for market with keyword '{keyword}'")
            return None, None, None

    def filter_markets_by_slug_keyword(self, markets, keyword):
        """
        Filter markets by keyword in their slug.
        
        Args:
            markets (list): List of markets already filtered by other criteria
            keyword (str): Keyword to search for in the slug
            
        Returns:
            list: Markets that contain the keyword in their slug
        """
        if not keyword:
            return markets
        
        keyword = keyword.lower()
        filtered_markets = []
        
        for market in markets:
            slug = market.get('slug', '').lower()
            if keyword in slug:
                filtered_markets.append(market)
        
        logging.info(f"Found {len(filtered_markets)} markets with '{keyword}' in slug")
        return filtered_markets
