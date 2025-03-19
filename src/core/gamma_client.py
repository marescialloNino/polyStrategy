# src/gamma_client.py
import requests
import time

class GammaMarketsClient:
    def __init__(self, base_url="https://gamma-api.polymarket.com"):
        self.base_url = base_url

    def get_markets(
        self,
        limit=100, 
        offset=0,  
        order=None, 
        ascending=True,  
        id=None,  
        slug=None,  
        archived=None, 
        active=None,  
        closed=None,  
        clob_token_ids=None,  
        condition_ids=None,  
        liquidity_num_min=None,  
        liquidity_num_max=None,  
        volume_num_min=None,  
        volume_num_max=None,  
        start_date_min=None,  
        start_date_max=None,  
        end_date_min=None, 
        end_date_max=None,  
        tag_id=None,  
        related_tags=False, 
    ):
        """
        Fetch markets with optional filters, handling pagination using limit and offset.

        Parameters:
            limit (int): Number of results per request (default: 100).
            offset (int): Pagination offset (default: 0).
            order (str): Key to sort by (e.g., "volume", "liquidity").
            ascending (bool): Sort direction (default: True for ascending).
            id (int): market IDs to query.
            slug (str): event slug to query.
            archived (bool): Filter by archived status.
            active (bool): Filter by active status.
            closed (bool): Filter by closed status.
            clob_token_ids (list): List of CLOB token IDs to filter by.
            condition_ids (list): List of condition IDs to filter by.
            liquidity_num_min (float): Minimum liquidity required.
            liquidity_num_max (float): Maximum liquidity allowed.
            volume_num_min (float): Minimum trading volume required.
            volume_num_max (float): Maximum trading volume allowed.
            start_date_min (str): Minimum start date (format: YYYY-MM-DD).
            start_date_max (str): Maximum start date (format: YYYY-MM-DD).
            end_date_min (str): Minimum end date (format: YYYY-MM-DD).
            end_date_max (str): Maximum end date (format: YYYY-MM-DD).
            tag_id (int): Filter by tag ID.
            related_tags (bool): Include events with related tags (requires tag_id).

        Returns:
            list: A list of all markets matching the filters.
        """
        url = f"{self.base_url}/markets"
        params = {
            "limit": limit,
            "offset": offset,
        }

        # Add filters to the query parameters
        if order:
            params["order"] = order
            params["ascending"] = str(ascending).lower()  # Convert boolean to string
        if id:
            params["id"] = id
        if slug:
            params["slug"] = slug 
        if archived is not None:
            params["archived"] = str(archived).lower()
        if active is not None:
            params["active"] = str(active).lower()
        if closed is not None:
            params["closed"] = str(closed).lower()
        if clob_token_ids is not None:
            params["clob_token_ids"] = clob_token_ids 
        if condition_ids is not None:
            params["condition_ids"] = condition_ids  
        if liquidity_num_min is not None:
            params["liquidity_num_min"] = liquidity_num_min
        if liquidity_num_max is not None:
            params["liquidity_num_max"] = liquidity_num_max
        if volume_num_min is not None:
            params["volume_num_min"] = volume_num_min
        if volume_num_max is not None:
            params["volume_num_max"] = volume_num_max
        if start_date_min:
            params["start_date_min"] = start_date_min
        if start_date_max:
            params["start_date_max"] = start_date_max
        if end_date_min:
            params["end_date_min"] = end_date_min
        if end_date_max:
            params["end_date_max"] = end_date_max
        if tag_id is not None:
            params["tag_id"] = tag_id
            if related_tags:
                params["related_tags"] = "true"

        all_markets = []

        while True:
            # Make the API request
            response = requests.get(url, params=params)
            if response.status_code == 200:
                markets = response.json()  # Response is a list of events
                all_markets.extend(markets)

                # Check if there are more results
                if len(markets) < limit:
                    break  # No more results to fetch
                else:
                    params["offset"] += limit  # Move to the next set of results
                    time.sleep(0.05)  # Add a small delay between requests
            elif response.status_code == 429:
                print("Rate limit exceeded. Retrying after a delay...")
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                print(f"Error fetching markets: {response.status_code}")
                return None

        return all_markets
    

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
        
        print(f"Found {len(filtered_markets)} markets with '{keyword}' in slug")
        return filtered_markets




        
    def get_market(self, id):

        url = f"{self.base_url}/markets/{id}"

        # Make the API request
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching single market: {response.status_code}")
            return None


