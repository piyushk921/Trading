"""
Event-driven backtesting simulator for options trading.

Simulates trading based on model signals with proper risk management.
"""

import numpy as np
import pandas as pd
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime

from ..modeling.models import Option2xModel
from ..modeling.dataset import prepare_dataset
from ..config import Config, get_config
from ..utils.time_utils import parse_timestamp, minutes_between
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class Trade:
    """Represents a single trade."""

    symbol: str
    entry_time: str
    entry_price: float
    exit_time: Optional[str] = None
    exit_price: Optional[float] = None
    target_price: float = 0.0
    stop_loss_price: float = 0.0
    position_size: float = 10000.0
    status: str = "open"  # open, closed, stopped
    exit_reason: str = ""  # target_hit, stop_loss, eod, max_holding

    def __post_init__(self):
        """Calculate target and stop loss prices."""
        if self.target_price == 0.0:
            self.target_price = self.entry_price * 2.0  # 2x target

        if self.stop_loss_price == 0.0:
            self.stop_loss_price = self.entry_price * 0.6  # -40% stop loss

    @property
    def pnl(self) -> float:
        """Calculate P&L for the trade."""
        if self.exit_price is None:
            return 0.0

        # P&L = (exit - entry) * position_size / entry_price
        return (self.exit_price - self.entry_price) * (self.position_size / self.entry_price)

    @property
    def return_pct(self) -> float:
        """Calculate return percentage."""
        if self.exit_price is None or self.entry_price == 0:
            return 0.0

        return (self.exit_price / self.entry_price - 1.0) * 100

    @property
    def is_winner(self) -> bool:
        """Check if trade hit target."""
        return self.exit_reason == "target_hit"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'entry_time': self.entry_time,
            'entry_price': self.entry_price,
            'exit_time': self.exit_time,
            'exit_price': self.exit_price,
            'target_price': self.target_price,
            'stop_loss_price': self.stop_loss_price,
            'position_size': self.position_size,
            'pnl': self.pnl,
            'return_pct': self.return_pct,
            'status': self.status,
            'exit_reason': self.exit_reason,
            'is_winner': self.is_winner,
        }


