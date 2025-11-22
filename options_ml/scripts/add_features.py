#!/usr/bin/env python3
"""
Add new, powerful features to an existing training dataset.

This script:
1. Loads a processed training data Parquet file.
2. Engineers a suite of new features (e.g., momentum, moving averages).
3. Saves the enhanced dataset to a new Parquet file.
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path to allow for package imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from options_ml.data.loader import load_training_data
from options_ml.data.storage import save_training_data
from options_ml.utils.logging_utils import setup_logger

logger = setup_logger(__name__, log_file="logs/add_features.log")

def calculate_time_based_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate time-based features like momentum and moving averages.

    This function operates on groups of contract-days to prevent data leakage.
    """
    logger.info("Calculating time-based features (momentum, moving averages)...")

    # Ensure dt is a datetime object
    if 'dt' not in df.columns or df['dt'].dtype != 'datetime64[ns]':
        df['dt'] = pd.to_datetime(df['timestamp'])

    # Sort the dataframe to ensure correct chronological order for time-window calculations
    df = df.sort_values(['symbol', 'dt'])

    # Set dt as the index to use time-based window functions
    df.set_index('dt', inplace=True)

    # Calculate rolling features per contract
    grouped = df.groupby('symbol')

    # Price momentum (rate of change) over different windows
    for window in ['5min', '15min', '30min']:
        df[f'price_roc_{window}'] = grouped['price'].transform(
            lambda x: x.pct_change(freq=window)
        )

    # Moving averages of key metrics
    for col in ['price', 'volume', 'iv', 'delta']:
        if col in df.columns:
            for window in ['10min', '30min']:
                df[f'{col}_ma_{window}'] = grouped[col].transform(
                    lambda x: x.rolling(window).mean()
                )

    # Volume spike detection (how much the current volume is above the recent average)
    if 'volume_ma_30min' in df.columns:
        df['volume_spike_ratio'] = df['volume'] / (df['volume_ma_30min'] + 1) # +1 to avoid division by zero

    # Reset index to bring 'dt' back as a column
    df.reset_index(inplace=True)

    # Fill initial NaN values created by rolling windows
    df.fillna(method='bfill', inplace=True)

    logger.info("Finished calculating time-based features.")
    return df

def main():
    """Main function to add features and save the new dataset."""
    parser = argparse.ArgumentParser(description="Add new features to a training dataset.")
    parser.add_argument(
        "--input-file",
        type=str,
        required=True,
        help="Path to the processed training data Parquet file."
    )
    parser.add_argument(
        "--output-file",
        type=str,
        required=True,
        help="Path to save the new, feature-enhanced Parquet file."
    )
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("ADDING NEW FEATURES TO DATASET")
    logger.info("=" * 80)

    # Step 1: Load the data
    logger.info(f"Step 1: Loading data from {args.input_file}")
    try:
        df = load_training_data(args.input_file)
    except FileNotFoundError:
        logger.error(f"Error: Input file not found at {args.input_file}")
        sys.exit(1)

    # Step 2: Calculate and add new features
    logger.info("Step 2: Engineering new features")
    df_enhanced = calculate_time_based_features(df)

    # Step 3: Save the new dataset
    logger.info(f"Step 3: Saving feature-enhanced data to {args.output_file}")
    save_training_data(df_enhanced, args.output_file)

    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Original number of rows: {len(df)}")
    logger.info(f"New number of rows: {len(df_enhanced)}")
    logger.info(f"Original number of columns: {len(df.columns)}")
    logger.info(f"New number of columns: {len(df_enhanced.columns)}")
    logger.info(f"Data saved to: {args.output_file}")

    logger.info("\nDONE: Feature engineering complete!")

if __name__ == "__main__":
    main()
