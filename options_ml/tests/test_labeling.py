"""Tests for label building."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from options_ml.labeling.label_builder import LabelBuilder
from options_ml.config import Config


@pytest.fixture
def simple_contract_data():
    """Create simple contract data for testing label logic."""
    base_time = datetime(2025, 11, 19, 9, 15, 0)

    data = []

    # Create a scenario where price doubles at snapshot 5
    prices = [10.0, 10.5, 11.0, 15.0, 18.0, 20.0, 19.0, 18.5, 18.0, 17.0]

    for i, price in enumerate(prices):
        snapshot = {
            'symbol': 'TEST_1000.0_CE',
            'timestamp': (base_time + pd.Timedelta(minutes=i*10)).strftime('%Y-%m-%d %H:%M:%S'),
            'dt': base_time + pd.Timedelta(minutes=i*10),
            'price': price,
        }
        data.append(snapshot)

    return pd.DataFrame(data)


def test_label_builder_initialization():
    """Test LabelBuilder initialization."""
    config = Config()
    builder = LabelBuilder(config)
    assert builder.config is not None
    assert builder.label_config is not None


def test_label_2x_detection(simple_contract_data):
    """Test that 2x labels are correctly assigned."""
    builder = LabelBuilder()
    df_labeled = builder.build_labels(simple_contract_data)

    # Row 0: price=10.0, target=20.0, achieved at row 5
    assert df_labeled.iloc[0]['label_2x'] == 1

    # Row 1: price=10.5, target=21.0, never achieved
    assert df_labeled.iloc[1]['label_2x'] == 0

    # Row 5 onwards: price is already high, can't double
    assert df_labeled.iloc[5]['label_2x'] == 0


def test_time_to_2x(simple_contract_data):
    """Test time_to_2x calculation."""
    builder = LabelBuilder()
    df_labeled = builder.build_labels(simple_contract_data)

    # Row 0: should have time_to_2x for when 20.0 is hit (row 5, which is 50 minutes later)
    row_0_time_to_2x = df_labeled.iloc[0]['time_to_2x_minutes']
    assert not pd.isna(row_0_time_to_2x)
    assert row_0_time_to_2x == 50.0  # 5 snapshots * 10 minutes


def test_max_future_return(simple_contract_data):
    """Test max_future_return calculation."""
    builder = LabelBuilder()
    df_labeled = builder.build_labels(simple_contract_data)

    # Row 0: price=10.0, max future=20.0, return=100%
    row_0_max_return = df_labeled.iloc[0]['max_future_return']
    assert not pd.isna(row_0_max_return)
    assert abs(row_0_max_return - 100.0) < 0.1

    # Last row: no future data, max return should be 0
    last_row_max_return = df_labeled.iloc[-1]['max_future_return']
    assert abs(last_row_max_return - 0.0) < 0.1


def test_no_data_leakage(simple_contract_data):
    """Test that labels only use future data."""
    builder = LabelBuilder()
    df_labeled = builder.build_labels(simple_contract_data)

    # For each row, verify that label only considers future rows
    for i in range(len(simple_contract_data) - 1):
        current_price = simple_contract_data.iloc[i]['price']
        target_price = current_price * 2.0

        # Get max price in future
        future_prices = simple_contract_data.iloc[i+1:]['price']
        max_future_price = future_prices.max() if len(future_prices) > 0 else current_price

        label = df_labeled.iloc[i]['label_2x']

        if max_future_price >= target_price:
            assert label == 1, f"Row {i} should have label=1"
        else:
            assert label == 0, f"Row {i} should have label=0"


def test_custom_multiplier():
    """Test custom target multiplier."""
    base_time = datetime(2025, 11, 19, 9, 15, 0)

    # Create data where price goes 1.5x but not 2x
    data = []
    prices = [10.0, 11.0, 12.0, 14.0, 15.0, 14.5]

    for i, price in enumerate(prices):
        snapshot = {
            'symbol': 'TEST_1000.0_CE',
            'timestamp': (base_time + pd.Timedelta(minutes=i*10)).strftime('%Y-%m-%d %H:%M:%S'),
            'dt': base_time + pd.Timedelta(minutes=i*10),
            'price': price,
        }
        data.append(snapshot)

    df = pd.DataFrame(data)

    # Test with 2x multiplier (default)
    config_2x = Config()
    config_2x.labels.target_multiplier = 2.0
    builder_2x = LabelBuilder(config_2x)
    df_labeled_2x = builder_2x.build_labels(df)

    # Should not hit 2x
    assert df_labeled_2x.iloc[0]['label_2x'] == 0

    # Test with 1.5x multiplier
    config_1_5x = Config()
    config_1_5x.labels.target_multiplier = 1.5
    builder_1_5x = LabelBuilder(config_1_5x)
    df_labeled_1_5x = builder_1_5x.build_labels(df)

    # Should hit 1.5x
    assert df_labeled_1_5x.iloc[0]['label_2x'] == 1


def test_horizon_limiting():
    """Test that horizon limits lookahead."""
    base_time = datetime(2025, 11, 19, 9, 15, 0)

    # Create data where 2x is hit after 60 minutes
    data = []
    prices = [10.0, 11.0, 12.0, 15.0, 18.0, 20.0, 22.0]  # 2x at index 5 (50 min)

    for i, price in enumerate(prices):
        snapshot = {
            'symbol': 'TEST_1000.0_CE',
            'timestamp': (base_time + pd.Timedelta(minutes=i*10)).strftime('%Y-%m-%d %H:%M:%S'),
            'dt': base_time + pd.Timedelta(minutes=i*10),
            'price': price,
        }
        data.append(snapshot)

    df = pd.DataFrame(data)

    # Test with 30-minute horizon (should NOT see the 2x)
    config_30min = Config()
    config_30min.labels.horizon_minutes = 30
    builder_30min = LabelBuilder(config_30min)
    df_labeled_30min = builder_30min.build_labels(df)

    # Row 0: within 30 min, can't reach 2x
    assert df_labeled_30min.iloc[0]['label_2x'] == 0

    # Test with 60-minute horizon (should see the 2x)
    config_60min = Config()
    config_60min.labels.horizon_minutes = 60
    builder_60min = LabelBuilder(config_60min)
    df_labeled_60min = builder_60min.build_labels(df)

    # Row 0: within 60 min, can reach 2x
    assert df_labeled_60min.iloc[0]['label_2x'] == 1
