"""
Model evaluation module.

Provides comprehensive evaluation including threshold analysis,
calibration, and performance metrics.
"""

import numpy as np
import pandas as pd
from typing import Optional, List, Tuple
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, roc_curve,
    brier_score_loss, confusion_matrix, classification_report
)

from .models import Option2xModel
from ..config import Config, get_config
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def evaluate_model(
    model: Option2xModel,
    X: pd.DataFrame,
    y: pd.Series,
    thresholds: Optional[List[float]] = None,
    return_predictions: bool = False
) -> pd.DataFrame:
    """
    Comprehensive model evaluation.

    Args:
        model: Trained model
        X: Features
        y: True labels
        thresholds: List of probability thresholds to evaluate
        return_predictions: Whether to return predictions DataFrame

    Returns:
        DataFrame with evaluation metrics per threshold
    """
    logger.info(f"Evaluating model on {len(X)} samples")

    if thresholds is None:
        config = get_config()
        thresholds = config.signals.evaluation_thresholds

    # Get predictions
    y_proba = model.predict_proba(X)[:, 1]

    # Calculate metrics for each threshold
    results = []

    for threshold in thresholds:
        y_pred = (y_proba >= threshold).astype(int)

        # Basic metrics
        tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0

        results.append({
            'threshold': threshold,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'specificity': specificity,
            'accuracy': accuracy,
            'true_positives': int(tp),
            'false_positives': int(fp),
            'true_negatives': int(tn),
            'false_negatives': int(fn),
            'total_signals': int(tp + fp),
        })

    results_df = pd.DataFrame(results)

    # Add overall metrics (threshold-independent)
    try:
        roc_auc = roc_auc_score(y, y_proba)
        logger.info(f"ROC-AUC: {roc_auc:.4f}")
    except ValueError:
        roc_auc = np.nan
        logger.warning("Could not compute ROC-AUC (only one class present?)")

    brier_score = brier_score_loss(y, y_proba)
    logger.info(f"Brier score: {brier_score:.4f}")

    # Log results
    logger.info("\nPerformance at different thresholds:")
    logger.info(results_df.to_string(index=False))

    if return_predictions:
        pred_df = pd.DataFrame({
            'y_true': y,
            'y_proba': y_proba,
        })
        return results_df, pred_df
    else:
        return results_df


