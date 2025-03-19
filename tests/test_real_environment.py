import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.execution.order_tracker import OrderTracker, OrderStatus
from src.core.clob_client import PolymarketClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Load API credentials
load_dotenv()

API_KEY = os.getenv("POLYMARKET_API_KEY")
API_SECRET = os.getenv("POLYMARKET_API_SECRET")
API_PASSPHRASE = os.getenv("POLYMARKET_API_PASSPHRASE")

# Test market tokens
TOKEN1_ID = "43186308813322774389511655009441265359358460001746875331763940432725323754100"
TOKEN2_ID = "42475543248404210065990230898512565125915441850041772863138114442518722564349"

class SafeExecutor:
    """Real executor that connects to Polymarket but doesn't place actual orders"""
    
    def __init__(self):
        self.client = PolymarketClient()
        self.mock_orders = {}
    
    async def execute_signal(self, signal):
        """Simulate executing an order but get real market data"""
        order_id = str(uuid.uuid4())
        
        # Get real market data
        price = self.client.get_price(signal["token_id"], signal["side"])
        
        logging.info(f"Market price for {signal['token_id']} {signal['side']}: {price}")
        
        # Create mock order with real market data
        self.mock_orders[order_id] = {
            "orderId": order_id,
            "token_id": signal["token_id"],
            "side": signal["side"],
            "quantity": signal["quantity"],
            "price": signal["price"],
            "status": "live",
            "filledQuantity": 0,
            "market_price": price
        }
        
        logging.info(f"Created safe mock order {order_id}: {signal}")
        return {"orderId": order_id, "status": "live"}
    
    async def get_order_status(self, order_id):
        """Get status of a mock order"""
        return self.mock_orders.get(order_id)
    
    async def cancel_order(self, order_id):
        """Cancel a mock order"""
        if order_id in self.mock_orders:
            self.mock_orders[order_id]["status"] = "cancelled"
            logging.info(f"Cancelled mock order {order_id}")
            return True
        return False

async def handle_order_filled(order: OrderStatus):
    """Callback for when an order is filled"""
    logging.info(f"Order filled callback: {order.order_id}, {order.token_id}, {order.filled_quantity} at {order.price}")

async def test_real_environment():
    """Test with real market data but simulated orders"""
    executor = SafeExecutor()
    
    tracker = OrderTracker(
        callback=handle_order_filled,
        executor=executor,
        status_check_interval=10,
        cleanup_interval=30,
        api_key=API_KEY,
        api_secret=API_SECRET,
        api_passphrase=API_PASSPHRASE
    )
    
    logging.info("Starting OrderTracker in real environment...")
    
    # Start the tracker
    tracker_task = asyncio.create_task(tracker.start())
    
    try:
        # Get market data for the tokens
        token1_price = executor.client.get_midpoint_price(TOKEN1_ID)
        token2_price = executor.client.get_midpoint_price(TOKEN2_ID)
        
        logging.info(f"Token1 midpoint price: {token1_price}")
        logging.info(f"Token2 midpoint price: {token2_price}")
        
        # Place a mock buy order
        signal1 = {
            "token_id": TOKEN1_ID,
            "side": "BUY",
            "quantity": 2.0,
            "price": token1_price * 0.98 if token1_price else 0.5,  # Slightly below market
            "order_type": "limit"
        }
        
        response1 = await executor.execute_signal(signal1)
        order_id1 = response1["orderId"]
        
        await tracker.track_order(
            order_id=order_id1,
            token_id=signal1["token_id"],
            side=signal1["side"],
            quantity=signal1["quantity"],
            price=signal1["price"],
            timeout_minutes=2
        )
        
        # Let the order timeout naturally
        logging.info("Waiting for order timeout...")
        await asyncio.sleep(150)  # 2.5 minutes, should be enough to see timeout
        
    finally:
        # Stop the tracker
        await tracker.stop()
        tracker_task.cancel()
        
        logging.info("Real environment test completed")

if __name__ == "__main__":
    asyncio.run(test_real_environment()) 