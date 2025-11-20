#!/usr/bin/env python3
"""
Prepare training data from raw JSON files.

This script:
1. Loads raw option chain data from JSON files
2. Builds features using FeatureBuilder
3. Creates labels using LabelBuilder
4. Saves processed data to Parquet for training
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from options_ml.data.loader import load_multiple_json_files, filter_valid_snapshots
from options_ml.data.storage import save_training_data
from options_ml.features.feature_builder import FeatureBuilder
from options_ml.labeling.label_builder import LabelBuilder
from options_ml.config import Config, load_config
from options_ml.utils.logging_utils import setup_logger

logger = setup_logger(__name__, log_file="logs/prepare_data.log")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Prepare training data from raw JSON files")
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Directory containing raw JSON files"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="data/processed/training_data.parquet",
        help="Output file path for processed data"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config file (optional)"
    )
    parser.add_argument(
        "--target-multiplier",
        type=float,
        default=2.0,
        help="Target multiplier for labeling (default: 2.0 for 2x)"
    )
    parser.add_argument(
        "--horizon-minutes",
        type=int,
        default=None,
        help="Lookahead horizon in minutes (None = end of day)"
    )

    args = parser.parse_args()

    # Load config
    if args.config:
        config = load_config(args.config)
    else:
        config = Config()

    # Override label config if specified
    if args.target_multiplier != 2.0:
        config.labels.target_multiplier = args.target_multiplier
    if args.horizon_minutes:
        config.labels.horizon_minutes = args.horizon_minutes

    # Ensure directories exist
    config.ensure_directories()

    logger.info("=" * 80)
    logger.info("PREPARING TRAINING DATA")
    logger.info("=" * 80)
    logger.info(f"Input directory: {args.input_dir}")
    logger.info(f"Output file: {args.output_file}")
    logger.info(f"Target multiplier: {config.labels.target_multiplier}x")
    logger.info(f"Horizon: {config.labels.horizon_minutes} minutes" if config.labels.horizon_minutes else "Horizon: End of day")

    # Step 1: Load raw JSON files
    logger.info("\nStep 1: Loading raw JSON files")
    input_path = Path(args.input_dir)

    if not input_path.exists():
        logger.error(f"Input directory does not exist: {input_path}")
        sys.exit(1)

    json_files = list(input_path.glob("*.json"))

    if not json_files:
        logger.error(f"No JSON files found in {input_path}")
        sys.exit(1)

    logger.info(f"Found {len(json_files)} JSON files")

    # Load and combine all files
    df_raw = load_multiple_json_files([str(f) for f in json_files], combine=True)

    if df_raw.empty:
        logger.error("No data loaded from JSON files")
        sys.exit(1)

    logger.info(f"Loaded {len(df_raw)} snapshots from {len(json_files)} files")

    # Step 2: Filter valid contracts
    logger.info("\nStep 2: Filtering valid contracts")
    df_filtered = filter_valid_snapshots(
        df_raw,
        min_snapshots=config.data.min_snapshots_per_contract
    )

    # Step 3: Build features
    logger.info("\nStep 3: Building features")
    feature_builder = FeatureBuilder(config)
    df_features = feature_builder.build_features(df_filtered)

    # Step 4: Build labels
    logger.info("\nStep 4: Building labels")
    label_builder = LabelBuilder(config)
    df_labeled = label_builder.build_labels(df_features)

    # Step 5: Remove rows with NaN labels (can't be used for training)
    logger.info("\nStep 5: Cleaning data")
    before_clean = len(df_labeled)
    df_clean = df_labeled.dropna(subset=['label_2x'])
    after_clean = len(df_clean)
    logger.info(f"Removed {before_clean - after_clean} rows with missing labels")

    # Step 6: Save processed data
    logger.info("\nStep 6: Saving processed data")
    save_training_data(df_clean, args.output_file, format='parquet')

    # Summary statistics
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total snapshots: {len(df_clean)}")
    logger.info(f"Total features: {len(feature_builder.get_feature_names(df_clean))}")
    logger.info(f"Unique contracts: {df_clean['symbol'].nunique()}")
    logger.info(f"Unique underlyings: {df_clean['underlying'].nunique()}")
    logger.info(f"Positive samples (2x): {df_clean['label_2x'].sum()} ({df_clean['label_2x'].mean()*100:.2f}%)")
    logger.info(f"Data saved to: {args.output_file}")

    logger.info("\n✓ Data preparation complete!")


if __name__ == "__main__":
    main()
