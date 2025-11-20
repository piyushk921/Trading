#!/usr/bin/env python3
"""
Run live inference example.

This script demonstrates how to:
1. Load a trained model
2. Fetch live data from Dhan API (or use mock data)
3. Generate trading signals
4. Save signals to file

Note: For actual trading, implement order execution logic.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from options_ml.modeling.models import Option2xModel
from options_ml.live.inference import LiveInferenceEngine, execute_signals_with_dhan
from options_ml.data.ingest_dhan import create_dhan_client
from options_ml.config import Config, load_config
from options_ml.utils.logging_utils import setup_logger

logger = setup_logger(__name__, log_file="logs/live_inference.log")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run live inference for signal generation")
    parser.add_argument(
        "--model-dir",
        type=str,
        required=True,
        help="Directory containing trained model"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config file (optional)"
    )
    parser.add_argument(
        "--use-mock",
        action="store_true",
        help="Use mock Dhan client for testing (no real API calls)"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="results/live_signals.csv",
        help="Output file for signals"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute signals (place orders) - USE WITH CAUTION"
    )

    args = parser.parse_args()

    # Load config
    if args.config:
        config = load_config(args.config)
    else:
        config = Config()

    logger.info("=" * 80)
    logger.info("LIVE INFERENCE")
    logger.info("=" * 80)
    logger.info(f"Model directory: {args.model_dir}")
    logger.info(f"Use mock client: {args.use_mock}")
    logger.info(f"Output file: {args.output_file}")
    logger.info(f"Execute signals: {args.execute}")

    if args.execute and not args.use_mock:
        logger.warning("=" * 80)
        logger.warning("WARNING: Signal execution is enabled!")
        logger.warning("This will place REAL orders via Dhan API.")
        logger.warning("Make sure you understand the risks.")
        logger.warning("=" * 80)
        response = input("Type 'YES' to continue: ")
        if response != "YES":
            logger.info("Execution cancelled by user")
            sys.exit(0)

    # Step 1: Load model
    logger.info("\nStep 1: Loading trained model")
    try:
        model = Option2xModel.load(args.model_dir, config=config)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Step 2: Initialize Dhan client
    logger.info("\nStep 2: Initializing Dhan API client")

    if args.use_mock:
        logger.info("Using mock Dhan client (no real API calls)")
        dhan_client = create_dhan_client(use_mock=True)
    else:
        # Get credentials from config or environment
        client_id = config.live.dhan_client_id
        access_token = config.live.dhan_access_token

        if not client_id or not access_token:
            logger.error("Dhan credentials not found in config or environment")
            logger.info("Set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN environment variables")
            logger.info("Or provide them in config file")
            logger.info("Alternatively, use --use-mock for testing")
            sys.exit(1)

        dhan_client = create_dhan_client(
            client_id=client_id,
            access_token=access_token,
            use_mock=False
        )

    dhan_client.connect()

    # Step 3: Initialize inference engine
    logger.info("\nStep 3: Initializing live inference engine")
    inference_engine = LiveInferenceEngine(
        model=model,
        dhan_client=dhan_client,
        config=config
    )

    # Step 4: Check market status
    logger.info("\nStep 4: Checking market status")
    if not inference_engine.check_market_status():
        logger.warning("Market is not ready for trading")
        logger.info("Exiting...")
        sys.exit(0)

    # Step 5: Generate signals
    logger.info("\nStep 5: Generating trading signals")
    signals = inference_engine.generate_signals(apply_filters=True)

    if not signals:
        logger.info("No signals generated")
        logger.info("Try adjusting probability threshold or signal filters")
        sys.exit(0)

    logger.info(f"\nGenerated {len(signals)} signals:")
    for i, signal in enumerate(signals, 1):
        logger.info(
            f"{i}. {signal.symbol} - "
            f"Prob: {signal.predicted_probability:.3f}, "
            f"Entry: ₹{signal.entry_price:.2f}, "
            f"Target: ₹{signal.target_price:.2f}, "
            f"SL: ₹{signal.stop_loss_price:.2f}"
        )

    # Step 6: Save signals
    logger.info(f"\nStep 6: Saving signals to {args.output_file}")
    inference_engine.save_signals(signals, args.output_file)

    # Step 7: Execute signals (if requested)
    if args.execute:
        logger.info("\nStep 7: Executing signals")
        execute_signals_with_dhan(signals)
    else:
        logger.info("\nStep 7: Skipping signal execution (use --execute to enable)")

    logger.info("\n✓ Live inference complete!")


if __name__ == "__main__":
    main()
