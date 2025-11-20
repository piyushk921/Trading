"""
Feature engineering for options ML system.

Builds comprehensive feature sets from option snapshot data including:
- Static/snapshot features (moneyness, Greeks, spreads)
- Intraday change features (price returns, volume momentum)
- Cross-sectional features (relative ranking within chain)
- Time-based features (time of day, time to expiry)
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Dict
import math

from ..config import Config, get_config
from ..utils.time_utils import parse_timestamp, encode_time_of_day
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


class FeatureBuilder:
    """
    Builds ML features from option contract snapshots.

    Handles both historical batch processing and live single-snapshot feature generation.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize feature builder.

        Args:
            config: Configuration object (uses global config if None)
        """
        self.config = config or get_config()
        self.feature_config = self.config.features

    def build_features(self, df: pd.DataFrame, chunk_size: int = 100000, use_disk: bool = True) -> pd.DataFrame:
        """
        Build complete feature set from a DataFrame of snapshots.

        Args:
            df: DataFrame with option snapshots (must have required columns)
            chunk_size: Process data in chunks to avoid memory issues (default: 100k rows)
            use_disk: Save chunks to disk for very large datasets (default: True)

        Returns:
            DataFrame with added feature columns

        Note:
            Input df should have columns matching OptionSnapshot schema,
            plus 'symbol', 'underlying', 'strike', 'option_type'.
        """
        logger.info(f"Building features for {len(df)} snapshots")

        # If dataset is small, process normally
        if len(df) <= chunk_size:
            return self._build_features_internal(df)

        # For large datasets, process in chunks by symbol
        logger.info(f"Large dataset detected. Processing in chunks...")

        df = df.copy()

        # Ensure we have a datetime column
        if 'timestamp' in df.columns and df['timestamp'].dtype == 'object':
            df['dt'] = pd.to_datetime(df['timestamp'])
        elif 'dt' not in df.columns:
            raise ValueError("DataFrame must have 'timestamp' or 'dt' column")

        # Sort by symbol and time
        logger.info("Sorting data...")
        df = df.sort_values(['symbol', 'dt']).reset_index(drop=True)

        # Process by groups of symbols to keep contracts together
        symbols = df['symbol'].unique()
        total_symbols = len(symbols)

        # For very large datasets, save chunks to disk
        if use_disk and len(df) > 500000:
            return self._build_features_with_disk(df, symbols, total_symbols, chunk_size)
        else:
            return self._build_features_in_memory(df, symbols, total_symbols, chunk_size)

    def _build_features_in_memory(self, df: pd.DataFrame, symbols: np.ndarray,
                                   total_symbols: int, chunk_size: int) -> pd.DataFrame:
        """Build features keeping chunks in memory (for medium datasets)."""
        processed_dfs = []

        # Process symbols in batches
        batch_size = max(1, chunk_size // 20)  # Assume ~20 snapshots per symbol
        for i in range(0, total_symbols, batch_size):
            batch_symbols = symbols[i:i+batch_size]
            batch_df = df[df['symbol'].isin(batch_symbols)].copy()

            logger.info(f"Processing symbols {i+1}-{min(i+batch_size, total_symbols)} of {total_symbols} ({len(batch_df)} rows)")

            batch_df = self._build_features_internal(batch_df)
            processed_dfs.append(batch_df)

        logger.info("Combining processed chunks...")
        result_df = pd.concat(processed_dfs, ignore_index=True)

        logger.info(f"Feature building complete. Total features: {len(result_df.columns)}")
        return result_df

    def _build_features_with_disk(self, df: pd.DataFrame, symbols: np.ndarray,
                                   total_symbols: int, chunk_size: int) -> pd.DataFrame:
        """Build features saving chunks to disk (for very large datasets)."""
        import tempfile
        import os

        logger.info("Very large dataset - will save chunks to disk to avoid memory issues")

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_files = []

        try:
            # Process symbols in batches
            batch_size = max(1, chunk_size // 20)  # Assume ~20 snapshots per symbol
            for i in range(0, total_symbols, batch_size):
                batch_symbols = symbols[i:i+batch_size]
                batch_df = df[df['symbol'].isin(batch_symbols)].copy()

                logger.info(f"Processing symbols {i+1}-{min(i+batch_size, total_symbols)} of {total_symbols} ({len(batch_df)} rows)")

                batch_df = self._build_features_internal(batch_df)

                # Save to temporary file
                temp_file = os.path.join(temp_dir, f"chunk_{i:06d}.parquet")
                batch_df.to_parquet(temp_file, index=False)
                temp_files.append(temp_file)

                # Free memory immediately
                del batch_df

            logger.info(f"Saved {len(temp_files)} chunks to disk. Now combining pairs iteratively...")

            # Hierarchical merge: combine 2 files at a time to minimize memory
            current_files = temp_files[:]
            merge_round = 1

            while len(current_files) > 1:
                logger.info(f"Merge round {merge_round}: combining {len(current_files)} files...")
                next_files = []

                for i in range(0, len(current_files), 2):
                    if i + 1 < len(current_files):
                        # Combine pair using chunked approach to minimize memory
                        logger.info(f"  Merging files {i+1} and {i+2} of {len(current_files)}...")

                        # Save merged result - write first file, then append second
                        merged_file = os.path.join(temp_dir, f"merged_r{merge_round}_{i:06d}.parquet")

                        try:
                            # Try memory-efficient merge with chunked reading
                            df1 = pd.read_parquet(current_files[i])
                            df1.to_parquet(merged_file, index=False)
                            del df1

                            # Append second file in chunks to avoid memory spike
                            df2 = pd.read_parquet(current_files[i + 1])

                            # Read existing merged file and append
                            existing = pd.read_parquet(merged_file)
                            combined = pd.concat([existing, df2], ignore_index=True)
                            combined.to_parquet(merged_file, index=False)

                            del df2, existing, combined
                        except MemoryError:
                            logger.warning("MemoryError during merge - trying ultra-conservative approach")
                            # Fall back to line-by-line if needed (very slow but works)
                            import pyarrow.parquet as pq
                            import pyarrow as pa

                            # Use PyArrow for more memory-efficient concatenation
                            table1 = pq.read_table(current_files[i])
                            table2 = pq.read_table(current_files[i + 1])
                            combined_table = pa.concat_tables([table1, table2])
                            pq.write_table(combined_table, merged_file)

                            del table1, table2, combined_table

                        next_files.append(merged_file)
                    else:
                        # Odd file out, carry forward
                        next_files.append(current_files[i])

                current_files = next_files
                merge_round += 1

            # Final result is the last remaining file
            logger.info("Loading final merged result...")
            result_df = pd.read_parquet(current_files[0])

            logger.info(f"Feature building complete. Total features: {len(result_df.columns)}")
            return result_df

        finally:
            # Clean up temporary files
            logger.info("Cleaning up temporary files...")
            import glob
            # Remove all parquet files in temp directory
            for temp_file in glob.glob(os.path.join(temp_dir, "*.parquet")):
                try:
                    os.remove(temp_file)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass

    def _build_features_internal(self, df: pd.DataFrame) -> pd.DataFrame:
        """Internal method to build features (called per chunk)."""
        # Ensure we have a datetime column
        if 'timestamp' in df.columns and df['timestamp'].dtype == 'object':
            df['dt'] = pd.to_datetime(df['timestamp'])
        elif 'dt' not in df.columns:
            df['dt'] = pd.to_datetime(df['timestamp'])

        # Sort by symbol and time to ensure proper ordering
        df = df.sort_values(['symbol', 'dt']).reset_index(drop=True)

        # Build features in groups
        df = self._add_static_features(df)
        df = self._add_time_features(df)
        df = self._add_greek_features(df)
        df = self._add_liquidity_features(df)
        df = self._add_spread_features(df)
        df = self._add_lagged_features(df)
        df = self._add_rolling_features(df)

        # Cross-sectional features (if enabled)
        if self.feature_config.compute_cross_sectional:
            df = self._add_cross_sectional_features(df)

        return df

    def _add_static_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add static snapshot features."""
        # Fill missing spot_price with strike (reasonable approximation)
        df['spot_price'] = df['spot_price'].fillna(df['strike'])

        # Moneyness features
        df['moneyness'] = (df['spot_price'] - df['strike']) / df['strike']
        df['log_moneyness'] = np.log(df['spot_price'] / df['strike'])
        df['abs_moneyness'] = np.abs(df['moneyness'])

        # Distance to ATM
        df['distance_to_atm'] = np.abs(df['spot_price'] - df['strike'])
        df['distance_to_atm_pct'] = df['distance_to_atm'] / df['spot_price'] * 100

        # Option type encoding
        df['is_call'] = (df['option_type'] == 'CE').astype(int)
        df['is_put'] = (df['option_type'] == 'PE').astype(int)

        # Price level
        df['price_level'] = df['price']
        df['log_price'] = np.log(df['price'] + 1)  # Add 1 to avoid log(0)

        # Spot price level
        df['log_spot_price'] = np.log(df['spot_price'])

        return df

    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features (optimized for large datasets)."""
        # Ensure dt column is datetime
        if 'dt' not in df.columns:
            df['dt'] = pd.to_datetime(df['timestamp'])
        elif df['dt'].dtype == 'object':
            df['dt'] = pd.to_datetime(df['dt'])

        # Extract hour and minute (vectorized)
        df['hour'] = df['dt'].dt.hour
        df['minute'] = df['dt'].dt.minute

        # Calculate minutes since market open (9:15 AM)
        market_open_hour = 9
        market_open_minute = 15
        df['minutes_since_open'] = (df['hour'] - market_open_hour) * 60 + (df['minute'] - market_open_minute)

        # Cyclical encoding (vectorized)
        total_market_minutes = 375.0  # 6 hours 15 minutes
        angle = (df['minutes_since_open'] / total_market_minutes) * 2 * np.pi
        df['sin_time_of_day'] = np.sin(angle)
        df['cos_time_of_day'] = np.cos(angle)

        return df

    def _add_greek_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Greek-based features."""
        # Raw Greeks are already in the data
        # Add some derived features

        # Delta-adjusted gamma
        df['delta_gamma'] = df['delta'] * df['gamma']

        # Vega-to-theta ratio (risk ratio)
        df['vega_theta_ratio'] = np.where(
            df['theta'] != 0,
            df['vega'] / np.abs(df['theta']),
            0
        )

        # IV level
        df['iv_level'] = df['iv']
        df['log_iv'] = np.log(df['iv'] + 1)

        return df

    def _add_liquidity_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add liquidity-based features."""
        # Volume and OI
        df['log_volume'] = np.log(df['volume'] + 1)
        df['log_oi'] = np.log(df['open_interest'] + 1)
        df['log_oi_change'] = np.log(np.abs(df['oi_change']) + 1)
        df['oi_change_sign'] = np.sign(df['oi_change'])

        # Volume to OI ratio
        df['volume_oi_ratio'] = np.where(
            df['open_interest'] > 0,
            df['volume'] / df['open_interest'],
            0
        )

        return df

    def _add_spread_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add bid-ask spread features."""
        # Mid price
        df['mid_price'] = (df['bid_price'] + df['ask_price']) / 2.0

        # Spreads
        df['bid_ask_spread'] = df['ask_price'] - df['bid_price']
        df['bid_ask_spread_pct'] = np.where(
            df['mid_price'] > 0,
            (df['bid_ask_spread'] / df['mid_price']) * 100,
            0
        )

        # Order book imbalance
        total_qty = df['bid_qty'] + df['ask_qty']
        df['order_book_imbalance'] = np.where(
            total_qty > 0,
            (df['bid_qty'] - df['ask_qty']) / total_qty,
            0
        )

        # Price vs mid (which side is last price on?)
        df['price_vs_mid'] = df['price'] - df['mid_price']
        df['price_vs_mid_pct'] = np.where(
            df['mid_price'] > 0,
            (df['price_vs_mid'] / df['mid_price']) * 100,
            0
        )

        return df

    def _add_lagged_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add lagged features (price returns, Greek changes, etc.)."""
        lookback_windows = self.feature_config.lookback_windows

        for lag in lookback_windows:
            # Group by symbol to ensure we don't leak across contracts
            grouped = df.groupby('symbol')

            # Price returns
            df[f'price_return_{lag}'] = grouped['price'].pct_change(lag)
            df[f'spot_return_{lag}'] = grouped['spot_price'].pct_change(lag)

            # Greek changes
            df[f'delta_change_{lag}'] = grouped['delta'].diff(lag)
            df[f'iv_change_{lag}'] = grouped['iv'].diff(lag)
            df[f'vega_change_{lag}'] = grouped['vega'].diff(lag)
            df[f'theta_change_{lag}'] = grouped['theta'].diff(lag)

            # Volume and OI changes
            df[f'volume_change_{lag}'] = grouped['volume'].diff(lag)
            df[f'oi_change_{lag}'] = grouped['open_interest'].diff(lag)

            # Spread changes
            df[f'spread_change_{lag}'] = grouped['bid_ask_spread_pct'].diff(lag)

        return df

    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling statistics features."""
        if not self.feature_config.compute_rolling_stats:
            return df

        rolling_windows = self.feature_config.rolling_window_sizes

        for window in rolling_windows:
            grouped = df.groupby('symbol')

            # Rolling volatility
            df[f'price_volatility_{window}'] = grouped['price'].rolling(window).std().reset_index(0, drop=True)
            df[f'spot_volatility_{window}'] = grouped['spot_price'].rolling(window).std().reset_index(0, drop=True)

            # Rolling means
            df[f'price_ma_{window}'] = grouped['price'].rolling(window).mean().reset_index(0, drop=True)
            df[f'volume_ma_{window}'] = grouped['volume'].rolling(window).mean().reset_index(0, drop=True)

            # Rolling IV stats
            df[f'iv_mean_{window}'] = grouped['iv'].rolling(window).mean().reset_index(0, drop=True)
            df[f'iv_std_{window}'] = grouped['iv'].rolling(window).std().reset_index(0, drop=True)

            # Price momentum (current price vs rolling mean)
            df[f'price_momentum_{window}'] = np.where(
                df[f'price_ma_{window}'] > 0,
                (df['price'] - df[f'price_ma_{window}']) / df[f'price_ma_{window}'],
                0
            )

        return df

    def _add_cross_sectional_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add cross-sectional features comparing this option to others in the chain.

        Note: Requires grouping by (underlying, timestamp) to get the full chain at each time.
        """
        # Group by underlying and timestamp
        if 'dt' in df.columns:
            df['dt_str'] = df['dt'].astype(str)
            group_keys = ['underlying', 'dt_str']

            # Rank within chain by IV
            df['iv_rank_in_chain'] = df.groupby(group_keys)['iv'].rank(pct=True)

            # Rank by OI
            df['oi_rank_in_chain'] = df.groupby(group_keys)['open_interest'].rank(pct=True)

            # Rank by volume
            df['volume_rank_in_chain'] = df.groupby(group_keys)['volume'].rank(pct=True)

            # Distance to ATM relative to chain
            df['moneyness_rank'] = df.groupby(group_keys)['abs_moneyness'].rank()

            # Clean up temporary column
            df = df.drop('dt_str', axis=1)

        return df

    def get_feature_names(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of feature column names (excluding identifiers and targets).

        Args:
            df: DataFrame with features

        Returns:
            List of feature column names
        """
        exclude_cols = {
            'symbol', 'timestamp', 'dt', 'underlying', 'strike', 'option_type',
            'label_2x', 'time_to_2x_minutes', 'max_future_return',
            # Raw snapshot columns (we use derived features instead)
            'open', 'high', 'low', 'close',
        }

        feature_cols = [col for col in df.columns if col not in exclude_cols]
        return feature_cols


def build_features_for_contract(
    contract_df: pd.DataFrame,
    config: Optional[Config] = None
) -> pd.DataFrame:
    """
    Convenience function to build features for a single contract's history.

    Args:
        contract_df: DataFrame with snapshots for one contract
        config: Configuration object

    Returns:
        DataFrame with features added
    """
    builder = FeatureBuilder(config)
    return builder.build_features(contract_df)


def build_features_for_snapshot(
    current_snapshot: dict,
    recent_history: List[dict],
    config: Optional[Config] = None
) -> pd.Series:
    """
    Build features for a single snapshot in real-time (live inference).

    Args:
        current_snapshot: Current snapshot dict
        recent_history: List of recent snapshot dicts (for lagged features)
        config: Configuration object

    Returns:
        Series with feature values

    Note:
        This is used during live inference where we need features for one snapshot at a time.
    """
    # Combine current with history
    all_snapshots = recent_history + [current_snapshot]

    # Convert to DataFrame
    df = pd.DataFrame(all_snapshots)

    # Build features
    builder = FeatureBuilder(config)
    df_features = builder.build_features(df)

    # Return only the last row (current snapshot)
    return df_features.iloc[-1]
