"""
Model training module.

Handles the complete training pipeline including data splitting,
model training, and saving artifacts.
"""

import pandas as pd
from typing import Optional, Tuple
from pathlib import Path

from .models import Option2xModel, create_model
from .dataset import prepare_dataset, split_data_by_time, create_sample_weights
from ..config import Config, get_config
from ..utils.logging_utils import get_logger
from ..utils.io_utils import save_json

logger = get_logger(__name__)


def train_model(
    df: pd.DataFrame,
    output_dir: str,
    config: Optional[Config] = None,
    use_validation: bool = True,
    use_sample_weights: bool = False
) -> Tuple[Option2xModel, dict]:
    """
    Train a model on the provided dataset.

    Args:
        df: DataFrame with features and labels
        output_dir: Directory to save model and artifacts
        config: Configuration object
        use_validation: Whether to use validation set for early stopping
        use_sample_weights: Whether to use sample weights for class imbalance

    Returns:
        Tuple of (trained_model, training_info)
    """
    logger.info("=" * 80)
    logger.info("Starting model training pipeline")
    logger.info("=" * 80)

    if config is None:
        config = get_config()

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Prepare dataset
    logger.info("Step 1: Preparing dataset")
    X, y, feature_names = prepare_dataset(df, config)

    # Split data
    logger.info("Step 2: Splitting data by time")
    if use_validation:
        train_df, val_df, test_df = split_data_by_time(
            df,
            train_ratio=0.7,
            validation_ratio=0.15
        )

        X_train, y_train, _ = prepare_dataset(train_df, config)
        X_val, y_val, _ = prepare_dataset(val_df, config)
        X_test, y_test, _ = prepare_dataset(test_df, config)

        logger.info(f"Train size: {len(X_train)}, Val size: {len(X_val)}, Test size: {len(X_test)}")
    else:
        train_df, _, test_df = split_data_by_time(
            df,
            train_ratio=0.8,
            validation_ratio=0.0
        )

        X_train, y_train, _ = prepare_dataset(train_df, config)
        X_val, y_val = None, None
        X_test, y_test, _ = prepare_dataset(test_df, config)

        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Create sample weights if needed
    sample_weight = None
    if use_sample_weights:
        logger.info("Creating sample weights for class imbalance")
        sample_weight = create_sample_weights(y_train, method="inverse_freq")

    # Initialize model
    logger.info("Step 3: Initializing model")
    model = create_model(
        model_type=config.model.model_type,
        config=config
    )

    # Train model
    logger.info("Step 4: Training model")
    model.fit(
        X_train, y_train,
        X_val, y_val,
        sample_weight=sample_weight,
        verbose=True
    )

    # Evaluate on test set
    logger.info("Step 5: Evaluating on test set")
    test_proba = model.predict_proba(X_test)[:, 1]
    test_pred = (test_proba >= 0.5).astype(int)

    from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score

    test_metrics = {
        'roc_auc': roc_auc_score(y_test, test_proba),
        'precision': precision_score(y_test, test_pred, zero_division=0),
        'recall': recall_score(y_test, test_pred, zero_division=0),
        'f1': f1_score(y_test, test_pred, zero_division=0),
    }

    logger.info("Test set metrics:")
    for metric, value in test_metrics.items():
        logger.info(f"  {metric}: {value:.4f}")

    # Get feature importance
    logger.info("Step 6: Computing feature importance")
    feature_importance = model.get_feature_importance()

    logger.info("Top 10 features:")
    for idx, row in feature_importance.head(10).iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.2f}")

    # Save model
    logger.info("Step 7: Saving model and artifacts")
    model_dir = Path(output_dir) / "model"
    model.save(str(model_dir))

    # Save feature importance
    feature_importance.to_csv(
        Path(output_dir) / "feature_importance.csv",
        index=False
    )

    # Save training info
    training_info = {
        'train_size': len(X_train),
        'val_size': len(X_val) if X_val is not None else 0,
        'test_size': len(X_test),
        'n_features': len(feature_names),
        'test_metrics': test_metrics,
        'config': config.to_dict(),
    }

    save_json(
        training_info,
        str(Path(output_dir) / "training_info.json")
    )

    logger.info("=" * 80)
    logger.info("Training pipeline complete!")
    logger.info(f"Model saved to: {model_dir}")
    logger.info("=" * 80)

    return model, training_info


def cross_validate_model(
    df: pd.DataFrame,
    config: Optional[Config] = None,
    n_splits: int = 5
) -> pd.DataFrame:
    """
    Perform time-series cross-validation.

    Args:
        df: DataFrame with features and labels
        config: Configuration object
        n_splits: Number of CV splits

    Returns:
        DataFrame with CV results
    """
    logger.info(f"Performing {n_splits}-fold time-series cross-validation")

    if config is None:
        config = get_config()

    from sklearn.metrics import roc_auc_score, precision_score, recall_score

    results = []

    # Sort by time
    df = df.sort_values('timestamp').reset_index(drop=True)
    n = len(df)

    for fold in range(n_splits):
        logger.info(f"Fold {fold + 1}/{n_splits}")

        # Expanding window split
        train_end = int(n * (fold + 1) / (n_splits + 1))
        test_start = train_end
        test_end = int(n * (fold + 2) / (n_splits + 1))

        train_df = df.iloc[:train_end]
        test_df = df.iloc[test_start:test_end]

        # Prepare datasets
        X_train, y_train, _ = prepare_dataset(train_df, config)
        X_test, y_test, _ = prepare_dataset(test_df, config)

        # Train model
        model = create_model(model_type=config.model.model_type, config=config)
        model.fit(X_train, y_train, verbose=False)

        # Evaluate
        test_proba = model.predict_proba(X_test)[:, 1]
        test_pred = (test_proba >= 0.5).astype(int)

        fold_results = {
            'fold': fold + 1,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'roc_auc': roc_auc_score(y_test, test_proba),
            'precision': precision_score(y_test, test_pred, zero_division=0),
            'recall': recall_score(y_test, test_pred, zero_division=0),
        }

        results.append(fold_results)
        logger.info(f"  ROC-AUC: {fold_results['roc_auc']:.4f}")

    results_df = pd.DataFrame(results)

    logger.info("Cross-validation complete!")
    logger.info("Average metrics:")
    for metric in ['roc_auc', 'precision', 'recall']:
        logger.info(f"  {metric}: {results_df[metric].mean():.4f} ± {results_df[metric].std():.4f}")

    return results_df
