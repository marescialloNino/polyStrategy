import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.execution.order_tracker import OrderTracker, OrderStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Load API credentials from .env file
load_dotenv()

API_KEY = os.getenv("POLYMARKET_API_KEY")
API_SECRET = os.getenv("POLYMARKET_API_SECRET")
API_PASSPHRASE = os.getenv("POLYMARKET_API_PASSPHRASE")

# Mock token IDs for testing
TOKEN1_ID = "62697312879578878537492465609249634498018844363287127652537828808816942160117"
TOKEN2_ID = "58869207313910862764544355046372409163802584381615059274538220105674199390869"

class MockOrderExecutor:
    """Simple mock order executor for testing OrderTracker"""
    
    def __init__(self):
        self.orders = {}
    
    async def execute_signal(self, signal):
        """Simulate executing an order"""
        order_id = str(uuid.uuid4())
        self.orders[order_id] = {
            "orderId": order_id,
            "token_id": signal["token_id"],
            "side": signal["side"],
            "quantity": signal["quantity"],
            "price": signal["price"],
            "status": "live",
            "filledQuantity": 0
        }
        logging.info(f"Created mock order {order_id}: {signal}")
        return {"orderId": order_id, "status": "live"}
    
    async def get_order_status(self, order_id):
        """Get status of a mock order"""
        return self.orders.get(order_id)
    
    async def cancel_order(self, order_id):
        """Cancel a mock order"""
        if order_id in self.orders:
            self.orders[order_id]["status"] = "cancelled"
            logging.info(f"Cancelled mock order {order_id}")
            return True
        return False

async def handle_order_filled(order: OrderStatus):
    """Callback for when an order is filled"""
    logging.info(f"Order filled callback: {order.order_id}, {order.token_id}, {order.filled_quantity} at {order.price}")

async def simulate_order_updates(executor, tracker):
    """Simulate order updates that would normally come from WebSocket"""
    await asyncio.sleep(10)  # Wait for WebSocket connection to establish
    
    # Place a buy order for TOKEN1
    signal1 = {
        "token_id": TOKEN1_ID,
        "side": "BUY",
        "quantity": 2.0,
        "price": 0.5,
        "order_type": "limit"
    }
    
    # Execute order and track it
    response1 = await executor.execute_signal(signal1)
    order_id1 = response1["orderId"]
    await tracker.track_order(
        order_id=order_id1,
        token_id=signal1["token_id"],
        side=signal1["side"],
        quantity=signal1["quantity"],
        price=signal1["price"],
        timeout_minutes=5  # Short timeout for testing
    )
    
    # Wait a bit before simulating a partial fill
    await asyncio.sleep(5)
    
    # Simulate a partial fill message that would come from WebSocket
    partial_fill_message = [{
        "event_type": "trade",
        "maker_orders": [{
            "order_id": order_id1,
            "matched_amount": 1.0,
            "price": 0.5
        }]
    }]
    
    await tracker.handle_ws_message(partial_fill_message)
    
    # Wait a bit before simulating a complete fill
    await asyncio.sleep(5)
    
    # Simulate a complete fill message
    complete_fill_message = [{
        "event_type": "trade",
        "maker_orders": [{
            "order_id": order_id1,
            "matched_amount": 1.0,
            "price": 0.5
        }]
    }]
    
    await tracker.handle_ws_message(complete_fill_message)
    
    # Place a sell order for TOKEN2
    signal2 = {
        "token_id": TOKEN2_ID,
        "side": "SELL",
        "quantity": 1.5,
        "price": 0.6,
        "order_type": "limit"
    }
    
    # Execute order and track it
    response2 = await executor.execute_signal(signal2)
    order_id2 = response2["orderId"]
    await tracker.track_order(
        order_id=order_id2,
        token_id=signal2["token_id"],
        side=signal2["side"],
        quantity=signal2["quantity"],
        price=signal2["price"],
        timeout_minutes=5
    )
    
    # Wait a bit before simulating a cancellation
    await asyncio.sleep(5)
    
    # Simulate a cancellation message
    cancel_message = [{
        "event_type": "order",
        "action": "CANCELLATION",
        "order_id": order_id2
    }]
    
    await tracker.handle_ws_message(cancel_message)
    
    # Keep the test running to see timeout handling
    await asyncio.sleep(20)

async def test_order_tracker():
    """Test the OrderTracker with simulated orders"""
    executor = MockOrderExecutor()
    
    tracker = OrderTracker(
        callback=handle_order_filled,
        executor=executor,
        status_check_interval=5,  # Short interval for testing
        cleanup_interval=10,      # Short interval for testing
        api_key=API_KEY,
        api_secret=API_SECRET,
        api_passphrase=API_PASSPHRASE
    )
    
    logging.info("Starting OrderTracker and running simulations...")
    
    # Start the tracker and simulation concurrently
    simulation_task = asyncio.create_task(simulate_order_updates(executor, tracker))
    tracker_task = asyncio.create_task(tracker.start())
    
    try:
        # Let the simulation run to completion
        await simulation_task
        
        # Keep the tracker running for a bit longer to see final logs
        await asyncio.sleep(10)
    finally:
        # Stop the tracker
        await tracker.stop()
        tracker_task.cancel()
        
        logging.info("OrderTracker test completed")

if __name__ == "__main__":
    asyncio.run(test_order_tracker()) 