class BacktestSimulator:
    """
    Event-driven backtest simulator.

    Iterates through historical data chronologically and simulates trading.
    """

    def __init__(
        self,
        model: Option2xModel,
        config: Optional[Config] = None
    ):
        """
        Initialize backtest simulator.

        Args:
            model: Trained model for generating signals
            config: Configuration object
        """
        self.model = model
        self.config = config or get_config()
        self.bt_config = self.config.backtest
        self.signal_config = self.config.signals

        self.trades: List[Trade] = []
        self.open_positions: Dict[str, Trade] = {}

        logger.info("Backtest simulator initialized")

    def run(
        self,
        df: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Run backtest on historical data.

        Args:
            df: DataFrame with features (must have 'symbol', 'timestamp', 'price', etc.)
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            DataFrame with all trades
        """
        logger.info("=" * 80)
        logger.info("Starting backtest simulation")
        logger.info("=" * 80)

        # Filter by date if specified
        if start_date:
            df = df[df['timestamp'] >= start_date].copy()
        if end_date:
            df = df[df['timestamp'] <= end_date].copy()

        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)

        logger.info(f"Backtesting on {len(df)} snapshots")
        logger.info(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

        # Prepare features
        X, y_true, feature_names = prepare_dataset(df, self.config)

        # Get model predictions
        logger.info("Generating model predictions...")
        y_proba = self.model.predict_proba(X)[:, 1]
        df['pred_proba'] = y_proba

        # Event loop: iterate through each snapshot
        logger.info("Running event-driven simulation...")
        for idx in range(len(df)):
            row = df.iloc[idx]
            self._process_snapshot(row, df, idx)

        # Close any remaining open positions at end
        self._close_all_positions(df.iloc[-1], reason="backtest_end")

        logger.info(f"Backtest complete. Total trades: {len(self.trades)}")

        # Convert trades to DataFrame
        if self.trades:
            trades_df = pd.DataFrame([trade.to_dict() for trade in self.trades])
        else:
            trades_df = pd.DataFrame()

        return trades_df

    def _process_snapshot(
        self,
        row: pd.Series,
        df_full: pd.DataFrame,
        current_idx: int
    ) -> None:
        """
        Process a single snapshot (event).

        Args:
            row: Current snapshot row
            df_full: Full DataFrame (for lookahead to update trades)
            current_idx: Current index in df_full
        """
        current_time = row['timestamp']
        symbol = row['symbol']

        # 1. Update existing positions for this symbol
        if symbol in self.open_positions:
            self._update_position(row, df_full, current_idx)

        # 2. Check for new entry signal
        else:
            self._check_entry_signal(row)

    def _check_entry_signal(self, row: pd.Series) -> None:
        """Check if current snapshot generates an entry signal."""
        # Apply signal filters
        if not self._passes_filters(row):
            return

        # Check probability threshold
        if row['pred_proba'] < self.signal_config.prob_threshold:
            return

        # Check position limits
        if len(self.open_positions) >= self.bt_config.max_positions:
            return

        # Enter trade
        trade = Trade(
            symbol=row['symbol'],
            entry_time=row['timestamp'],
            entry_price=self._get_entry_price(row),
            position_size=self.bt_config.position_size_fixed,
        )

        self.open_positions[row['symbol']] = trade
        logger.debug(f"Entered trade: {row['symbol']} at {trade.entry_price:.2f}")

    def _update_position(
        self,
        row: pd.Series,
        df_full: pd.DataFrame,
        current_idx: int
    ) -> None:
        """Update an existing open position."""
        symbol = row['symbol']
        trade = self.open_positions[symbol]

        current_price = self._get_current_price(row)
        current_time = row['timestamp']

        # Check exit conditions
        exit_reason = None

        # 1. Target hit
        if current_price >= trade.target_price:
            exit_reason = "target_hit"
            exit_price = trade.target_price  # Assume we got out at target

        # 2. Stop loss hit
        elif current_price <= trade.stop_loss_price:
            exit_reason = "stop_loss"
            exit_price = trade.stop_loss_price

        # 3. Max holding period
        elif self.bt_config.max_holding_minutes:
            entry_dt = parse_timestamp(trade.entry_time)
            current_dt = parse_timestamp(current_time)
            minutes_held = minutes_between(entry_dt, current_dt)

            if minutes_held >= self.bt_config.max_holding_minutes:
                exit_reason = "max_holding"
                exit_price = current_price

        # 4. End of day (check if this is last snapshot for the symbol today)
        # Simple heuristic: if this is the last row for this symbol
        symbol_rows = df_full[df_full['symbol'] == symbol]
        if current_idx == symbol_rows.index[-1]:
            exit_reason = "eod"
            exit_price = current_price

        # Close position if exit condition met
        if exit_reason:
            self._close_position(trade, exit_price, current_time, exit_reason)

    def _close_position(
        self,
        trade: Trade,
        exit_price: float,
        exit_time: str,
        exit_reason: str
    ) -> None:
        """Close an open position."""
        trade.exit_price = exit_price
        trade.exit_time = exit_time
        trade.exit_reason = exit_reason
        trade.status = "closed"

        # Apply slippage
        if self.bt_config.slippage_bps > 0:
            slippage = exit_price * (self.bt_config.slippage_bps / 10000)
            trade.exit_price -= slippage

        # Apply brokerage
        trade.position_size -= self.bt_config.brokerage_per_trade

        self.trades.append(trade)
        del self.open_positions[trade.symbol]

        logger.debug(
            f"Closed trade: {trade.symbol} at {trade.exit_price:.2f}, "
            f"P&L: {trade.pnl:.2f}, Reason: {exit_reason}"
        )

    def _close_all_positions(self, last_row: pd.Series, reason: str) -> None:
        """Close all remaining open positions."""
        for symbol, trade in list(self.open_positions.items()):
            # Try to get last price for this symbol
            exit_price = trade.entry_price  # Default to entry if no data
            self._close_position(trade, exit_price, last_row['timestamp'], reason)

    def _passes_filters(self, row: pd.Series) -> bool:
        """Check if snapshot passes signal filters."""
        # Price filter
        if row['price'] < self.signal_config.min_signal_price:
            return False
        if row['price'] > self.signal_config.max_signal_price:
            return False

        # Volume filter
        if row['volume'] < self.signal_config.min_volume:
            return False

        # OI filter
        if row['open_interest'] < self.signal_config.min_open_interest:
            return False

        # Spread filter
        if 'bid_ask_spread_pct' in row and row['bid_ask_spread_pct'] > self.signal_config.max_bid_ask_spread_pct:
            return False

        return True

    def _get_entry_price(self, row: pd.Series) -> float:
        """Get entry price based on config."""
        if self.bt_config.entry_method == "mid":
            if 'mid_price' in row:
                return row['mid_price']
            else:
                return (row['bid_price'] + row['ask_price']) / 2
        elif self.bt_config.entry_method == "ask":
            return row['ask_price']
        else:
            return row['price']

    def _get_current_price(self, row: pd.Series) -> float:
        """Get current price for position update."""
        if self.bt_config.exit_method == "mid":
            if 'mid_price' in row:
                return row['mid_price']
            else:
                return (row['bid_price'] + row['ask_price']) / 2
        else:
            return row['price']
