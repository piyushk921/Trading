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
import pandas as pd

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
    parser.add_argument(
        "--filter-atm",
        type=int,
        default=None,
        help="Keep only N strikes above and below ATM (e.g., 5 for ATM±5)"
    )
    parser.add_argument(
        "--filter-moneyness",
        type=float,
        default=None,
        help="Keep only strikes within moneyness threshold (e.g., 0.05 for ±5%%)"
    )
    parser.add_argument(
        "--filter-top-priced",
        type=int,
        default=None,
        help="Keep top N highest-priced CE and PE options per underlying per day (e.g., 5 for top 5 CE + top 5 PE)"
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
    if args.filter_moneyness:
        logger.info(f"ATM Filter: Keep strikes within ±{args.filter_moneyness*100:.0f}% moneyness")
    elif args.filter_atm:
        logger.info(f"ATM Filter: Keep top {args.filter_atm} strikes above/below ATM")
    elif args.filter_top_priced:
        logger.info(f"Price Filter: Keep top {args.filter_top_priced} highest-priced CE and PE options per day")

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

    # Step 2.5: Filter by moneyness (ATM strikes only)
    if args.filter_moneyness or args.filter_atm or args.filter_top_priced:
        logger.info("\nStep 2.5: Filtering by moneyness (keeping only ATM and near-ATM strikes)")
        before_filter = len(df_filtered)

        if args.filter_moneyness:
            # Filter by moneyness percentage (e.g., 0.05 = ±5%)
            df_filtered['abs_moneyness'] = abs((df_filtered['spot_price'] - df_filtered['strike']) / df_filtered['strike'])
            df_filtered = df_filtered[df_filtered['abs_moneyness'] <= args.filter_moneyness].copy()
            df_filtered = df_filtered.drop('abs_moneyness', axis=1)
            logger.info(f"Kept strikes within ±{args.filter_moneyness*100:.0f}% moneyness")

        elif args.filter_atm:
            # Filter by keeping N strikes above and below ATM
            import numpy as np

            filtered_dfs = []
            for (underlying, timestamp), group in df_filtered.groupby(['underlying', 'timestamp']):
                if len(group) == 0:
                    continue

                # Get spot price (should be same for all in group)
                spot = group['spot_price'].iloc[0]

                # Calculate distance from ATM for each strike
                group = group.copy()
                group['strike_distance'] = abs(group['strike'] - spot)

                # Sort by distance and take top N*2 (N above, N below)
                group = group.sort_values('strike_distance')
                top_strikes = group.head(args.filter_atm * 2)

                filtered_dfs.append(top_strikes.drop('strike_distance', axis=1))

            if filtered_dfs:
                df_filtered = pd.concat(filtered_dfs, ignore_index=True)
                logger.info(f"Kept top {args.filter_atm} strikes above and below ATM per underlying")

        elif args.filter_top_priced:
            # Filter by keeping top N highest-priced CE and PE options per underlying per day
            import numpy as np

            # Extract date from timestamp
            df_filtered['date'] = pd.to_datetime(df_filtered['timestamp']).dt.date

            # Track selected strikes
            selected_strikes = set()

            # Group by underlying and date
            for (underlying, date), day_group in df_filtered.groupby(['underlying', 'date']):
                # Find the first timestamp of the day (first fetch)
                first_timestamp = day_group['timestamp'].min()
                first_fetch = day_group[day_group['timestamp'] == first_timestamp]

                # Split into CE and PE options
                ce_options = first_fetch[first_fetch['option_type'] == 'CE']
                pe_options = first_fetch[first_fetch['option_type'] == 'PE']

                # Get top N highest-priced CE options
                if len(ce_options) > 0:
                    top_ce = ce_options.nlargest(args.filter_top_priced, 'price')
                    for strike in top_ce['strike'].unique():
                        selected_strikes.add((underlying, date, strike, 'CE'))

                # Get top N highest-priced PE options
                if len(pe_options) > 0:
                    top_pe = pe_options.nlargest(args.filter_top_priced, 'price')
                    for strike in top_pe['strike'].unique():
                        selected_strikes.add((underlying, date, strike, 'PE'))

            # Filter to keep only selected strikes for the entire day
            def is_selected(row):
                return (row['underlying'], row['date'], row['strike'], row['option_type']) in selected_strikes

            df_filtered['selected'] = df_filtered.apply(is_selected, axis=1)
            df_filtered = df_filtered[df_filtered['selected']].drop(['selected', 'date'], axis=1).copy()

            logger.info(f"Kept top {args.filter_top_priced} highest-priced CE and PE options per underlying per day")
            logger.info(f"Total unique strikes selected: {len(selected_strikes)}")

        after_filter = len(df_filtered)
        logger.info(f"Filtered from {before_filter:,} to {after_filter:,} snapshots ({(after_filter/before_filter)*100:.1f}% kept)")
        logger.info(f"Removed {before_filter - after_filter:,} far OTM/ITM snapshots")

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
