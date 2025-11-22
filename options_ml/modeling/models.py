"""
ML model wrapper for options 2x prediction.

Provides a unified interface for LightGBM and XGBoost models.
"""

import joblib
import numpy as np
import pandas as pd
from typing import Optional, List, Any
from pathlib import Path

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

from ..config import Config, get_config
from ..utils.logging_utils import get_logger
from ..utils.io_utils import save_json, load_json

logger = get_logger(__name__)


class Option2xModel:
    """
    Wrapper class for option 2x prediction models.

    Provides a consistent interface for training, prediction, and serialization.
    """

    def __init__(
        self,
        model_type: str = "lightgbm",
        config: Optional[Config] = None,
        **model_params
    ):
        """
        Initialize model.

        Args:
            model_type: Type of model ("lightgbm" or "xgboost")
            config: Configuration object
            **model_params: Additional model parameters (override config)
        """
        self.model_type = model_type
        self.config = config or get_config()
        self.model = None
        self.feature_names: Optional[List[str]] = None
        self.model_params = self._get_model_params(**model_params)

        # Validate model type is available
        if model_type == "lightgbm" and not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM not installed. Install with: pip install lightgbm")
        if model_type == "xgboost" and not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost not installed. Install with: pip install xgboost")

        logger.info(f"Initialized {model_type} model")

    def _get_model_params(self, **overrides) -> dict:
        """Get model parameters from config with optional overrides."""
        params = {
            'n_estimators': self.config.model.n_estimators,
            'learning_rate': self.config.model.learning_rate,
            'max_depth': self.config.model.max_depth,
            'num_leaves': self.config.model.num_leaves,
            'min_child_samples': self.config.model.min_child_samples,
            'subsample': self.config.model.subsample,
            'colsample_bytree': self.config.model.colsample_bytree,
            'reg_alpha': self.config.model.reg_alpha,
            'reg_lambda': self.config.model.reg_lambda,
            'random_state': self.config.model.random_state,
            'n_jobs': self.config.model.n_jobs,
        }

        # Apply overrides
        params.update(overrides)
        return params

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        sample_weight: Optional[np.ndarray] = None,
        verbose: bool = True
    ) -> "Option2xModel":
        """
        Train the model.

        Args:
            X: Training features
            y: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            sample_weight: Sample weights (optional)
            verbose: Whether to print training progress

        Returns:
            Self for chaining
        """
        logger.info(f"Training {self.model_type} model on {len(X)} samples")

        # Store feature names
        self.feature_names = list(X.columns)

        # Calculate class weight if needed
        if self.config.model.scale_pos_weight is None:
            neg_count = (y == 0).sum()
            pos_count = (y == 1).sum()
            scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
            logger.info(f"Auto-calculated scale_pos_weight: {scale_pos_weight:.2f}")
        else:
            scale_pos_weight = self.config.model.scale_pos_weight

        if self.model_type == "lightgbm":
            self.model = self._train_lightgbm(
                X, y, X_val, y_val, sample_weight, scale_pos_weight, verbose
            )
        elif self.model_type == "xgboost":
            self.model = self._train_xgboost(
                X, y, X_val, y_val, sample_weight, scale_pos_weight, verbose
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        logger.info("Training complete")
        return self

    def _train_lightgbm(
        self,
        X, y, X_val, y_val, sample_weight, scale_pos_weight, verbose
    ) -> Any:
        """Train LightGBM model."""
        params = self.model_params.copy()
        params['scale_pos_weight'] = scale_pos_weight
        params['verbose'] = -1 if not verbose else 100

        eval_set = [(X_val, y_val)] if X_val is not None else None

        model = lgb.LGBMClassifier(**params)
        model.fit(
            X, y,
            sample_weight=sample_weight,
            eval_set=eval_set,
            callbacks=[lgb.early_stopping(self.config.model.early_stopping_rounds)] if eval_set else None,
        )

        return model

    def _train_xgboost(
        self,
        X, y, X_val, y_val, sample_weight, scale_pos_weight, verbose
    ) -> Any:
        """Train XGBoost model."""
        params = self.model_params.copy()
        params['scale_pos_weight'] = scale_pos_weight
        params['verbosity'] = 2 if verbose else 0

        eval_set = [(X_val, y_val)] if X_val is not None else None

        model = xgb.XGBClassifier(**params)
        model.fit(
            X, y,
            sample_weight=sample_weight,
            eval_set=eval_set,
            early_stopping_rounds=self.config.model.early_stopping_rounds if eval_set else None,
            verbose=verbose,
        )

        return model

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict probabilities.

        Args:
            X: Features

        Returns:
            Array of shape (n_samples, 2) with class probabilities
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        # Ensure feature order matches training
        if self.feature_names is not None:
            X = X[self.feature_names]

        return self.model.predict_proba(X)

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """
        Predict class labels.

        Args:
            X: Features
            threshold: Probability threshold for positive class

        Returns:
            Array of predicted labels (0 or 1)
        """
        proba = self.predict_proba(X)
        return (proba[:, 1] >= threshold).astype(int)

    def get_feature_importance(self, importance_type: str = "gain") -> pd.DataFrame:
        """
        Get feature importance.

        Args:
            importance_type: Type of importance ("gain", "split", etc.)

        Returns:
            DataFrame with feature names and importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        if self.model_type == "lightgbm":
            importance = self.model.booster_.feature_importance(importance_type=importance_type)
        elif self.model_type == "xgboost":
            importance = self.model.feature_importances_
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        })
        df = df.sort_values('importance', ascending=False).reset_index(drop=True)

        return df

    def save(self, model_dir: str) -> None:
        """
        Save model to disk.

        Args:
            model_dir: Directory to save model files
        """
        if self.model is None:
            raise ValueError("No model to save")

        Path(model_dir).mkdir(parents=True, exist_ok=True)

        # Save model
        model_path = Path(model_dir) / "model.pkl"
        joblib.dump(self.model, model_path)
        logger.info(f"Model saved to {model_path}")

        # Save metadata
        metadata = {
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'model_params': self.model_params,
        }
        metadata_path = Path(model_dir) / "metadata.json"
        save_json(metadata, str(metadata_path))
        logger.info(f"Metadata saved to {metadata_path}")

    @classmethod
    def load(cls, model_dir: str, config: Optional[Config] = None) -> "Option2xModel":
        """
        Load model from disk.

        Args:
            model_dir: Directory containing model files
            config: Configuration object

        Returns:
            Loaded Option2xModel instance
        """
        # Load metadata
        metadata_path = Path(model_dir) / "metadata.json"
        metadata = load_json(str(metadata_path))

        # Create instance
        instance = cls(
            model_type=metadata['model_type'],
            config=config,
            **metadata['model_params']
        )

        # Load model
        model_path = Path(model_dir) / "model.pkl"
        instance.model = joblib.load(model_path)
        instance.feature_names = metadata['feature_names']

        logger.info(f"Model loaded from {model_dir}")
        return instance


def create_model(
    model_type: str = "lightgbm",
    config: Optional[Config] = None,
    **model_params
) -> Option2xModel:
    """
    Factory function to create a model.

    Args:
        model_type: Type of model ("lightgbm" or "xgboost")
        config: Configuration object
        **model_params: Additional model parameters

    Returns:
        Option2xModel instance
    """
    return Option2xModel(model_type=model_type, config=config, **model_params)
