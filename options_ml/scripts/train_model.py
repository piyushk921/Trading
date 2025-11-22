#!/usr/bin/env python3
"""
Train ML model for option 2x prediction.

This script:
1. Loads prepared training data
2. Splits data by time
3. Trains model with proper validation
4. Saves trained model and artifacts
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from options_ml.data.loader import load_training_data
from options_ml.modeling.train import train_model
from options_ml.config import Config, load_config
from options_ml.utils.logging_utils import setup_logger

logger = setup_logger(__name__, log_file="logs/training.log")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Train option 2x prediction model")
    parser.add_argument(
        "--input-file",
        type=str,
        default="data/processed/training_data.parquet",
        help="Path to prepared training data"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/run_001",
        help="Output directory for model and artifacts"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config file (optional)"
    )
    parser.add_argument(
        "--model-type",
        type=str,
        default="lightgbm",
        choices=["lightgbm", "xgboost"],
        help="Model type to train"
    )
    parser.add_argument(
        "--use-validation",
        action="store_true",
        default=True,
        help="Use validation set for early stopping"
    )
    parser.add_argument(
        "--use-sample-weights",
        action="store_true",
        help="Use sample weights for class imbalance"
    )

    args = parser.parse_args()

    # Load config
    if args.config:
        config = load_config(args.config)
    else:
        config = Config()

    # Override model type if specified
    if args.model_type:
        config.model.model_type = args.model_type

    # Ensure directories exist
    config.ensure_directories()

    logger.info("=" * 80)
    logger.info("TRAINING OPTIONS ML MODEL")
    logger.info("=" * 80)
    logger.info(f"Input file: {args.input_file}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Model type: {config.model.model_type}")
    logger.info(f"Use validation: {args.use_validation}")
    logger.info(f"Use sample weights: {args.use_sample_weights}")

    # Step 1: Load training data
    logger.info("\nStep 1: Loading training data")
    if not Path(args.input_file).exists():
        logger.error(f"Training data file not found: {args.input_file}")
        logger.info("Please run prepare_training_data.py first")
        sys.exit(1)

    df = load_training_data(args.input_file)

    # Step 2: Train model
    logger.info("\nStep 2: Training model")
    model, training_info = train_model(
        df=df,
        output_dir=args.output_dir,
        config=config,
        use_validation=args.use_validation,
        use_sample_weights=args.use_sample_weights
    )

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TRAINING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Model type: {config.model.model_type}")
    logger.info(f"Training samples: {training_info['train_size']}")
    logger.info(f"Validation samples: {training_info['val_size']}")
    logger.info(f"Test samples: {training_info['test_size']}")
    logger.info(f"Number of features: {training_info['n_features']}")
    logger.info("\nTest set performance:")
    for metric, value in training_info['test_metrics'].items():
        logger.info(f"  {metric}: {value:.4f}")
    logger.info(f"\nModel saved to: {args.output_dir}/model")

    logger.info("\n✓ Training complete!")


if __name__ == "__main__":
    main()
