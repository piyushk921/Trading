"""Backtesting module for options ML."""

from .simulator import BacktestSimulator, Trade
from .metrics import calculate_trading_metrics, generate_backtest_report

__all__ = [
    "BacktestSimulator",
    "Trade",
    "calculate_trading_metrics",
    "generate_backtest_report",
]
