"""
Data storage utilities for options ML system.

Handles saving processed data, models, and results.
"""

import pandas as pd
from pathlib import Path
from typing import Optional

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def save_dataframe(
    df: pd.DataFrame,
    filepath: str,
    format: str = 'parquet',
    **kwargs
) -> None:
    """
    Save DataFrame to file.

    Args:
        df: DataFrame to save
        filepath: Output file path
        format: File format ('parquet', 'csv', 'feather')
        **kwargs: Additional arguments for the save function
    """
    # Ensure directory exists
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving DataFrame ({len(df)} rows) to {filepath}")

    if format == 'parquet':
        df.to_parquet(filepath, index=False, **kwargs)
    elif format == 'csv':
        df.to_csv(filepath, index=False, **kwargs)
    elif format == 'feather':
        df.to_feather(filepath, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {format}")

    logger.info(f"Saved successfully to {filepath}")


def save_training_data(
    df: pd.DataFrame,
    output_path: str,
    format: str = 'parquet'
) -> None:
    """
    Save prepared training data.

    Args:
        df: Training DataFrame with features and labels
        output_path: Output file path
        format: File format
    """
    logger.info(f"Saving training data: {len(df)} rows, {len(df.columns)} columns")

    save_dataframe(df, output_path, format=format)

    # Log statistics
    if 'label_2x' in df.columns:
        positive_count = df['label_2x'].sum()
        total_count = len(df)
        positive_rate = positive_count / total_count * 100
        logger.info(f"Positive samples: {positive_count}/{total_count} ({positive_rate:.2f}%)")


def save_predictions(
    df: pd.DataFrame,
    output_path: str,
    include_features: bool = False
) -> None:
    """
    Save model predictions.

    Args:
        df: DataFrame with predictions
        output_path: Output file path
        include_features: Whether to include feature columns
    """
    logger.info(f"Saving predictions to {output_path}")

    if not include_features:
        # Save only identifier and prediction columns
        keep_cols = [
            col for col in df.columns
            if any(x in col.lower() for x in ['symbol', 'timestamp', 'pred', 'prob', 'label'])
        ]
        df_save = df[keep_cols].copy()
    else:
        df_save = df.copy()

    save_dataframe(df_save, output_path, format='csv')


def append_to_dataframe(
    new_data: pd.DataFrame,
    filepath: str,
    format: str = 'parquet'
) -> None:
    """
    Append new data to existing file.

    Args:
        new_data: New data to append
        filepath: File path
        format: File format
    """
    logger.info(f"Appending {len(new_data)} rows to {filepath}")

    if Path(filepath).exists():
        if format == 'parquet':
            existing_data = pd.read_parquet(filepath)
        elif format == 'csv':
            existing_data = pd.read_csv(filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")

        combined_data = pd.concat([existing_data, new_data], ignore_index=True)
    else:
        combined_data = new_data

    save_dataframe(combined_data, filepath, format=format)
