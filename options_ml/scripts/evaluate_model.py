#!/usr/bin/env python3
"""
Evaluate trained model on test data.

Generates comprehensive evaluation report including threshold analysis,
calibration, and feature importance.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from options_ml.data.loader import load_training_data
from options_ml.modeling.models import Option2xModel
from options_ml.modeling.dataset import prepare_dataset, split_data_by_time
from options_ml.modeling.evaluate import generate_evaluation_report
from options_ml.config import Config, load_config
from options_ml.utils.logging_utils import setup_logger

logger = setup_logger(__name__, log_file="logs/evaluation.log")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Evaluate trained model")
    parser.add_argument(
        "--model-dir",
        type=str,
        required=True,
        help="Directory containing trained model"
    )
    parser.add_argument(
        "--test-data",
        type=str,
        default="data/processed/training_data.parquet",
        help="Path to test data (will use last 20%)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/evaluation",
        help="Output directory for evaluation results"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config file (optional)"
    )

    args = parser.parse_args()

    # Load config
    if args.config:
        config = load_config(args.config)
    else:
        config = Config()

    logger.info("=" * 80)
    logger.info("MODEL EVALUATION")
    logger.info("=" * 80)
    logger.info(f"Model directory: {args.model_dir}")
    logger.info(f"Test data: {args.test_data}")
    logger.info(f"Output directory: {args.output_dir}")

    # Step 1: Load model
    logger.info("\nStep 1: Loading trained model")
    try:
        model = Option2xModel.load(args.model_dir, config=config)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Step 2: Load test data
    logger.info("\nStep 2: Loading test data")
    df = load_training_data(args.test_data)

    # Split to get test set (last 20%)
    _, _, test_df = split_data_by_time(df, train_ratio=0.7, validation_ratio=0.1)
    logger.info(f"Test set size: {len(test_df)}")

    # Prepare test data
    X_test, y_test, _ = prepare_dataset(test_df, config)

    # Step 3: Generate evaluation report
    logger.info("\nStep 3: Generating evaluation report")
    report = generate_evaluation_report(
        model=model,
        X_test=X_test,
        y_test=y_test,
        output_path=args.output_dir,
        df_full=test_df
    )

    logger.info(f"\n✓ Evaluation complete! Results saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
