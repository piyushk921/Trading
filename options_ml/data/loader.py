"""
Data loading utilities for options ML system.

Handles loading historical data from various formats (JSON, Parquet, CSV).
"""

import json
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict

from .schemas import OptionChainData, OptionContract
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def load_json_data(filepath: str) -> dict:
    """
    Load raw JSON data from file.

    Args:
        filepath: Path to JSON file

    Returns:
        Dictionary with raw data
    """
    logger.info(f"Loading JSON data from {filepath}")
    with open(filepath, 'r') as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} contracts from JSON")
    return data


def load_option_chain_from_json(
    filepath: str,
    date: Optional[str] = None
) -> OptionChainData:
    """
    Load option chain data from JSON file.

    Args:
        filepath: Path to JSON file
        date: Optional trading date

    Returns:
        OptionChainData object
    """
    raw_data = load_json_data(filepath)
    chain_data = OptionChainData.from_raw_json(raw_data, date=date)
    logger.info(
        f"Parsed {chain_data.total_contracts} contracts for "
        f"{len(chain_data.unique_underlyings)} underlyings"
    )
    return chain_data


def flatten_option_chain_to_dataframe(raw_data: dict) -> pd.DataFrame:
    """
    Convert raw contract->timeseries structure to a flat DataFrame for ML.
    This corrected version mirrors the logic from `verify_label_improvements.py`
    to ensure data integrity.

    Args:
        raw_data: The raw JSON data as a dictionary.

    Returns:
        DataFrame with one row per snapshot.
    """
    logger.info("Flattening raw data to DataFrame")
    all_records = []

    for contract_name, contract_data in raw_data.items():
        # Ensure contract_data is a dictionary and has 'all_history'
        if not isinstance(contract_data, dict):
            continue
        all_history = contract_data.get('all_history', [])

        # Extract contract details from the name
        parts = contract_name.split('_')
        underlying, expiry, strike, option_type = parts[0], parts[1], float(parts[2]), parts[3]

        for snapshot in all_history:
            record = snapshot.copy()
            record['symbol'] = contract_name
            record['underlying'] = underlying
            record['strike'] = strike
            record['option_type'] = option_type
            record['expiry'] = expiry
            all_records.append(record)

    df = pd.DataFrame(all_records)
    if 'timestamp' in df.columns:
        df['dt'] = pd.to_datetime(df['timestamp'])

    logger.info(f"Created DataFrame with {len(df)} rows")
    return df


def load_multiple_json_files(
    filepaths: List[str],
    combine: bool = True
) -> pd.DataFrame:
    """
    Load and combine multiple JSON files.

    Args:
        filepaths: List of JSON file paths
        combine: Whether to combine into single DataFrame

    Returns:
        Combined DataFrame (if combine=True) or list of DataFrames
    """
    dfs = []

    for filepath in filepaths:
        try:
            # Extract date from filename if possible
            date = Path(filepath).stem.split('_')[-1] if '_' in Path(filepath).stem else None

            # Load the raw JSON data directly
            raw_data = load_json_data(filepath)
            # Use the corrected flattening function
            df = flatten_option_chain_to_dataframe(raw_data)
            df['source_file'] = filepath

            if date:
                df['date'] = date

            dfs.append(df)
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            continue

    if combine and dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        logger.info(f"Combined {len(dfs)} files into DataFrame with {len(combined_df)} rows")
        return combined_df
    elif dfs:
        return dfs
    else:
        logger.warning("No data loaded")
        return pd.DataFrame()


def load_parquet_data(filepath: str) -> pd.DataFrame:
    """
    Load processed data from Parquet file.

    Args:
        filepath: Path to Parquet file

    Returns:
        DataFrame
    """
    logger.info(f"Loading Parquet data from {filepath}")
    df = pd.read_parquet(filepath)
    logger.info(f"Loaded {len(df)} rows from Parquet")
    return df


def load_training_data(filepath: str) -> pd.DataFrame:
    """
    Load prepared training data.

    Args:
        filepath: Path to training data (Parquet or CSV)

    Returns:
        DataFrame with features and labels
    """
    logger.info(f"Loading training data from {filepath}")

    if filepath.endswith('.parquet'):
        df = pd.read_parquet(filepath)
    elif filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath}")

    logger.info(f"Loaded training data: {len(df)} rows, {len(df.columns)} columns")

    # Validate required columns
    required_cols = ['symbol', 'timestamp', 'price', 'label_2x']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.warning(f"Missing expected columns: {missing}")

    return df


def filter_valid_snapshots(df: pd.DataFrame, min_snapshots: int = 3) -> pd.DataFrame:
    """
    Filter contracts with minimum number of snapshots.

    Args:
        df: DataFrame with snapshots
        min_snapshots: Minimum number of snapshots per contract

    Returns:
        Filtered DataFrame
    """
    logger.info(f"Filtering contracts with >= {min_snapshots} snapshots")

    snapshot_counts = df.groupby('symbol').size()
    valid_symbols = snapshot_counts[snapshot_counts >= min_snapshots].index

    filtered_df = df[df['symbol'].isin(valid_symbols)].copy()

    logger.info(
        f"Filtered from {len(df)} to {len(filtered_df)} snapshots "
        f"({len(valid_symbols)}/{len(snapshot_counts)} contracts)"
    )

    return filtered_df
