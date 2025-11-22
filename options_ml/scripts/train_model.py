#!/usr/bin/env python3
"""
Train a machine learning model to predict 2x option price increases.

This script:
1. Loads the prepared training data from a Parquet file.
2. Defines the feature set to be used for training.
3. Splits the data into training and validation sets.
4. Trains an XGBoost classifier model.
5. Evaluates the model on the validation set and prints a classification report.
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Add parent directory to path to allow for package imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from options_ml.data.loader import load_training_data
from options_ml.utils.logging_utils import setup_logger

logger = setup_logger(__name__, log_file="logs/train_model.log")

def get_feature_names(df: pd.DataFrame) -> list[str]:
    """
    Get the list of feature names from the DataFrame.

    This excludes identifier columns, metadata, and the label itself.

    Args:
        df: The input DataFrame.

    Returns:
        A list of strings with the column names to be used as features.
    """
    logger.info("Identifying feature columns...")

    # Columns to exclude from the feature set
    cols_to_exclude = [
        'symbol', 'timestamp', 'dt', 'date', 'price', 'source_file',
        'label_2x', 'time_to_2x_minutes', 'max_future_return',
        'underlying', 'strike', 'option_type', 'expiry'
    ]

    # Get all columns that are not in the exclusion list
    feature_names = [col for col in df.columns if col not in cols_to_exclude]

    logger.info(f"Identified {len(feature_names)} feature columns.")
    return feature_names

def main():
    """Main function to train and evaluate the model."""
    parser = argparse.ArgumentParser(description="Train an XGBoost model on processed options data.")
    parser.add_argument(
        "--input-file",
        type=str,
        required=True,
        help="Path to the processed training data Parquet file."
    )
    parser.add_argument(
        "--validation-size",
        type=float,
        default=0.2,
        help="Proportion of the dataset to use for validation (default: 0.2 for 20%)."
    )
    parser.add_argument(
        "--output-model-file",
        type=str,
        default="model.json",
        help="Path to save the trained model file (default: model.json)."
    )
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("TRAINING PREDICTION MODEL")
    logger.info("=" * 80)

    # Step 1: Load the data
    logger.info(f"Step 1: Loading data from {args.input_file}")
    try:
        df = load_training_data(args.input_file)
    except FileNotFoundError:
        logger.error(f"Error: Input file not found at {args.input_file}")
        sys.exit(1)

    if df.empty:
        logger.error("The loaded DataFrame is empty. Cannot proceed with training.")
        sys.exit(1)

    # Step 2: Define features and target, and clean the data
    logger.info("Step 2: Defining features, cleaning data, and setting target variable")
    feature_names = get_feature_names(df)
    X = df[feature_names]
    y = df['label_2x']

    # Clean the data: Replace infinite values with 0
    # This is a critical step to prevent XGBoost from crashing on invalid inputs.
    logger.info("Cleaning data by replacing infinite values...")
    X.replace([np.inf, -np.inf], 0, inplace=True)
    logger.info("Data cleaning complete.")

    if X.empty or y.empty:
        logger.error("Feature set or target variable is empty. Cannot train the model.")
        sys.exit(1)

    # Step 3: Split data into training and validation sets
    logger.info(f"Step 3: Splitting data into training and validation sets ({1-args.validation_size:.0%} train / {args.validation_size:.0%} validation)")
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=args.validation_size, random_state=42, stratify=y
    )
    logger.info(f"Training set size: {len(X_train)} samples")
    logger.info(f"Validation set size: {len(X_val)} samples")

    # Step 4: Train the XGBoost model
    logger.info("Step 4: Training the XGBoost model")

    # Handle class imbalance by calculating scale_pos_weight
    # This tells the model to pay more attention to the rare positive class
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    logger.info(f"Calculated scale_pos_weight for class imbalance: {scale_pos_weight:.2f}")

    model = xgb.XGBClassifier(
        objective='binary:logistic',
        eval_metric='logloss',
        use_label_encoder=False,
        scale_pos_weight=scale_pos_weight,
        random_state=42
    )

    model.fit(X_train, y_train)
    logger.info("Model training complete.")

    # Step 5: Evaluate the model on the validation set
    logger.info("Step 5: Evaluating model performance on the validation set")
    y_pred = model.predict(X_val)

    logger.info("\n" + "=" * 80)
    logger.info("MODEL EVALUATION REPORT")
    logger.info("=" * 80)

    report = classification_report(y_val, y_pred, target_names=['No 2x', 'Achieved 2x'])
    print(report)
    logger.info("\n" + report)

    # Step 6: Save the trained model
    logger.info("Step 6: Saving the trained model")
    model.save_model(args.output_model_file)
    logger.info(f"Model saved successfully to {args.output_model_file}")

    logger.info("=" * 80)
    logger.info("\nDONE: Model training and evaluation complete!")

if __name__ == "__main__":
    main()
