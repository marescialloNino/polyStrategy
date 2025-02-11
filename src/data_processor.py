# src/data_processor.py
import pandas as pd

class DataProcessor:
    def __init__(self):
        self.order_book_data = pd.DataFrame()
        self.trades_data = pd.DataFrame()

    def process_order_book(self, order_book):
        """Process and store order book data."""
        # Example: Convert order book to a DataFrame
        self.order_book_data = pd.DataFrame(order_book)

    def process_trades(self, trades):
        """Process and store trade data."""
        # Example: Convert trades to a DataFrame
        self.trades_data = pd.DataFrame(trades)