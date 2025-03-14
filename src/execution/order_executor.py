from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY, SELL
from src.core.clob_client import PolymarketClient

class OrderExecutor:
    def __init__(self):
        # Instantiate your Polymarket client (which uses py-order-utils)
        self.client = PolymarketClient()

    def execute_signal(self, signal: dict):
        """
        Executes an order based on the provided signal.
        
        The signal is expected to be a dictionary with keys:
          - token_id: The token/market identifier.
          - order_type: "limit" or "market".
          - side: "BUY" or "SELL".
          - For limit orders, include "price" and "quantity".
          - For market orders, include "quantity" (order size).
        
        Returns the API response from order placement.
        """
        token_id = signal.get("token_id")
        side = signal.get("side")
        order_type = signal.get("order_type")

        if order_type == "limit":
            price = signal.get("price")
            quantity = signal.get("quantity")
            print(f"Placing LIMIT order: {side} {quantity} of {token_id} at {price}")
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=quantity,
                side=side,
            )
            # Use the create_and_post_order method from the client wrapper
            response = self.client.create_and_post_order(order_args)
            return response

        elif order_type == "market":
            quantity = signal.get("quantity")
            print(f"Placing MARKET order: {side} {quantity} of {token_id}")
            order_args = MarketOrderArgs(
                token_id=token_id,
                amount=quantity,
                side=side,
            )
            signed_order = self.client.create_market_order(order_args)
            if not signed_order:
                return None
            response = self.client.post_order(signed_order, orderType=OrderType.FOK)
            return response

        else:
            print(f"Unknown order type '{order_type}' in signal: {signal}")
            return None

    def cancel_order(self, order_id: str):
        """
        Cancels a specific order.
        Returns the API response.
        """
        print(f"Cancelling order with ID: {order_id}")
        return self.client.cancel_order(order_id)

    def cancel_all_orders(self):
        """
        Cancels all active orders.
        Returns the API response.
        """
        print("Cancelling all orders.")
        return self.client.cancel_all_orders()

    def exit_strategy(self, exit_reason: str = None):
        """
        Exits the strategy by canceling all active orders.
        Optionally logs the exit reason.
        Returns the API response.
        """
        if exit_reason:
            print(f"Exiting strategy due to: {exit_reason}. Cancelling all orders.")
        else:
            print("Exiting strategy. Cancelling all orders.")
        return self.cancel_all_orders()
