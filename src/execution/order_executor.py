# File: execution/order_executor.py

from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY, SELL
from core.polymarket_client import PolymarketClient

class OrderExecutor:
    def __init__(self):
        # Instantiate your Polymarket API wrapper.
        # This wrapper is already integrated with py-order-utils to build and sign orders.
        self.client = PolymarketClient()

    def execute_signal(self, signal: dict):
        """
        Execute an order based on the provided signal.
        
        The expected signal dictionary should contain:
          - token_id: (str) The identifier for the token/market.
          - order_type: (str) Either "limit" or "market".
          - side: (str) "BUY" or "SELL".
          - For limit orders: "price" (float) and "quantity" (float)
          - For market orders: "quantity" (float) indicating order size.
        
        Returns the API response from order placement.
        """
        token_id = signal.get("token_id")
        side = signal.get("side")
        order_type = signal.get("order_type")
        
        if order_type == "limit":
            price = signal.get("price")
            quantity = signal.get("quantity")
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=quantity,
                side=side,
            )
            print(f"Placing LIMIT order: {side} {quantity} of {token_id} at {price}")
            # This call uses py-order-utils via your client to build, sign, and post the order.
            response = self.client.create_and_post_order(order_args)
            return response

        elif order_type == "market":
            quantity = signal.get("quantity")
            order_args = MarketOrderArgs(
                token_id=token_id,
                amount=quantity,  # For market orders, amount represents the order size.
                side=side,
            )
            print(f"Placing MARKET order: {side} {quantity} of {token_id}")
            signed_order = self.client.create_market_order(order_args)
            response = self.client.post_order(signed_order, orderType=OrderType.FOK)
            return response

        else:
            print(f"Invalid order type in signal: {signal}")
            return None

    def cancel_order(self, order_id: str):
        """
        Cancel a specific order using its order_id.
        
        Returns the response from the cancellation API call.
        """
        print(f"Cancelling order: {order_id}")
        response = self.client.cancel(order_id)
        return response

    def cancel_all_orders(self):
        """
        Cancel all active orders for the account.
        
        Returns the response from the cancellation API call.
        """
        print("Cancelling all orders")
        response = self.client.cancel_all()
        return response

    def exit_strategy(self, exit_reason: str = None):
        """
        Exit the current strategy by canceling all orders.
        This method can be used when an exit condition (such as stop-loss or take-profit)
        is triggered.
        
        Optionally logs the exit reason.
        
        Returns the API response from canceling all orders.
        """
        if exit_reason:
            print(f"Exiting strategy due to: {exit_reason}. Cancelling all orders.")
        else:
            print("Exiting strategy. Cancelling all orders.")
        return self.cancel_all_orders()
