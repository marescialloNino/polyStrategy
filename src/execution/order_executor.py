from core.polymarket_client import PolymarketClient

class OrderExecutor:
    def __init__(self):
        # Create an instance of your Polymarket API wrapper.
        self.client = PolymarketClient()

    def execute_signal(self, signal: dict):
        """
        Executes an order based on the signal generated by the strategy.
        
        The signal is expected to be a dictionary with keys:
          - token_id: The token to trade (or market identifier).
          - order_type: "limit" or "market".
          - side: "BUY" or "SELL".
          - For limit orders, include "price" and "quantity".
          - For market orders, include "quantity" (representing the order size).
        
        Returns the response from the API call.
        """
        token_id = signal.get("token_id")
        side = signal.get("side")
        order_type = signal.get("order_type")

        if order_type == "limit":
            price = signal.get("price")
            quantity = signal.get("quantity")
            print(f"Executing LIMIT order: {side} {quantity} of {token_id} at {price}")
            response = self.client.place_limit_order(token_id, price, quantity, side)
            return response

        elif order_type == "market":
            amount = signal.get("quantity")  # 'quantity' here represents the order size.
            print(f"Executing MARKET order: {side} {amount} of {token_id}")
            response = self.client.place_market_order(token_id, amount, side)
            return response

        else:
            print(f"Unknown order type '{order_type}' in signal: {signal}")
            return None

    def cancel_order(self, order_id: str):
        """
        Cancels a specific order identified by order_id.
        
        Returns the API response.
        """
        print(f"Cancelling order with ID: {order_id}")
        response = self.client.cancel_order(order_id)
        return response

    def cancel_all_orders(self):
        """
        Cancels all active orders for the current account.
        
        Returns the API response.
        """
        print("Cancelling all orders.")
        response = self.client.cancel_all_orders()
        return response

    def exit_strategy(self, exit_reason: str = None):
        """
        Executes an exit strategy by canceling all active orders.
        Optionally logs the exit reason.
        
        Returns the API response from cancel_all_orders.
        """
        if exit_reason:
            print(f"Exiting strategy due to: {exit_reason}. Cancelling all orders.")
        else:
            print("Exiting strategy. Cancelling all orders.")
        return self.cancel_all_orders()