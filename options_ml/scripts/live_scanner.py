#!/usr/bin/env python3
"""
Live scanner to predict 2x option price increases in real-time.

This script:
1. Loads a pre-trained XGBoost model.
2. Enters a loop to continuously fetch live market data.
3. Maintains a history of recent data to calculate features.
4. Makes predictions on the latest data point.
5. Generates a "BUY" signal if the prediction confidence is high.
6. Sends a notification (currently a print statement).
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import xgboost as xgb
import time
from collections import deque

# Add parent directory to path to allow for package imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from options_ml.utils.logging_utils import setup_logger

logger = setup_logger(__name__, log_file="logs/live_scanner.log")

# --- Placeholder Functions (to be replaced with real implementations) ---

def fetch_live_data() -> pd.DataFrame:
    """
    *** PLACEHOLDER ***
    This function should connect to your live data feed and return the latest
    snapshot for all relevant option contracts.

    It must return a DataFrame with columns like:
    ['symbol', 'timestamp', 'price', 'volume', 'iv', 'delta', etc.]
    """
    # For now, we simulate receiving data for a few contracts
    symbols = ['NIFTY_20251128_19500_CE', 'BANKNIFTY_20251128_44000_PE']
    data = []
    for symbol in symbols:
        data.append({
            'symbol': symbol,
            'timestamp': pd.Timestamp.now(),
            'price': np.random.uniform(10, 20),
            'volume': np.random.randint(1000, 5000),
            'iv': np.random.uniform(15, 25),
            'delta': np.random.uniform(0.4, 0.6)
        })
    return pd.DataFrame(data)

# Global bot instance
TELEGRAM_BOT = None

def initialize_telegram_bot(token: str):
    """Initializes the global Telegram bot instance."""
    global TELEGRAM_BOT
    if token:
        try:
            from telegram import Bot
            TELEGRAM_BOT = Bot(token=token)
            logger.info("Telegram bot initialized successfully.")
        except ImportError:
            logger.warning("`python-telegram-bot` is not installed. Notifications will be printed to console.")
            TELEGRAM_BOT = None
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            TELEGRAM_BOT = None

def send_notification(chat_id: str, symbol: str, price: float, confidence: float):
    """
    Sends a formatted message to a specified Telegram chat.
    Falls back to console output if the bot is not initialized.
    """
    message = (
        f"🚀 *Potential 2x Signal!* 🚀\n\n"
        f"*Symbol:* `{symbol}`\n"
        f"*Current Price:* `{price}`\n"
        f"*Confidence:* `{confidence:.1%}`"
    )

    if TELEGRAM_BOT and chat_id:
        try:
            TELEGRAM_BOT.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='MarkdownV2'
            )
            logger.info(f"Sent Telegram notification for {symbol}.")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            print(f"\n--- TELEGRAM FAILED ---\n{message}\n-----------------------\n")
    else:
        # Fallback to console if bot is not configured
        logger.info("--- (PREVIEW) SENDING NOTIFICATION ---")
        logger.info(message)
        print("\n" + message + "\n")
        logger.info("------------------------------------")

# --- Core Logic ---

class LiveFeatureCalculator:
    """Manages historical data and calculates features in real-time."""
    def __init__(self, history_length: str = '30min'):
        self.history = pd.DataFrame()
        self.history_length = pd.Timedelta(history_length)

    def update_and_calculate(self, new_data: pd.DataFrame) -> pd.DataFrame:
        """
        Appends new data, trims history, and calculates features for the latest snapshot.
        """
        # Append new data
        self.history = pd.concat([self.history, new_data], ignore_index=True)

        # Drop duplicates and sort
        self.history.drop_duplicates(subset=['symbol', 'timestamp'], keep='last', inplace=True)
        self.history.sort_values('timestamp', inplace=True)

        # Trim history to keep it within the desired window
        cutoff = pd.Timestamp.now() - self.history_length
        self.history = self.history[self.history['timestamp'] >= cutoff]

        # Calculate features for the latest data points
        latest_features = self.history.groupby('symbol').apply(self._calculate_features_for_group, include_groups=False)

        return latest_features.reset_index()

    def _calculate_features_for_group(self, group: pd.DataFrame) -> pd.Series:
        """Calculates features for the most recent row in a group."""
        group = group.set_index('timestamp').sort_index()

        # Create an explicit copy to avoid SettingWithCopyWarning
        latest = group.iloc[-1:].copy()

        # --- This logic should mirror the feature engineering scripts ---
        # Price momentum (rate of change)
        for window in ['5min', '15min']:
            # Use .loc to ensure we are setting values on the DataFrame directly
            latest.loc[:, f'price_roc_{window}'] = group['price'].pct_change(freq=window).iloc[-1]

        # Moving averages
        for col in ['price', 'volume', 'iv', 'delta']:
            if col in group.columns:
                for window in ['10min']:
                    latest.loc[:, f'{col}_ma_{window}'] = group[col].rolling(window).mean().iloc[-1]

        # Volume spike
        if 'volume_ma_10min' in latest.columns:
            latest.loc[:, 'volume_spike_ratio'] = latest['volume'] / (latest['volume_ma_10min'] + 1)

        return latest.iloc[0] # Return as a Series

def main():
    """Main function to run the live scanner."""
    parser = argparse.ArgumentParser(description="Live scanner for options trading signals.")
    parser.add_argument(
        "--model-file",
        type=str,
        default="model.json",
        help="Path to the trained XGBoost model file."
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Seconds to wait between fetching live data (default: 5)."
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.8,
        help="Probability threshold to trigger a signal (default: 0.8 for 80%)."
    )
    parser.add_argument(
        "--telegram-token",
        type=str,
        help="Your Telegram Bot token for sending notifications."
    )
    parser.add_argument(
        "--telegram-chat-id",
        type=str,
        help="The destination Telegram chat ID for notifications."
    )
    args = parser.parse_args()

    # Initialize the Telegram bot if a token is provided
    initialize_telegram_bot(args.telegram_token)

    logger.info("=" * 80)
    logger.info("STARTING LIVE OPTIONS SCANNER")
    logger.info("=" * 80)

    # Step 1: Load the trained model
    logger.info(f"Loading model from {args.model_file}...")
    try:
        model = xgb.XGBClassifier()
        model.load_model(args.model_file)
        logger.info("Model loaded successfully.")
    except (xgb.core.XGBoostError, FileNotFoundError):
        logger.error(f"Error: Could not load model from {args.model_file}. Make sure the file exists.")
        sys.exit(1)

    # Initialize feature calculator
    feature_calculator = LiveFeatureCalculator()

    logger.info("Scanner is running. Press Ctrl+C to stop.")

    # Main loop
    while True:
        try:
            # Step 2: Fetch live data
            live_data = fetch_live_data()
            if live_data.empty:
                time.sleep(args.poll_interval)
                continue

            # Step 3: Calculate features for the new data
            latest_features_df = feature_calculator.update_and_calculate(live_data)

            if latest_features_df.empty:
                time.sleep(args.poll_interval)
                continue

            # Step 4: Make predictions
            # Ensure the feature columns match what the model was trained on
            features_for_prediction = [col for col in model.feature_names_in_ if col in latest_features_df.columns]
            X_live = latest_features_df[features_for_prediction]

            # Handle missing columns by filling with 0 in a single, efficient operation
            missing_cols = set(model.feature_names_in_) - set(X_live.columns)
            if missing_cols:
                # Create a DataFrame of zeros for the missing columns
                missing_df = pd.DataFrame(0, index=X_live.index, columns=list(missing_cols))
                # Concatenate along the columns axis
                X_live = pd.concat([X_live, missing_df], axis=1)

            # Ensure the column order matches the model's expectations exactly
            X_live = X_live[model.feature_names_in_]

            if not X_live.empty:
                probabilities = model.predict_proba(X_live)

                # The second column is the probability of the positive class (Achieved 2x)
                positive_probabilities = probabilities[:, 1]

                # Step 5: Generate signals
                for i, prob in enumerate(positive_probabilities):
                    if prob >= args.confidence_threshold:
                        symbol = latest_features_df.iloc[i]['symbol']
                        price = latest_features_df.iloc[i]['price']
                        send_notification(
                            chat_id=args.telegram_chat_id,
                            symbol=symbol,
                            price=price,
                            confidence=prob
                        )

            # Wait for the next poll
            time.sleep(args.poll_interval)

        except KeyboardInterrupt:
            logger.info("Scanner stopped by user.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            time.sleep(args.poll_interval * 2) # Wait longer after an error

if __name__ == "__main__":
    main()
