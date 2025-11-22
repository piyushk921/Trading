"""Tests for feature engineering."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from options_ml.features.feature_builder import FeatureBuilder
from options_ml.config import Config


@pytest.fixture
def sample_data():
    """Create sample option snapshot data for testing."""
    data = []
    base_time = datetime(2025, 11, 19, 9, 15, 0)

    for i in range(10):
        snapshot = {
            'symbol': 'TEST_1000.0_CE',
            'underlying': 'TEST',
            'strike': 1000.0,
            'option_type': 'CE',
            'timestamp': (base_time + pd.Timedelta(minutes=i*10)).strftime('%Y-%m-%d %H:%M:%S'),
            'spot_price': 1000.0 + i,
            'price': 10.0 + i * 0.5,
            'volume': 100000 + i * 1000,
            'open_interest': 500000,
            'oi_change': 1000,
            'bid_price': 10.0 + i * 0.5,
            'ask_price': 10.1 + i * 0.5,
            'bid_qty': 1000,
            'ask_qty': 1000,
            'iv': 15.0 + i * 0.1,
            'delta': 0.5,
            'gamma': 0.02,
            'theta': -0.5,
            'vega': 0.3,
            'open': 0.0,
            'high': 0.0,
            'low': 0.0,
            'close': 0.0,
        }
        data.append(snapshot)

    return pd.DataFrame(data)


def test_feature_builder_initialization():
    """Test FeatureBuilder initialization."""
    config = Config()
    builder = FeatureBuilder(config)
    assert builder.config is not None
    assert builder.feature_config is not None


def test_build_features_shape(sample_data):
    """Test that feature building produces correct shape."""
    builder = FeatureBuilder()
    df_features = builder.build_features(sample_data)

    # Should have same number of rows
    assert len(df_features) == len(sample_data)

    # Should have more columns (original + features)
    assert len(df_features.columns) > len(sample_data.columns)


def test_static_features(sample_data):
    """Test static feature generation."""
    builder = FeatureBuilder()
    df_features = builder.build_features(sample_data)

    # Check moneyness features exist
    assert 'moneyness' in df_features.columns
    assert 'log_moneyness' in df_features.columns
    assert 'abs_moneyness' in df_features.columns

    # Check option type encoding
    assert 'is_call' in df_features.columns
    assert 'is_put' in df_features.columns
    assert df_features['is_call'].sum() == len(sample_data)  # All are CE


def test_lagged_features(sample_data):
    """Test lagged feature generation."""
    builder = FeatureBuilder()
    df_features = builder.build_features(sample_data)

    # Check that lagged features exist
    assert 'price_return_1' in df_features.columns
    assert 'spot_return_1' in df_features.columns

    # First row should have NaN for lag-1 features
    assert pd.isna(df_features.iloc[0]['price_return_1'])

    # Later rows should have values
    assert not pd.isna(df_features.iloc[1]['price_return_1'])


def test_no_future_leakage(sample_data):
    """Test that features don't use future data."""
    builder = FeatureBuilder()
    df_features = builder.build_features(sample_data)

    # For row i, lagged features should only use data from rows <= i
    # Check that row 5's lag-1 feature uses data from row 4
    row_4_price = sample_data.iloc[4]['price']
    row_5_price = sample_data.iloc[5]['price']

    expected_return = (row_5_price / row_4_price) - 1.0
    actual_return = df_features.iloc[5]['price_return_1']

    assert abs(expected_return - actual_return) < 0.001


def test_feature_names():
    """Test feature name extraction."""
    sample_data = pd.DataFrame({
        'symbol': ['TEST'],
        'timestamp': ['2025-11-19 09:15:00'],
        'price': [10.0],
        'label_2x': [0],
        'some_feature': [1.0],
    })

    builder = FeatureBuilder()
    feature_names = builder.get_feature_names(sample_data)

    # Should exclude identifiers and labels
    assert 'symbol' not in feature_names
    assert 'timestamp' not in feature_names
    assert 'label_2x' not in feature_names

    # Should include actual features
    assert 'some_feature' in feature_names


def test_missing_values_handled(sample_data):
    """Test that missing values are handled properly."""
    # Introduce some NaN values
    sample_data_with_nan = sample_data.copy()
    sample_data_with_nan.loc[5, 'volume'] = np.nan

    builder = FeatureBuilder()
    df_features = builder.build_features(sample_data_with_nan)

    # Should complete without errors
    assert len(df_features) == len(sample_data)
