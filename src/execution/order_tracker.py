import asyncio
import json
import websockets
import logging
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

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
    timeout_minutes: int = 30  # Default timeout of 30 minutes
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
        return datetime.utcnow() - self.last_check > timedelta(minutes=1)  # Check every minute

class OrderTracker:
    def __init__(
        self, 
        ws_url: str, 
        callback: Callable = None,
        executor: Optional['OrderExecutor'] = None,  # Reference to executor for cancelling orders
        status_check_interval: int = 60,  # Seconds between status checks
        cleanup_interval: int = 300,  # Seconds between cleanup runs
    ):
        self.ws_url = ws_url
        self.callback = callback
        self.executor = executor
        self.status_check_interval = status_check_interval
        self.cleanup_interval = cleanup_interval
        self.active_orders: Dict[str, OrderStatus] = {}
        self.ws = None
        self.running = False
        self.tasks: List[asyncio.Task] = []

    async def start(self):
        """Start the WebSocket connection and maintenance tasks."""
        self.running = True
        self.tasks = [
            asyncio.create_task(self._run_websocket()),
            asyncio.create_task(self._check_order_statuses()),
            asyncio.create_task(self._cleanup_orders())
        ]
        await asyncio.gather(*self.tasks)

    async def stop(self):
        """Stop all tracking and cleanup."""
        self.running = False
        if self.ws:
            await self.ws.close()
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Cancel all active orders
        for order_id in list(self.active_orders.keys()):
            await self.cancel_order(order_id)

    async def _run_websocket(self):
        """Main WebSocket connection loop."""
        while self.running:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    self.ws = websocket
                    await self.subscribe_to_orders()
                    
                    while self.running:
                        message = await websocket.recv()
                        await self.handle_message(json.loads(message))
                        
            except websockets.exceptions.ConnectionClosed:
                logging.error("WebSocket connection closed. Reconnecting...")
                await asyncio.sleep(5)
            except Exception as e:
                logging.error(f"WebSocket error: {e}")
                await asyncio.sleep(5)

    async def _check_order_statuses(self):
        """Periodically check status of active orders."""
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

    async def subscribe_to_orders(self):
        """Subscribe to order updates on the WebSocket."""
        subscribe_message = {
            "type": "subscribe",
            "channel": "orders"
        }
        await self.ws.send(json.dumps(subscribe_message))
    
    async def handle_message(self, message: dict):
        """
        Handle incoming WebSocket messages.
        
        Args:
            message: Parsed WebSocket message
        """
        if message.get("type") == "order_update":
            order_id = message.get("orderId")
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                
                # Update order status
                new_status = message.get("status")
                filled_quantity = float(message.get("filledQuantity", 0))
                order.status = new_status
                order.filled_quantity = filled_quantity
                
                logging.info(f"Order {order_id} update: status={new_status}, filled={filled_quantity}")
                
                # Check if order is completely filled
                if new_status == "filled" or filled_quantity >= order.quantity:
                    if self.callback:
                        await self.callback(order)
                    del self.active_orders[order_id]
                    logging.info(f"Order {order_id} completed and removed from tracking")
                
                # Check if order is cancelled
                elif new_status == "cancelled":
                    del self.active_orders[order_id]
                    logging.info(f"Order {order_id} cancelled and removed from tracking") 