import asyncio
import logging
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from src.core.polymarket_websocket_client import PolymarketWebSocketClient

@dataclass
class OrderStatus:
    order_id: str
    token_id: str
    side: str
    quantity: float
    price: float
    status: str
    filled_quantity: float = 0.0
    timestamp: datetime = None
    timeout_minutes: int = 30
    last_check: datetime = None

    @property
    def is_timed_out(self) -> bool:
        if not self.timestamp:
            return False
        return datetime.utcnow() - self.timestamp > timedelta(minutes=self.timeout_minutes)

    @property
    def needs_status_check(self) -> bool:
        if not self.last_check:
            return True
        return datetime.utcnow() - self.last_check > timedelta(minutes=1)

class OrderTracker:
    def __init__(
        self, 
        ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/",
        callback: Callable = None,
        executor: Optional['OrderExecutor'] = None,
        status_check_interval: int = 60,
        cleanup_interval: int = 300,
        api_key: str = None,
        api_secret: str = None,
        api_passphrase: str = None
    ):
        self.callback = callback
        self.executor = executor
        self.status_check_interval = status_check_interval
        self.cleanup_interval = cleanup_interval
        self.active_orders: Dict[str, OrderStatus] = {}
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        # Initialize WebSocket client with our message callback
        self.ws_client = PolymarketWebSocketClient(
            api_key=api_key,
            api_secret=api_secret,
            api_passphrase=api_passphrase,
            message_callback=self.handle_ws_message,
            ws_url=ws_url
        )

    async def start(self):
        """Start the order tracker."""
        self.running = True
        self.tasks = [
            asyncio.create_task(self.ws_client.start("user")),  # Start WebSocket client in user channel
            asyncio.create_task(self._check_order_statuses()),
            asyncio.create_task(self._cleanup_orders())
        ]
        await asyncio.gather(*self.tasks)

    async def stop(self):
        """Stop tracking and cleanup."""
        self.running = False
        
        # Stop WebSocket client
        await self.ws_client.stop()
        
        # Cancel all tasks
        for task in self.tasks:
            try:
                task.cancel()
            except Exception:
                pass
        
        # Cancel all active orders
        for order_id in list(self.active_orders.keys()):
            await self.cancel_order(order_id)

    async def _check_order_statuses(self):
        """Periodically check status of active orders via REST API as a backup."""
        while self.running:
            try:
                for order_id, order in list(self.active_orders.items()):
                    if order.needs_status_check and self.executor:
                        status = await self.executor.get_order_status(order_id)
                        if status:
                            await self.update_order_status(order_id, status)
                        order.last_check = datetime.utcnow()
            except Exception as e:
                logging.error(f"Error checking order statuses: {e}")
            
            await asyncio.sleep(self.status_check_interval)

    async def _cleanup_orders(self):
        """Periodically clean up timed out orders."""
        while self.running:
            try:
                for order_id, order in list(self.active_orders.items()):
                    if order.is_timed_out:
                        logging.warning(f"Order {order_id} timed out after {order.timeout_minutes} minutes")
                        await self.cancel_order(order_id)
            except Exception as e:
                logging.error(f"Error during order cleanup: {e}")
            
            await asyncio.sleep(self.cleanup_interval)

    async def track_order(
        self, 
        order_id: str, 
        token_id: str, 
        side: str, 
        quantity: float, 
        price: float,
        timeout_minutes: int = 30
    ):
        """Start tracking a new order with optional timeout."""
        self.active_orders[order_id] = OrderStatus(
            order_id=order_id,
            token_id=token_id,
            side=side,
            quantity=quantity,
            price=price,
            status="pending",
            timestamp=datetime.utcnow(),
            timeout_minutes=timeout_minutes
        )
        logging.info(f"Started tracking order {order_id} with {timeout_minutes} minute timeout")

    async def cancel_order(self, order_id: str):
        """Cancel an order and remove it from tracking."""
        if order_id in self.active_orders:
            if self.executor:
                try:
                    await self.executor.cancel_order(order_id)
                    logging.info(f"Cancelled order {order_id}")
                except Exception as e:
                    logging.error(f"Error cancelling order {order_id}: {e}")
            
            del self.active_orders[order_id]

    async def update_order_status(self, order_id: str, status_update: dict):
        """Update order status from external source."""
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
            new_status = status_update.get("status")
            filled_quantity = float(status_update.get("filledQuantity", 0))
            
            order.status = new_status
            order.filled_quantity = filled_quantity
            
            await self._handle_status_update(order)

    async def _handle_status_update(self, order: OrderStatus):
        """Handle order status updates."""
        logging.info(f"Order {order.order_id} update: status={order.status}, filled={order.filled_quantity}")
        
        if order.status == "filled" or order.filled_quantity >= order.quantity:
            if self.callback:
                await self.callback(order)
            del self.active_orders[order.order_id]
            logging.info(f"Order {order.order_id} completed and removed from tracking")
        
        elif order.status == "cancelled":
            del self.active_orders[order.order_id]
            logging.info(f"Order {order.order_id} cancelled and removed from tracking")

    async def handle_ws_message(self, message):
        """Handle WebSocket messages from Polymarket."""
        try:
            if isinstance(message, list):
                for msg in message:
                    await self._process_ws_message(msg)
            else:
                await self._process_ws_message(message)
        except Exception as e:
            logging.error(f"Error handling WebSocket message: {e}")

    async def _process_ws_message(self, msg):
        """Process a single WebSocket message."""
        event_type = msg.get("event_type")
        
        if event_type == "trade":
            await self._handle_trade_message(msg)
        elif event_type == "order":
            await self._handle_order_message(msg)

    async def _handle_trade_message(self, message: dict):
        """Handle trade messages which indicate orders being filled."""
        maker_orders = message.get('maker_orders', [])
        
        for maker_order in maker_orders:
            order_id = maker_order.get('order_id')
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                filled_amount = float(maker_order.get('matched_amount', 0))
                price = float(maker_order.get('price', 0))
                
                order.filled_quantity += filled_amount
                order.status = "matched"
                
                logging.info(f"Order {order_id} matched: {filled_amount} at {price}")
                
                if order.filled_quantity >= order.quantity:
                    if self.callback:
                        await self.callback(order)
                    del self.active_orders[order_id]
                    logging.info(f"Order {order_id} fully filled and removed from tracking")

    async def _handle_order_message(self, message: dict):
        """Handle order status update messages."""
        action = message.get('action')
        order_id = message.get('order_id')
        
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
            
            if action == "PLACEMENT":
                order.status = "live"
                logging.info(f"Order {order_id} placed successfully")
                
            elif action == "UPDATE":
                new_filled = float(message.get('matched_amount', 0))
                if new_filled > order.filled_quantity:
                    order.filled_quantity = new_filled
                    logging.info(f"Order {order_id} updated: {order.filled_quantity}/{order.quantity} filled")
                
                if order.filled_quantity >= order.quantity:
                    if self.callback:
                        await self.callback(order)
                    del self.active_orders[order_id]
                    logging.info(f"Order {order_id} fully filled and removed from tracking")
                    
            elif action == "CANCELLATION":
                order.status = "cancelled"
                if self.callback:
                    await self.callback(order)
                del self.active_orders[order_id]
                logging.info(f"Order {order_id} cancelled and removed from tracking")

    # Utility methods for getting order information
    def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """Get current status of an order."""
        return self.active_orders.get(order_id)

    def get_active_orders(self) -> List[OrderStatus]:
        """Get list of all active orders."""
        return list(self.active_orders.values())

    def get_active_orders_for_token(self, token_id: str) -> List[OrderStatus]:
        """Get all active orders for a specific token."""
        return [order for order in self.active_orders.values() if order.token_id == token_id]

    def get_total_exposure(self, token_id: str) -> float:
        """Calculate total exposure (quantity * price) for a token."""
        return sum(
            order.quantity * order.price 
            for order in self.active_orders.values() 
            if order.token_id == token_id
        ) 