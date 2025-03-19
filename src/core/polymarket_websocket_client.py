import json
import asyncio
import websockets
import logging
from typing import Callable, Optional, List

class PolymarketWebSocketClient:
    """
    Client for Polymarket WebSocket API handling authentication and message handling.
    This is separated from order tracking to create a cleaner separation of concerns.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_passphrase: Optional[str] = None,
        message_callback: Optional[Callable] = None,
        ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/"
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.websocket_url = ws_url
        self.connection = None
        self.running = False
        self.message_callback = message_callback
        self.task = None
    
    async def connect(self, channel_type: str):
        """Establishes a connection to the WebSocket."""
        try:
            logging.info('Trying to establish WebSocket connection')
            self.connection = await websockets.connect(f"{self.websocket_url}{channel_type}")
            logging.info(f"Connected to WebSocket on channel {channel_type}")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to WebSocket: {e}")
            self.connection = None
            return False
    
    async def subscribe(self, channel_type: str, markets: List[str] = None, assets_ids: List[str] = None):
        """
        Subscribes to a specified channel.

        Args:
            channel_type: 'user' or 'market'
            markets: List of market condition IDs ONLY for user channel
            assets_ids: List of asset IDs ONLY for market channel
        """
        if not self.connection:
            logging.warning("No WebSocket connection established. Cannot subscribe.")
            return False

        if channel_type not in ["user", "market"]:
            raise ValueError("Invalid channel type. Use 'user' or 'market'.")

        subscribe_message = {
            "type": channel_type,
        }

        if channel_type == "user" and self.api_key and self.api_secret and self.api_passphrase:
            subscribe_message["auth"] = {
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "passphrase": self.api_passphrase,
            }
            subscribe_message["markets"] = markets or []

        if channel_type == "market":
            subscribe_message["assets_ids"] = assets_ids or []

        try:
            await self.connection.send(json.dumps(subscribe_message))
            logging.info(f"Subscribed to {channel_type} channel")
            return True
        except Exception as e:
            logging.error(f"Subscription error: {e}")
            return False
    
    async def listen(self, channel_type: str, markets: List[str] = None, assets_ids: List[str] = None):
        """Listens for incoming messages from the WebSocket."""
        while self.running:
            try:
                async for message in self.connection:
                    data = json.loads(message)
                    await self.handle_message(data)
            except websockets.exceptions.ConnectionClosed as e:
                logging.warning(f"WebSocket connection closed: {e}")
                if self.running:
                    await self.reconnect(channel_type, markets, assets_ids)
            except Exception as e:
                logging.error(f"Error in WebSocket listener: {e}")
                if self.running:
                    await asyncio.sleep(2)
                    await self.reconnect(channel_type, markets, assets_ids)
    
    async def reconnect(self, channel_type: str, markets: List[str] = None, assets_ids: List[str] = None):
        """Attempts to reconnect to the WebSocket after an unexpected closure."""
        logging.info("Attempting to reconnect WebSocket...")
        retry_count = 0
        max_retries = 5
        delay = 1

        while self.running and retry_count < max_retries:
            await asyncio.sleep(delay)
            retry_count += 1
            delay = min(delay * 2, 30)  # Exponential backoff with max 30 seconds

            if await self.connect(channel_type):
                if await self.subscribe(channel_type, markets, assets_ids):
                    logging.info(f"Successfully reconnected after {retry_count} attempts")
                    return True
        
        logging.error(f"Failed to reconnect after {max_retries} attempts")
        return False
    
    async def handle_message(self, message):
        """
        Handles incoming WebSocket messages.

        Args:
            message: Parsed JSON message
        """
        try:
            if self.message_callback:
                # If a callback is set, use it for message handling
                await self.message_callback(message)
                return
                
            # Default handling if no callback is provided
            for msg in message:
                event_type = msg.get("event_type")
                if event_type:
                    logging.debug(f"Received {event_type} message")
                else:
                    logging.debug(f"Received message with no event_type: {msg}")
        except Exception as e:
            logging.error(f"Error handling WebSocket message: {e}")
    
    async def stop(self):
        """Stops the WebSocket client."""
        self.running = False
        await self.close()
        if self.task:
            try:
                self.task.cancel()
            except Exception:
                pass
    
    async def close(self):
        """Closes the WebSocket connection."""
        if self.connection:
            try:
                await self.connection.close()
                logging.info("WebSocket connection closed")
            except Exception as e:
                logging.error(f"Error closing WebSocket: {e}")
            self.connection = None
    
    async def keep_alive(self, interval: int = 30):
        """Send ping messages to keep the connection alive."""
        while self.running and self.connection:
            try:
                await self.connection.ping()
                logging.debug("WebSocket ping sent to keep connection alive")
            except Exception as e:
                logging.error(f"Error during WebSocket keep-alive: {e}")
                break
            await asyncio.sleep(interval)
    
    async def start(self, channel_type: str = "user", markets: List[str] = None, asset_ids: List[str] = None):
        """Start the WebSocket client and return the running task."""
        self.running = True
        self.task = asyncio.create_task(self._run(channel_type, markets, asset_ids))
        return self.task
    
    async def _run(self, channel_type: str, markets: List[str] = None, asset_ids: List[str] = None):
        """Run the WebSocket client with automatic reconnection."""
        keep_alive_task = None
        
        try:
            if await self.connect(channel_type):
                if await self.subscribe(channel_type, markets, asset_ids):
                    # Start the keep-alive task
                    keep_alive_task = asyncio.create_task(self.keep_alive())
                    # Main listen loop
                    await self.listen(channel_type, markets, asset_ids)
        except Exception as e:
            logging.error(f"Error in WebSocket client: {e}")
        finally:
            self.running = False
            if keep_alive_task:
                keep_alive_task.cancel()
            await self.close() 