"""Tests for modeling components."""

import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil

from options_ml.modeling.models import Option2xModel
from options_ml.modeling.dataset import prepare_dataset
from options_ml.config import Config


@pytest.fixture
def sample_training_data():
    """Create sample training data."""
    np.random.seed(42)

    n_samples = 200
    n_features = 10

    # Create synthetic features
    X = np.random.randn(n_samples, n_features)

    # Create synthetic labels (20% positive)
    y = np.random.choice([0, 1], size=n_samples, p=[0.8, 0.2])

    # Create DataFrame
    data = {f'feature_{i}': X[:, i] for i in range(n_features)}
    data['label_2x'] = y
    data['symbol'] = 'TEST'
    data['timestamp'] = pd.date_range('2025-01-01', periods=n_samples, freq='10T')

    return pd.DataFrame(data)


def test_model_initialization():
    """Test model initialization."""
    model = Option2xModel(model_type='lightgbm')
    assert model.model_type == 'lightgbm'
    assert model.model is None  # Not trained yet


def test_model_fit_predict(sample_training_data):
    """Test basic model training and prediction."""
    # Prepare dataset
    X, y, feature_names = prepare_dataset(sample_training_data)

    # Split data
    n_train = int(len(X) * 0.8)
    X_train, X_test = X[:n_train], X[n_train:]
    y_train, y_test = y[:n_train], y[n_train:]

    # Train model
    model = Option2xModel(model_type='lightgbm')
    model.fit(X_train, y_train, verbose=False)

    # Model should be trained
    assert model.model is not None
    assert model.feature_names == feature_names

    # Make predictions
    y_proba = model.predict_proba(X_test)

    # Check output shape
    assert y_proba.shape == (len(X_test), 2)

    # Check probabilities are valid
    assert np.all(y_proba >= 0)
    assert np.all(y_proba <= 1)
    assert np.allclose(y_proba.sum(axis=1), 1.0)


def test_model_save_load(sample_training_data):
    """Test model serialization."""
    # Prepare and train model
    X, y, feature_names = prepare_dataset(sample_training_data)

    model = Option2xModel(model_type='lightgbm')
    model.fit(X, y, verbose=False)

    # Get predictions before saving
    y_proba_before = model.predict_proba(X)

    # Save to temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        model.save(temp_dir)

        # Load model
        loaded_model = Option2xModel.load(temp_dir)

        # Check loaded model
        assert loaded_model.model_type == model.model_type
        assert loaded_model.feature_names == model.feature_names

        # Get predictions from loaded model
        y_proba_after = loaded_model.predict_proba(X)

        # Predictions should be identical
        np.testing.assert_array_almost_equal(y_proba_before, y_proba_after)

    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def test_feature_importance(sample_training_data):
    """Test feature importance extraction."""
    X, y, feature_names = prepare_dataset(sample_training_data)

    model = Option2xModel(model_type='lightgbm')
    model.fit(X, y, verbose=False)

    # Get feature importance
    importance_df = model.get_feature_importance()

    # Check output
    assert len(importance_df) == len(feature_names)
    assert 'feature' in importance_df.columns
    assert 'importance' in importance_df.columns

    # Check sorted descending
    assert importance_df['importance'].is_monotonic_decreasing


def test_prepare_dataset():
    """Test dataset preparation."""
    # Create sample data
    data = {
        'symbol': ['TEST'] * 10,
        'timestamp': pd.date_range('2025-01-01', periods=10, freq='10T'),
        'label_2x': np.random.choice([0, 1], 10),
        'feature_1': np.random.randn(10),
        'feature_2': np.random.randn(10),
        'underlying': ['TEST'] * 10,  # Should be excluded
    }
    df = pd.DataFrame(data)

    # Prepare dataset
    X, y, feature_names = prepare_dataset(df)

    # Check shapes
    assert len(X) == 10
    assert len(y) == 10
    assert len(feature_names) == 2  # Only feature_1 and feature_2

    # Check excluded columns
    assert 'symbol' not in X.columns
    assert 'label_2x' not in X.columns
    assert 'underlying' not in X.columns

    # Check included columns
    assert 'feature_1' in X.columns
    assert 'feature_2' in X.columns
