import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.polymarket_websocket_client import PolymarketWebSocketClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Load API credentials from .env file (highly recommended for security)
load_dotenv()

API_KEY = os.getenv("POLYMARKET_API_KEY")
API_SECRET = os.getenv("POLYMARKET_API_SECRET")
API_PASSPHRASE = os.getenv("POLYMARKET_API_PASSPHRASE")

async def message_handler(message):
    """Simple message handler to print received messages"""
    if isinstance(message, list):
        for msg in message:
            event_type = msg.get("event_type")
            if event_type:
                logging.info(f"Received {event_type} message: {msg}")
    else:
        logging.info(f"Received message: {message}")

async def test_websocket_connection():
    """Test basic WebSocket connection and authentication"""
    ws_client = PolymarketWebSocketClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        api_passphrase=API_PASSPHRASE,
        message_callback=message_handler
    )
    
    logging.info("Starting WebSocket client...")
    
    # Start the WebSocket client task
    task = await ws_client.start("user")
    
    try:
        # Keep the script running for 60 seconds
        logging.info("WebSocket connection established, listening for 60 seconds...")
        await asyncio.sleep(60)
    finally:
        # Stop the WebSocket client
        await ws_client.stop()
        logging.info("WebSocket client stopped")

if __name__ == "__main__":
    asyncio.run(test_websocket_connection()) 