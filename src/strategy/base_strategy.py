from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self):
        # We accumulate incoming market data (each row as a dict)
        self.data = []

    def update_data(self, row: dict):
        """
        Append a new data row to the strategy’s internal storage.
        """
        self.data.append(row)

    @abstractmethod
    def generate_signal(self) -> dict | None:
        """
        Process the accumulated data and return a trading signal if conditions are met.
        The signal should be a dictionary with keys like:
          { "token_id": str, "order_type": "limit" or "market", "side": "BUY" or "SELL",
            "price": float, "quantity": float }
        Return None if no signal is generated.
        """
        pass
