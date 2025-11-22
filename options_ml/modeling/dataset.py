"""
Dataset preparation for model training.

Handles feature selection, train/test splits, and class imbalance.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, List
from sklearn.model_selection import train_test_split

from ..config import Config, get_config
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def prepare_dataset(
    df: pd.DataFrame,
    config: Optional[Config] = None,
    exclude_features: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Prepare dataset for training.

    Args:
        df: DataFrame with features and labels
        config: Configuration object
        exclude_features: Additional features to exclude

    Returns:
        Tuple of (X, y, feature_names)
    """
    logger.info(f"Preparing dataset from {len(df)} rows")

    if config is None:
        config = get_config()

    # Define columns to exclude from features
    exclude_cols = {
        'symbol', 'timestamp', 'dt', 'underlying', 'strike', 'option_type',
        'label_2x', 'time_to_2x_minutes', 'max_future_return',
        'source_file', 'date', 'expiry',
        # Raw OHLC (often zero from API)
        'open', 'high', 'low', 'close',
    }

    if exclude_features:
        exclude_cols.update(exclude_features)

    # Get feature columns
    feature_cols = [col for col in df.columns if col not in exclude_cols]

    # Validate required columns exist
    if 'label_2x' not in df.columns:
        raise ValueError("Dataset must have 'label_2x' column")

    # Extract features and labels
    X = df[feature_cols].copy()
    y = df['label_2x'].copy()

    # Handle missing values
    if X.isnull().any().any():
        null_counts = X.isnull().sum()
        logger.warning(f"Found missing values in features:\n{null_counts[null_counts > 0]}")

        # Fill with 0 (or could use more sophisticated imputation)
        X = X.fillna(0)
        logger.info("Filled missing values with 0")

    # Handle infinite values
    if np.isinf(X.values).any():
        logger.warning("Found infinite values in features, replacing with 0")
        X = X.replace([np.inf, -np.inf], 0)

    logger.info(f"Prepared dataset: X shape={X.shape}, y shape={y.shape}")
    logger.info(f"Feature count: {len(feature_cols)}")
    logger.info(f"Positive samples: {y.sum()}/{len(y)} ({y.mean()*100:.2f}%)")

    return X, y, feature_cols


def split_data_by_time(
    df: pd.DataFrame,
    train_ratio: float = 0.8,
    validation_ratio: float = 0.1,
    time_col: str = 'timestamp'
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data by time (chronological split to avoid leakage).

    Args:
        df: DataFrame with time-sorted data
        train_ratio: Fraction of data for training
        validation_ratio: Fraction of data for validation
        time_col: Name of time column

    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    logger.info(f"Splitting data by time with ratios: train={train_ratio}, val={validation_ratio}")

    # Ensure sorted by time
    if time_col in df.columns:
        df = df.sort_values(time_col).reset_index(drop=True)
    elif 'dt' in df.columns:
        df = df.sort_values('dt').reset_index(drop=True)
    else:
        logger.warning("No time column found, using existing order")

    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + validation_ratio))

    train_df = df.iloc[:train_end].copy()
    val_df = df.iloc[train_end:val_end].copy()
    test_df = df.iloc[val_end:].copy()

    logger.info(f"Split sizes: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")

    return train_df, val_df, test_df


def split_data_by_date(
    df: pd.DataFrame,
    train_end_date: str,
    val_end_date: Optional[str] = None,
    date_col: str = 'date'
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data by explicit dates.

    Args:
        df: DataFrame with date column
        train_end_date: Last date for training (inclusive)
        val_end_date: Last date for validation (inclusive), None = no validation
        date_col: Name of date column

    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    logger.info(f"Splitting data by date: train <= {train_end_date}, val <= {val_end_date}")

    train_df = df[df[date_col] <= train_end_date].copy()

    if val_end_date is not None:
        val_df = df[(df[date_col] > train_end_date) & (df[date_col] <= val_end_date)].copy()
        test_df = df[df[date_col] > val_end_date].copy()
    else:
        val_df = pd.DataFrame()
        test_df = df[df[date_col] > train_end_date].copy()

    logger.info(f"Split sizes: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")

    return train_df, val_df, test_df


def balance_dataset(
    X: pd.DataFrame,
    y: pd.Series,
    method: str = "undersample",
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Balance dataset for class imbalance.

    Args:
        X: Features
        y: Labels
        method: Balancing method ("undersample", "oversample", or "none")
        random_state: Random seed

    Returns:
        Tuple of (X_balanced, y_balanced)
    """
    logger.info(f"Balancing dataset using method: {method}")

    if method == "none":
        return X, y

    pos_count = (y == 1).sum()
    neg_count = (y == 0).sum()
    logger.info(f"Original class distribution: pos={pos_count}, neg={neg_count}")

    if method == "undersample":
        # Undersample majority class
        min_count = min(pos_count, neg_count)

        pos_indices = y[y == 1].index
        neg_indices = y[y == 0].index

        pos_sample = np.random.RandomState(random_state).choice(
            pos_indices, size=min_count, replace=False
        )
        neg_sample = np.random.RandomState(random_state).choice(
            neg_indices, size=min_count, replace=False
        )

        balanced_indices = np.concatenate([pos_sample, neg_sample])
        np.random.RandomState(random_state).shuffle(balanced_indices)

        X_balanced = X.loc[balanced_indices].reset_index(drop=True)
        y_balanced = y.loc[balanced_indices].reset_index(drop=True)

    elif method == "oversample":
        # Oversample minority class
        max_count = max(pos_count, neg_count)

        pos_indices = y[y == 1].index
        neg_indices = y[y == 0].index

        pos_sample = np.random.RandomState(random_state).choice(
            pos_indices, size=max_count, replace=True
        )
        neg_sample = np.random.RandomState(random_state).choice(
            neg_indices, size=max_count, replace=True
        )

        balanced_indices = np.concatenate([pos_sample, neg_sample])
        np.random.RandomState(random_state).shuffle(balanced_indices)

        X_balanced = X.loc[balanced_indices].reset_index(drop=True)
        y_balanced = y.loc[balanced_indices].reset_index(drop=True)

    else:
        raise ValueError(f"Unknown balancing method: {method}")

    logger.info(f"Balanced dataset: {len(X_balanced)} samples")
    return X_balanced, y_balanced


def create_sample_weights(
    y: pd.Series,
    method: str = "inverse_freq"
) -> np.ndarray:
    """
    Create sample weights for handling class imbalance.

    Args:
        y: Labels
        method: Weighting method ("inverse_freq" or "sqrt_inverse_freq")

    Returns:
        Array of sample weights
    """
    pos_count = (y == 1).sum()
    neg_count = (y == 0).sum()
    total = len(y)

    if method == "inverse_freq":
        pos_weight = total / (2 * pos_count) if pos_count > 0 else 1.0
        neg_weight = total / (2 * neg_count) if neg_count > 0 else 1.0
    elif method == "sqrt_inverse_freq":
        pos_weight = np.sqrt(total / pos_count) if pos_count > 0 else 1.0
        neg_weight = np.sqrt(total / neg_count) if neg_count > 0 else 1.0
    else:
        raise ValueError(f"Unknown weighting method: {method}")

    weights = np.where(y == 1, pos_weight, neg_weight)

    logger.info(f"Created sample weights: pos_weight={pos_weight:.2f}, neg_weight={neg_weight:.2f}")
    return weights
