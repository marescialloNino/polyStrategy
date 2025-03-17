# src/test_strategy_on_csv.py
import csv
import pandas as pd
from src.strategy.trade_dips_strategy import TradeDipsStrategy
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def run_strategy_on_csv(csv_path: str, token1_id: str, token2_id: str, buy_threshold: float = -0.01, sell_threshold: float = 0.01):
    # Initialize strategy
    strategy = TradeDipsStrategy(
        token1_id=token1_id,
        token2_id=token2_id,
        buy_threshold=buy_threshold,
        sell_threshold=sell_threshold,
        initial_cash=5.0,
        shares_per_buy=1.0  # Use $1 worth of tokens for simplicity
    )

    # Read CSV
    if not os.path.exists(csv_path):
        logging.error(f"CSV file not found at {csv_path}")
        return

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

        if not rows:
            logging.error("CSV file is empty")
            return

        logging.info(f"Loaded {len(rows)} rows from {csv_path}")

        # Process each row
        for row in rows:
            try:
                cleaned_row = {
                    "timestamp": row["timestamp"],
                    token1_id: float(row["token1_midpoint"]),
                    token2_id: float(row["token2_midpoint"])
                }
                logging.info(f"Processing row: {cleaned_row}")
                strategy.update_data(cleaned_row)

                # Generate signal
                signal = strategy.generate_signal()
                if signal:
                    current_price = cleaned_row[signal["token_id"]]
                    signal["quantity"] = min(1.0 / current_price, strategy.shares_per_buy)  # $1 worth
                    logging.info(f"Signal generated: {signal}")
            except Exception as e:
                logging.error(f"Error processing row {row}: {e}")

if __name__ == "__main__":
    # Adjust these to match your setup
    csv_path = os.path.join(os.getcwd(), "capitals-sharks", "capitals-sharks_combined.csv")
    token1_id = "40465031556608279901803453704591823162810651299818097010002629371896228132129"
    token2_id = "14317864523760696750903003863584839450566845793471157093404300778050229017704"

    run_strategy_on_csv(
        csv_path=csv_path,
        token1_id=token1_id,
        token2_id=token2_id,
        buy_threshold=-0.01,  # -1%
        sell_threshold=0.01   # +1%
    )