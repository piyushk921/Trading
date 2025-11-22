"""
Backtest performance metrics calculation.

Calculates trading KPIs including win rate, Sharpe ratio, drawdown, etc.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def calculate_trading_metrics(trades_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate comprehensive trading metrics from trades DataFrame.

    Args:
        trades_df: DataFrame with trade history

    Returns:
        Dictionary of metrics
    """
    if len(trades_df) == 0:
        logger.warning("No trades to analyze")
        return {}

    logger.info(f"Calculating metrics for {len(trades_df)} trades")

    metrics = {}

    # Basic counts
    metrics['total_trades'] = len(trades_df)
    metrics['winning_trades'] = (trades_df['is_winner'] == True).sum()
    metrics['losing_trades'] = (trades_df['is_winner'] == False).sum()

    # Win rate
    metrics['win_rate'] = metrics['winning_trades'] / metrics['total_trades'] * 100

    # P&L metrics
    metrics['total_pnl'] = trades_df['pnl'].sum()
    metrics['avg_pnl_per_trade'] = trades_df['pnl'].mean()
    metrics['median_pnl_per_trade'] = trades_df['pnl'].median()

    # Separate winner/loser stats
    winners = trades_df[trades_df['is_winner'] == True]
    losers = trades_df[trades_df['is_winner'] == False]

    if len(winners) > 0:
        metrics['avg_win'] = winners['pnl'].mean()
        metrics['max_win'] = winners['pnl'].max()
        metrics['avg_win_return_pct'] = winners['return_pct'].mean()
    else:
        metrics['avg_win'] = 0
        metrics['max_win'] = 0
        metrics['avg_win_return_pct'] = 0

    if len(losers) > 0:
        metrics['avg_loss'] = losers['pnl'].mean()
        metrics['max_loss'] = losers['pnl'].min()
        metrics['avg_loss_return_pct'] = losers['return_pct'].mean()
    else:
        metrics['avg_loss'] = 0
        metrics['max_loss'] = 0
        metrics['avg_loss_return_pct'] = 0

    # Risk/reward ratio
    if metrics['avg_loss'] != 0:
        metrics['risk_reward_ratio'] = abs(metrics['avg_win'] / metrics['avg_loss'])
    else:
        metrics['risk_reward_ratio'] = np.inf if metrics['avg_win'] > 0 else 0

    # Expectancy
    win_prob = metrics['win_rate'] / 100
    loss_prob = 1 - win_prob
    metrics['expectancy'] = (win_prob * metrics['avg_win']) + (loss_prob * metrics['avg_loss'])

    # Return metrics
    metrics['total_return_pct'] = trades_df['return_pct'].sum()
    metrics['avg_return_pct'] = trades_df['return_pct'].mean()
    metrics['median_return_pct'] = trades_df['return_pct'].median()

    # Drawdown
    cumulative_pnl = trades_df['pnl'].cumsum()
    running_max = cumulative_pnl.cummax()
    drawdown = cumulative_pnl - running_max
    metrics['max_drawdown'] = drawdown.min()

    # Consecutive wins/losses
    is_winner_series = trades_df['is_winner'].astype(int)
    consecutive_wins = _max_consecutive(is_winner_series, 1)
    consecutive_losses = _max_consecutive(is_winner_series, 0)

    metrics['max_consecutive_wins'] = consecutive_wins
    metrics['max_consecutive_losses'] = consecutive_losses

    # Sharpe-like ratio (simplified)
    if trades_df['pnl'].std() > 0:
        metrics['sharpe_ratio'] = trades_df['pnl'].mean() / trades_df['pnl'].std() * np.sqrt(252)
    else:
        metrics['sharpe_ratio'] = 0

    # Profit factor
    total_profit = winners['pnl'].sum() if len(winners) > 0 else 0
    total_loss = abs(losers['pnl'].sum()) if len(losers) > 0 else 0

    if total_loss > 0:
        metrics['profit_factor'] = total_profit / total_loss
    else:
        metrics['profit_factor'] = np.inf if total_profit > 0 else 0

    # Exit reason breakdown
    for reason in trades_df['exit_reason'].unique():
        count = (trades_df['exit_reason'] == reason).sum()
        metrics[f'exit_{reason}_count'] = count
        metrics[f'exit_{reason}_pct'] = count / len(trades_df) * 100

    return metrics


def _max_consecutive(series: pd.Series, value: int) -> int:
    """Calculate maximum consecutive occurrences of a value."""
    if len(series) == 0:
        return 0

    max_count = 0
    current_count = 0

    for val in series:
        if val == value:
            current_count += 1
            max_count = max(max_count, current_count)
        else:
            current_count = 0

    return max_count


