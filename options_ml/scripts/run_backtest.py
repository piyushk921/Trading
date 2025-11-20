#!/usr/bin/env python3
"""
Run backtest simulation on historical data.

Simulates trading with model signals and calculates performance metrics.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from options_ml.data.loader import load_training_data
from options_ml.modeling.models import Option2xModel
from options_ml.backtest.simulator import BacktestSimulator
from options_ml.backtest.metrics import generate_backtest_report
from options_ml.config import Config, load_config
from options_ml.utils.logging_utils import setup_logger

logger = setup_logger(__name__, log_file="logs/backtest.log")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run backtest simulation")
    parser.add_argument(
        "--model-dir",
        type=str,
        required=True,
        help="Directory containing trained model"
    )
    parser.add_argument(
        "--data-file",
        type=str,
        default="data/processed/training_data.parquet",
        help="Path to historical data for backtesting"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/backtest",
        help="Output directory for backtest results"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config file (optional)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Start date for backtest (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="End date for backtest (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    # Load config
    if args.config:
        config = load_config(args.config)
    else:
        config = Config()

    logger.info("=" * 80)
    logger.info("BACKTEST SIMULATION")
    logger.info("=" * 80)
    logger.info(f"Model directory: {args.model_dir}")
    logger.info(f"Data file: {args.data_file}")
    logger.info(f"Output directory: {args.output_dir}")
    if args.start_date:
        logger.info(f"Start date: {args.start_date}")
    if args.end_date:
        logger.info(f"End date: {args.end_date}")

    # Step 1: Load model
    logger.info("\nStep 1: Loading trained model")
    try:
        model = Option2xModel.load(args.model_dir, config=config)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Step 2: Load historical data
    logger.info("\nStep 2: Loading historical data")
    if not Path(args.data_file).exists():
        logger.error(f"Data file not found: {args.data_file}")
        sys.exit(1)

    df = load_training_data(args.data_file)
    logger.info(f"Loaded {len(df)} snapshots")

    # Step 3: Run backtest
    logger.info("\nStep 3: Running backtest simulation")
    simulator = BacktestSimulator(model=model, config=config)

    trades_df = simulator.run(
        df=df,
        start_date=args.start_date,
        end_date=args.end_date
    )

    if len(trades_df) == 0:
        logger.warning("No trades generated in backtest")
        logger.info("Check your signal filters and probability threshold")
        sys.exit(0)

    # Step 4: Generate report
    logger.info("\nStep 4: Generating backtest report")
    report = generate_backtest_report(
        trades_df=trades_df,
        output_path=args.output_dir
    )

    logger.info(f"\n✓ Backtest complete! Results saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
