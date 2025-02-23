import numpy as np
import pandas as pd
from datetime import datetime
from strategy.base_strategy import BaseStrategy

class TradeDipsStrategy(BaseStrategy):
    def __init__(self, buy_threshold: float, sell_threshold: float, 
                 initial_cash: float = 500, shares_per_buy: int = 50, 
                 take_profit_pct: float = 0.5, stop_loss_pct: float = 0.25):
        
        super().__init__()
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.initial_cash = initial_cash
        self.shares_per_buy = shares_per_buy
        self.take_profit_pct = take_profit_pct
        self.stop_loss_pct = stop_loss_pct

        # Internal state variables
        self.selected_team = None  # Once a team triggers a buy signal, we lock in on it.
        self.shares = 0
        self.cash = initial_cash
        self.exited = False  # True if take-profit or stop-loss condition triggered

    @staticmethod
    def compute_returns(series: pd.Series):
        """Compute the percentage returns of a price series."""
        returns = series.pct_change().fillna(0)
        return returns

    @staticmethod
    def compute_positions(returns: pd.Series, buy_threshold: float, sell_threshold: float):
        """Generate indices for buy/sell signals based on returns and thresholds."""
        buy = np.where(returns < buy_threshold)[0]
        sell = np.where(returns > sell_threshold)[0]
        return buy, sell

    def generate_signal(self) -> dict | None:
        """
        Process the accumulated data (assumed to be a list of dicts, which we convert to a DataFrame)
        and generate a trading signal if conditions are met.
        """
        if not self.data:
            return None
        
        df = pd.DataFrame(self.data)
        
        # Ensure a timestamp column is present and parsed as datetime.
        if 'timestamp' in df.columns and not np.issubdtype(df['timestamp'].dtype, np.datetime64):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # For this strategy, assume that the last two non-timestamp columns represent team prices.
        columns = list(df.columns)
        if 'timestamp' in columns:
            columns.remove('timestamp')
        if len(columns) < 2:
            return None  # Not enough price data
        
        team1, team2 = columns[-2], columns[-1]
        
        # Compute returns for both teams.
        returns_team1 = self.compute_returns(df[team1])
        returns_team2 = self.compute_returns(df[team2])
        
        # Get indices where returns cross thresholds.
        buy_team1, sell_team1 = self.compute_positions(returns_team1, self.buy_threshold, self.sell_threshold)
        buy_team2, sell_team2 = self.compute_positions(returns_team2, self.buy_threshold, self.sell_threshold)
        
        # Use the last row of data as the “current” time.
        current_index = df.index[-1]
        current_time = df['timestamp'].iloc[-1] if 'timestamp' in df.columns else datetime.now()
        current_prices = df.iloc[-1]
        
        signal = None
        
        # If no team has yet been selected, check if a buy signal appears for either team.
        if self.selected_team is None:
            if current_index in buy_team1:
                self.selected_team = team1
                print(f"Selected Team: {team1} at {current_time}")
            elif current_index in buy_team2:
                self.selected_team = team2
                print(f"Selected Team: {team2} at {current_time}")
        
        if self.selected_team is not None:
            current_price = current_prices[self.selected_team]
            # Check for a buy signal on the selected team.
            if self.selected_team == team1 and current_index in buy_team1:
                total_cost = current_price * self.shares_per_buy
                if self.cash >= total_cost:
                    self.shares += self.shares_per_buy
                    self.cash -= total_cost
                    print(f"Bought {self.shares_per_buy} shares at {current_price} on {team1} at {current_time}")
                    signal = {
                        "token_id": team1,    # In practice, map this to a token ID.
                        "order_type": "limit",
                        "side": "BUY",
                        "price": current_price,
                        "quantity": self.shares_per_buy
                    }
            elif self.selected_team == team2 and current_index in buy_team2:
                total_cost = current_price * self.shares_per_buy
                if self.cash >= total_cost:
                    self.shares += self.shares_per_buy
                    self.cash -= total_cost
                    print(f"Bought {self.shares_per_buy} shares at {current_price} on {team2} at {current_time}")
                    signal = {
                        "token_id": team2,
                        "order_type": "limit",
                        "side": "BUY",
                        "price": current_price,
                        "quantity": self.shares_per_buy
                    }
            
            # Check for a sell signal (if shares are held).
            if self.selected_team == team1 and current_index in sell_team1 and self.shares > 0:
                print(f"Sell {self.shares} shares at {current_price} on {team1} at {current_time}")
                signal = {
                    "token_id": team1,
                    "order_type": "limit",
                    "side": "SELL",
                    "price": current_price,
                    "quantity": self.shares
                }
                self.cash += self.shares * current_price
                self.shares = 0
            elif self.selected_team == team2 and current_index in sell_team2 and self.shares > 0:
                print(f"Sell {self.shares} shares at {current_price} on {team2} at {current_time}")
                signal = {
                    "token_id": team2,
                    "order_type": "limit",
                    "side": "SELL",
                    "price": current_price,
                    "quantity": self.shares
                }
                self.cash += self.shares * current_price
                self.shares = 0
            
            # Check for take-profit or stop-loss conditions.
            position_value = self.shares * current_price
            current_pnl = position_value + self.cash - self.initial_cash
            if current_pnl >= self.take_profit_pct * self.initial_cash and self.shares > 0:
                print(f"Take-profit triggered at {current_time}: Sell all at {current_price}")
                signal = {
                    "token_id": self.selected_team,
                    "order_type": "limit",
                    "side": "SELL",
                    "price": current_price,
                    "quantity": self.shares
                }
                self.cash += self.shares * current_price
                self.shares = 0
                self.exited = True
            elif current_pnl <= -self.stop_loss_pct * self.initial_cash and self.shares > 0:
                print(f"Stop-loss triggered at {current_time}: Sell all at {current_price}")
                signal = {
                    "token_id": self.selected_team,
                    "order_type": "limit",
                    "side": "SELL",
                    "price": current_price,
                    "quantity": self.shares
                }
                self.cash += self.shares * current_price
                self.shares = 0
                self.exited = True
        
        return signal