def calculate_daily_metrics(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate metrics grouped by day.

    Args:
        trades_df: DataFrame with trade history

    Returns:
        DataFrame with daily metrics
    """
    if len(trades_df) == 0:
        return pd.DataFrame()

    # Extract date from entry_time
    trades_df['date'] = pd.to_datetime(trades_df['entry_time']).dt.date

    daily_metrics = []

    for date, day_trades in trades_df.groupby('date'):
        metrics = {
            'date': date,
            'trades': len(day_trades),
            'winners': (day_trades['is_winner'] == True).sum(),
            'losers': (day_trades['is_winner'] == False).sum(),
            'win_rate': (day_trades['is_winner'] == True).sum() / len(day_trades) * 100,
            'total_pnl': day_trades['pnl'].sum(),
            'avg_pnl': day_trades['pnl'].mean(),
        }
        daily_metrics.append(metrics)

    daily_df = pd.DataFrame(daily_metrics)
    return daily_df


def generate_backtest_report(
    trades_df: pd.DataFrame,
    output_path: Optional[str] = None
) -> Dict[str, any]:
    """
    Generate comprehensive backtest report.

    Args:
        trades_df: DataFrame with trade history
        output_path: Optional path to save report files

    Returns:
        Dictionary with all metrics and analysis
    """
    logger.info("=" * 80)
    logger.info("Generating Backtest Report")
    logger.info("=" * 80)

    if len(trades_df) == 0:
        logger.warning("No trades to report")
        return {}

    report = {}

    # 1. Overall metrics
    logger.info("\n1. Overall Trading Metrics")
    overall_metrics = calculate_trading_metrics(trades_df)
    report['overall_metrics'] = overall_metrics

    # Print key metrics
    logger.info(f"Total Trades: {overall_metrics['total_trades']}")
    logger.info(f"Win Rate: {overall_metrics['win_rate']:.2f}%")
    logger.info(f"Total P&L: ${overall_metrics['total_pnl']:.2f}")
    logger.info(f"Avg P&L per Trade: ${overall_metrics['avg_pnl_per_trade']:.2f}")
    logger.info(f"Risk/Reward Ratio: {overall_metrics['risk_reward_ratio']:.2f}")
    logger.info(f"Profit Factor: {overall_metrics['profit_factor']:.2f}")
    logger.info(f"Max Drawdown: ${overall_metrics['max_drawdown']:.2f}")
    logger.info(f"Sharpe Ratio: {overall_metrics['sharpe_ratio']:.2f}")

    # 2. Daily metrics
    logger.info("\n2. Daily Performance")
    daily_metrics = calculate_daily_metrics(trades_df)
    report['daily_metrics'] = daily_metrics

    if len(daily_metrics) > 0:
        logger.info(f"Trading Days: {len(daily_metrics)}")
        logger.info(f"Avg Trades per Day: {daily_metrics['trades'].mean():.1f}")
        logger.info(f"Avg Daily P&L: ${daily_metrics['total_pnl'].mean():.2f}")
        logger.info(f"Best Day: ${daily_metrics['total_pnl'].max():.2f}")
        logger.info(f"Worst Day: ${daily_metrics['total_pnl'].min():.2f}")

    # 3. Exit reason analysis
    logger.info("\n3. Exit Reason Breakdown")
    exit_reasons = trades_df['exit_reason'].value_counts()
    logger.info(exit_reasons.to_string())

    # 4. Return distribution
    logger.info("\n4. Return Distribution")
    logger.info(f"Mean Return: {trades_df['return_pct'].mean():.2f}%")
    logger.info(f"Median Return: {trades_df['return_pct'].median():.2f}%")
    logger.info(f"Std Dev Return: {trades_df['return_pct'].std():.2f}%")
    logger.info(f"Min Return: {trades_df['return_pct'].min():.2f}%")
    logger.info(f"Max Return: {trades_df['return_pct'].max():.2f}%")

    # 5. Cumulative P&L
    trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
    report['trades_with_cumulative'] = trades_df

    # Save report if path provided
    if output_path:
        from pathlib import Path
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save trades
        trades_df.to_csv(output_dir / "trades.csv", index=False)

        # Save metrics
        metrics_df = pd.DataFrame([overall_metrics])
        metrics_df.to_csv(output_dir / "overall_metrics.csv", index=False)

        # Save daily metrics
        if len(daily_metrics) > 0:
            daily_metrics.to_csv(output_dir / "daily_metrics.csv", index=False)

        logger.info(f"\nBacktest report saved to {output_path}")

    logger.info("=" * 80)
    logger.info("Backtest Report Complete")
    logger.info("=" * 80)

    return report
