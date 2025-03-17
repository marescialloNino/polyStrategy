# src/strategy/trade_dips_strategy.py
import numpy as np
import pandas as pd
from datetime import datetime
from .base_strategy import BaseStrategy
import logging

class TradeDipsStrategy(BaseStrategy):
    def __init__(self, token1_id: str, token2_id: str, buy_threshold: float, sell_threshold: float, 
                 initial_cash: float = 10.0, take_profit_pct: float = 0.5, stop_loss_pct: float = 0.25,
                 max_trades: int = 5):
        super().__init__()
        self.token1_id = token1_id
        self.token2_id = token2_id
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.initial_cash = initial_cash
        self.take_profit_pct = take_profit_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_trades = max_trades
        self.order_value = initial_cash / max_trades  # 2 EUR per trade with 10 EUR initial
        self.min_order_value = 1.0  # Polymarket minimum threshold
        self.selected_team = None
        self.cash = initial_cash
        self.buy_positions = []  # List of (price, shares, cash_value) tuples
        self.exited = False

    @staticmethod
    def compute_returns(series: pd.Series):
        returns = series.pct_change().fillna(0)
        return returns

    @staticmethod
    def compute_positions(returns: pd.Series, buy_threshold: float, sell_threshold: float):
        buy = np.where(returns < buy_threshold)[0]
        sell = np.where(returns > sell_threshold)[0]
        return buy, sell

    def calculate_shares_for_value(self, price: float) -> tuple[float, float]:
        """
        Calculate number of shares to buy/sell to match our target order value.
        Returns (shares, actual_value) tuple.
        """
        target_value = min(self.order_value, self.cash)
        if target_value < self.min_order_value:
            return 0.0, 0.0
            
        shares = target_value / price
        actual_value = shares * price
        return shares, actual_value

    def generate_signal(self) -> dict | None:
        if not self.data or len(self.data) < 2:
            logging.info(f"Not enough data yet: {len(self.data)} rows")
            return None
        
        df = pd.DataFrame(self.data)
        if 'timestamp' in df.columns and not np.issubdtype(df['timestamp'].dtype, np.datetime64):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        team1, team2 = self.token1_id, self.token2_id
        returns_team1 = self.compute_returns(df[f"{team1}_best_buy"])  # For buying, look at best sell price
        returns_team2 = self.compute_returns(df[f"{team2}_best_buy"])
        
        logging.info(f"Team1 returns: {returns_team1.iloc[-1]:.4f}, Team2 returns: {returns_team2.iloc[-1]:.4f}")
        
        buy_team1, sell_team1 = self.compute_positions(returns_team1, self.buy_threshold, self.sell_threshold)
        buy_team2, sell_team2 = self.compute_positions(returns_team2, self.buy_threshold, self.sell_threshold)
        
        current_index = df.index[-1]
        current_time = df['timestamp'].iloc[-1]
        current_prices = df.iloc[-1]
        
        signal = None
        
        if self.selected_team is None:
            if current_index in buy_team1 and self.cash >= self.min_order_value:
                buy_price = current_prices[f"{team1}_best_sell"]
                shares, actual_value = self.calculate_shares_for_value(buy_price)
                if shares > 0:
                    self.selected_team = team1
                    signal = {
                        "token_id": team1,
                        "order_type": "limit",
                        "side": "BUY",
                        "quantity": shares,
                        "price": buy_price
                    }
                    logging.info(f"Selected {team1} and generated BUY limit order for {shares:.4f} shares at {buy_price:.4f} (€{actual_value:.2f})")
            elif current_index in buy_team2 and self.cash >= self.min_order_value:
                buy_price = current_prices[f"{team2}_best_sell"]
                shares, actual_value = self.calculate_shares_for_value(buy_price)
                if shares > 0:
                    self.selected_team = team2
                    signal = {
                        "token_id": team2,
                        "order_type": "limit",
                        "side": "BUY",
                        "quantity": shares,
                        "price": buy_price
                    }
                    logging.info(f"Selected {team2} and generated BUY limit order for {shares:.4f} shares at {buy_price:.4f} (€{actual_value:.2f})")
        
        elif self.selected_team is not None:
            current_buy_price = current_prices[f"{self.selected_team}_best_buy"]
            current_sell_price = current_prices[f"{self.selected_team}_best_sell"]
            
            if self.selected_team == team1 and current_index in buy_team1 and self.cash >= self.min_order_value:
                shares, actual_value = self.calculate_shares_for_value(current_sell_price)
                if shares > 0:
                    signal = {
                        "token_id": team1,
                        "order_type": "limit",
                        "side": "BUY",
                        "quantity": shares,
                        "price": current_sell_price
                    }
                    logging.info(f"Generated BUY limit order for {shares:.4f} shares at {current_sell_price:.4f} (€{actual_value:.2f})")
            elif self.selected_team == team2 and current_index in buy_team2 and self.cash >= self.min_order_value:
                shares, actual_value = self.calculate_shares_for_value(current_sell_price)
                if shares > 0:
                    signal = {
                        "token_id": team2,
                        "order_type": "limit",
                        "side": "BUY",
                        "quantity": shares,
                        "price": current_sell_price
                    }
                    logging.info(f"Generated BUY limit order for {shares:.4f} shares at {current_sell_price:.4f} (€{actual_value:.2f})")
            elif self.selected_team == team1 and current_index in sell_team1 and self.buy_positions:
                lowest_buy = min(self.buy_positions, key=lambda x: x[0])
                buy_price, shares, cash_value = lowest_buy
                self.buy_positions.remove(lowest_buy)
                signal = {
                    "token_id": team1,
                    "order_type": "limit",
                    "side": "SELL",
                    "quantity": shares,
                    "price": current_buy_price
                }
                self.cash += shares * current_buy_price
                logging.info(f"Generated SELL limit order for {shares:.4f} shares at {current_buy_price:.4f}")
            elif self.selected_team == team2 and current_index in sell_team2 and self.buy_positions:
                lowest_buy = min(self.buy_positions, key=lambda x: x[0])
                buy_price, shares, cash_value = lowest_buy
                self.buy_positions.remove(lowest_buy)
                signal = {
                    "token_id": team2,
                    "order_type": "limit",
                    "side": "SELL",
                    "quantity": shares,
                    "price": current_buy_price
                }
                self.cash += shares * current_buy_price
                logging.info(f"Generated SELL limit order for {shares:.4f} shares at {current_buy_price:.4f}")
            
            # Take-profit or stop-loss
            position_value = sum(shares * current_buy_price for _, shares, _ in self.buy_positions)
            current_pnl = position_value + self.cash - self.initial_cash
            if current_pnl >= self.take_profit_pct * self.initial_cash and self.buy_positions:
                total_shares = sum(shares for _, shares, _ in self.buy_positions)
                signal = {
                    "token_id": self.selected_team,
                    "order_type": "limit",
                    "side": "SELL",
                    "quantity": total_shares,
                    "price": current_buy_price
                }
                self.cash += total_shares * current_buy_price
                self.buy_positions.clear()
                self.exited = True
                logging.info(f"Take-profit triggered for {self.selected_team}, selling {total_shares:.4f} shares at {current_buy_price:.4f}")
            elif current_pnl <= -self.stop_loss_pct * self.initial_cash and self.buy_positions:
                total_shares = sum(shares for _, shares, _ in self.buy_positions)
                signal = {
                    "token_id": self.selected_team,
                    "order_type": "limit",
                    "side": "SELL",
                    "quantity": total_shares,
                    "price": current_buy_price
                }
                self.cash += total_shares * current_buy_price
                self.buy_positions.clear()
                self.exited = True
                logging.info(f"Stop-loss triggered for {self.selected_team}, selling {total_shares:.4f} shares at {current_buy_price:.4f}")
        
        return signal

    def record_buy(self, price: float, shares: float, cash_value: float):
        """Record a buy after execution with actual shares from Polymarket."""
        if self.cash >= cash_value:
            self.buy_positions.append((price, shares, cash_value))
            self.cash -= cash_value
        else:
            logging.warning(f"Insufficient cash for buy: {cash_value} > {self.cash}")