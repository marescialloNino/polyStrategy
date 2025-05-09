# src/bot_runner.py
import asyncio
import csv
import os
from src.data_streamer.data_streamer import MarketDataStreamer
from src.strategy.trade_dips_strategy import TradeDipsStrategy
from src.execution.order_executor import OrderExecutor
from src.execution.order_tracker import OrderTracker, OrderStatus
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

class TradingBot:
    def __init__(
        self,
        market_slug: str,
        token1_id: str,
        token2_id: str,
        interval_seconds: int = 90,
        max_trades: int = 2,
        initial_cash: float = 2.0,
        buy_threshold: float = -0.04,
        sell_threshold: float = 0.04,
        ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/",
        api_key: str = None,
        api_secret: str = None,
        api_passphrase: str = None
    ):
        self.market_slug = market_slug
        self.token1_id = token1_id
        self.token2_id = token2_id
        self.interval_seconds = interval_seconds
        self.max_trades = max_trades
        self.initial_cash = initial_cash
        
        # Configuration for WebSocket
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        
        self.streamer = MarketDataStreamer(
            slug=market_slug,
            token1=token1_id,
            token2=token2_id,
            interval_seconds=interval_seconds
        )
        self.strategy = TradeDipsStrategy(
            token1_id=token1_id,
            token2_id=token2_id,
            buy_threshold=buy_threshold,
            sell_threshold=sell_threshold,
            initial_cash=initial_cash,
            max_trades=max_trades
        )
        self.executor = OrderExecutor()
        self.csv_file = os.path.join(os.getcwd(), market_slug, f"{market_slug}_combined.csv")
        self.last_row_count = 0
        self.open_trades = 0
        
        # Use the proper OrderTracker with your existing PolymarketWebSocketClient
        self.order_tracker = OrderTracker(
            callback=self.handle_order_filled,
            executor=self.executor,
            status_check_interval=10,
            cleanup_interval=300,
            ws_url=ws_url,
            api_key=api_key,
            api_secret=api_secret,
            api_passphrase=api_passphrase
        )

    async def stream_data(self):
        logging.info(f"Starting data stream for market {self.market_slug}")
        await self.streamer.stream()

    async def process_csv(self):
        logging.info(f"Processing CSV at {self.csv_file}")
        while True:
            if not os.path.exists(self.csv_file):
                logging.info(f"CSV file {self.csv_file} not found, waiting...")
                await asyncio.sleep(10)
                continue

            with open(self.csv_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                new_rows = rows[self.last_row_count:]

                if not new_rows:
                    logging.info("No new rows to process")
                    await asyncio.sleep(10)
                    continue

                logging.info(f"Processing {len(new_rows)} new rows")
                for row in new_rows:
                    try:
                        cleaned_row = {
                            "timestamp": row["timestamp"],
                            self.token1_id: float(row["token1_midpoint"]),
                            self.token2_id: float(row["token2_midpoint"])
                        }
                        logging.info(f"Processing row: {cleaned_row}")
                        self.strategy.update_data(cleaned_row)

                        signal = self.strategy.generate_signal()
                        if signal:
                            if signal["side"] == "BUY":
                                if self.open_trades < self.max_trades and self.strategy.cash >= self.strategy.order_value:
                                    response = self.executor.execute_signal(signal)
                                    if response and response.get("status") == "live":
                                        # Start tracking the order
                                        await self.order_tracker.track_order(
                                            order_id=response["orderId"],
                                            token_id=signal["token_id"],
                                            side=signal["side"],
                                            quantity=signal["quantity"],
                                            price=signal["price"],
                                            timeout_minutes=45
                                        )
                                        self.open_trades += 1
                                        logging.info(f"Limit order placed and tracking started: {signal}")
                                    else:
                                        logging.error(f"Limit order failed: {signal}, Response: {response}")
                                else:
                                    logging.info(f"Buy signal ignored: Max trades ({self.max_trades}) or insufficient cash ({self.strategy.cash})")
                            elif signal["side"] == "SELL" and self.open_trades > 0:
                                response = self.executor.execute_signal(signal)
                                if response and response.get("status") == "live":
                                    # Start tracking the sell order
                                    await self.order_tracker.track_order(
                                        order_id=response["orderId"],
                                        token_id=signal["token_id"],
                                        side=signal["side"],
                                        quantity=signal["quantity"],
                                        price=signal["price"],
                                        timeout_minutes=45
                                    )
                                    logging.info(f"Sell limit order placed and tracking started: {signal}")
                                else:
                                    logging.error(f"Sell limit order failed: {signal}, Response: {response}")
                    except Exception as e:
                        logging.error(f"Error processing row {row}: {e}")

                self.last_row_count = len(rows)

            await asyncio.sleep(1)

    async def handle_order_filled(self, order: OrderStatus):
        """Handle completed order callback from OrderTracker."""
        if order.side == "BUY":
            self.strategy.record_buy(
                price=order.price,
                shares=order.filled_quantity,
                cash_value=order.filled_quantity * order.price
            )
            logging.info(f"Buy order filled: {order.filled_quantity} shares at {order.price}")
        else:  # SELL
            self.open_trades -= 1
            logging.info(f"Sell order filled: {order.filled_quantity} shares at {order.price}")

    async def run(self):
        """Run the trading bot with order tracking."""
        await asyncio.gather(
            self.stream_data(),
            self.process_csv(),
            self.order_tracker.start()
        )

    async def place_order(self, signal: dict):
        response = self.executor.execute_signal(signal)
        if response and response.get("status") == "live":
            await self.order_tracker.track_order(
                order_id=response["orderId"],
                token_id=signal["token_id"],
                side=signal["side"],
                quantity=signal["quantity"],
                price=signal["price"],
                timeout_minutes=45
            )
            return True
        return False

if __name__ == "__main__":
    bot = TradingBot(
        market_slug="celtics-nets",  # Replace with a real game slug
        token1_id="62697312879578878537492465609249634498018844363287127652537828808816942160117",
        token2_id="58869207313910862764544355046372409163802584381615059274538220105674199390869",
        interval_seconds=60,
        max_trades=4,
        initial_cash=4.0,
        buy_threshold=-0.05,
        sell_threshold=0.05
    )
    asyncio.run(bot.run())