def analyze_threshold_tradeoffs(
    model: Option2xModel,
    X: pd.DataFrame,
    y: pd.Series,
    df_full: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Analyze precision-recall tradeoff with trading context.

    Args:
        model: Trained model
        X: Features
        y: True labels
        df_full: Full DataFrame with 'max_future_return' for extra analysis

    Returns:
        DataFrame with threshold analysis
    """
    logger.info("Analyzing threshold tradeoffs")

    y_proba = model.predict_proba(X)[:, 1]

    # Precision-recall curve
    precision, recall, thresholds = precision_recall_curve(y, y_proba)

    # For each threshold, calculate metrics
    results = []

    for i, threshold in enumerate(thresholds):
        if i >= len(precision) - 1:
            break

        y_pred = (y_proba >= threshold).astype(int)
        n_signals = y_pred.sum()

        hit_rate = recall[i]  # Same as recall
        precision_val = precision[i]

        result = {
            'threshold': threshold,
            'precision': precision_val,
            'recall': recall[i],
            'n_signals': int(n_signals),
            'hit_rate': hit_rate,
        }

        # If we have max_future_return, analyze actual returns
        if df_full is not None and 'max_future_return' in df_full.columns:
            signal_mask = y_pred == 1
            if signal_mask.sum() > 0:
                avg_max_return = df_full.loc[signal_mask, 'max_future_return'].mean()
                result['avg_max_return'] = avg_max_return

        results.append(result)

    results_df = pd.DataFrame(results)

    # Find optimal threshold (maximize F1)
    results_df['f1'] = 2 * results_df['precision'] * results_df['recall'] / (
        results_df['precision'] + results_df['recall']
    )

    optimal_idx = results_df['f1'].idxmax()
    optimal_threshold = results_df.loc[optimal_idx, 'threshold']

    logger.info(f"\nOptimal threshold (by F1): {optimal_threshold:.4f}")
    logger.info(f"Precision: {results_df.loc[optimal_idx, 'precision']:.4f}")
    logger.info(f"Recall: {results_df.loc[optimal_idx, 'recall']:.4f}")
    logger.info(f"Signals: {results_df.loc[optimal_idx, 'n_signals']:.0f}")

    return results_df


def evaluate_calibration(
    model: Option2xModel,
    X: pd.DataFrame,
    y: pd.Series,
    n_bins: int = 10
) -> pd.DataFrame:
    """
    Evaluate probability calibration.

    Args:
        model: Trained model
        X: Features
        y: True labels
        n_bins: Number of probability bins

    Returns:
        DataFrame with calibration analysis
    """
    logger.info("Evaluating model calibration")

    y_proba = model.predict_proba(X)[:, 1]

    # Create bins
    bins = np.linspace(0, 1, n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    results = []

    for i in range(n_bins):
        bin_mask = (y_proba >= bins[i]) & (y_proba < bins[i + 1])
        n_samples = bin_mask.sum()

        if n_samples > 0:
            mean_predicted = y_proba[bin_mask].mean()
            mean_actual = y[bin_mask].mean()

            results.append({
                'bin': i + 1,
                'bin_center': bin_centers[i],
                'n_samples': int(n_samples),
                'mean_predicted_prob': mean_predicted,
                'actual_positive_rate': mean_actual,
                'calibration_error': abs(mean_predicted - mean_actual),
            })

    results_df = pd.DataFrame(results)

    # Expected Calibration Error (ECE)
    total_samples = len(y)
    ece = sum(
        (row['n_samples'] / total_samples) * row['calibration_error']
        for _, row in results_df.iterrows()
    )

    logger.info(f"Expected Calibration Error (ECE): {ece:.4f}")
    logger.info("\nCalibration by bin:")
    logger.info(results_df.to_string(index=False))

    return results_df


def generate_evaluation_report(
    model: Option2xModel,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    output_path: Optional[str] = None,
    df_full: Optional[pd.DataFrame] = None
) -> dict:
    """
    Generate comprehensive evaluation report.

    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
        output_path: Optional path to save report
        df_full: Full DataFrame for additional analysis

    Returns:
        Dictionary with all evaluation results
    """
    logger.info("=" * 80)
    logger.info("Generating comprehensive evaluation report")
    logger.info("=" * 80)

    report = {}

    # 1. Overall metrics
    logger.info("\n1. Overall Metrics")
    metrics_df = evaluate_model(model, X_test, y_test)
    report['threshold_metrics'] = metrics_df

    # 2. Threshold analysis
    logger.info("\n2. Threshold Tradeoff Analysis")
    tradeoff_df = analyze_threshold_tradeoffs(model, X_test, y_test, df_full)
    report['threshold_tradeoffs'] = tradeoff_df

    # 3. Calibration
    logger.info("\n3. Calibration Analysis")
    calibration_df = evaluate_calibration(model, X_test, y_test)
    report['calibration'] = calibration_df

    # 4. Feature importance
    logger.info("\n4. Feature Importance")
    importance_df = model.get_feature_importance()
    report['feature_importance'] = importance_df

    logger.info("Top 20 features:")
    logger.info(importance_df.head(20).to_string(index=False))

    # Save report if path provided
    if output_path:
        logger.info(f"\nSaving evaluation report to {output_path}")

        from pathlib import Path
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        metrics_df.to_csv(output_dir / "threshold_metrics.csv", index=False)
        tradeoff_df.to_csv(output_dir / "threshold_tradeoffs.csv", index=False)
        calibration_df.to_csv(output_dir / "calibration.csv", index=False)
        importance_df.to_csv(output_dir / "feature_importance.csv", index=False)

        logger.info("Report saved successfully")

    logger.info("=" * 80)
    logger.info("Evaluation report complete")
    logger.info("=" * 80)

    return report
