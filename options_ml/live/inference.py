"""
Live inference engine for real-time signal generation.

Fetches live data, generates features, and produces trading signals.
"""

import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from ..modeling.models import Option2xModel
from ..modeling.dataset import prepare_dataset
from ..features.feature_builder import FeatureBuilder
from ..data.ingest_dhan import DhanAPIClient
from ..data.schemas import OptionChainData
from ..config import Config, get_config
from ..utils.time_utils import get_ist_now, is_market_hours, minutes_to_market_close
from ..utils.logging_utils import get_logger
from .signal_rules import apply_signal_filters

logger = get_logger(__name__)


@dataclass
class TradingSignal:
    """Represents a trading signal."""

    timestamp: str
    symbol: str
    underlying: str
    strike: float
    option_type: str
    entry_price: float
    predicted_probability: float
    target_price: float
    stop_loss_price: float

    # Additional context
    spot_price: float
    volume: int
    open_interest: int
    iv: float
    delta: float

    # Signal metadata
    signal_strength: str = "medium"  # low, medium, high
    filters_passed: List[str] = None

    def __post_init__(self):
        """Initialize derived fields."""
        if self.filters_passed is None:
            self.filters_passed = []

        # Calculate targets if not provided
        if self.target_price == 0:
            self.target_price = self.entry_price * 2.0
        if self.stop_loss_price == 0:
            self.stop_loss_price = self.entry_price * 0.6

        # Determine signal strength
        if self.predicted_probability >= 0.8:
            self.signal_strength = "high"
        elif self.predicted_probability >= 0.7:
            self.signal_strength = "medium"
        else:
            self.signal_strength = "low"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class LiveInferenceEngine:
    """
    Live inference engine for real-time trading signals.

    Manages data fetching, feature engineering, and signal generation.
    """

    def __init__(
        self,
        model: Option2xModel,
        dhan_client: DhanAPIClient,
        config: Optional[Config] = None
    ):
        """
        Initialize live inference engine.

        Args:
            model: Trained model
            dhan_client: Dhan API client for data fetching
            config: Configuration object
        """
        self.model = model
        self.dhan_client = dhan_client
        self.config = config or get_config()
        self.feature_builder = FeatureBuilder(config)

        # Historical data buffer for feature calculation
        self.data_buffer: Dict[str, pd.DataFrame] = {}

        # Today's signals and trades
        self.signals_generated: List[TradingSignal] = []
        self.trades_executed: List[str] = []

        logger.info("Live inference engine initialized")

    def check_market_status(self) -> bool:
        """
        Check if market is open and ready for trading.

        Returns:
            True if market is open and we can trade
        """
        if not is_market_hours():
            logger.info("Market is currently closed")
            return False

        # Check time to close
        minutes_left = minutes_to_market_close()
        min_minutes = self.config.signals.min_minutes_to_close

        if minutes_left < min_minutes:
            logger.info(f"Too close to market close ({minutes_left:.0f} minutes left)")
            return False

        return True

    def fetch_latest_data(
        self,
        underlyings: Optional[List[str]] = None
    ) -> OptionChainData:
        """
        Fetch latest option chain data from Dhan API.

        Args:
            underlyings: List of underlying symbols (uses config if None)

        Returns:
            OptionChainData with latest snapshots
        """
        if underlyings is None:
            underlyings = self.config.data.underlying_symbols

        logger.info(f"Fetching option chain data for {len(underlyings)} underlyings")

        all_chain_data = {}

        for underlying in underlyings:
            try:
                chain_data = self.dhan_client.fetch_option_chain(underlying)
                all_chain_data.update(chain_data)
            except Exception as e:
                logger.error(f"Failed to fetch data for {underlying}: {e}")
                continue

        option_chain = OptionChainData.from_raw_json(all_chain_data)
        logger.info(f"Fetched data for {option_chain.total_contracts} contracts")

        return option_chain

    def update_data_buffer(self, option_chain: OptionChainData) -> None:
        """
        Update historical data buffer with new snapshots.

        Args:
            option_chain: Latest option chain data
        """
        for symbol, contract in option_chain.contracts.items():
            if contract.latest_snapshot is None:
                continue

            snapshot_dict = {
                'symbol': symbol,
                'underlying': contract.underlying,
                'strike': contract.strike,
                'option_type': contract.option_type,
                **contract.latest_snapshot.to_dict()
            }

            # Add to buffer
            if symbol not in self.data_buffer:
                self.data_buffer[symbol] = pd.DataFrame([snapshot_dict])
            else:
                new_row = pd.DataFrame([snapshot_dict])
                self.data_buffer[symbol] = pd.concat(
                    [self.data_buffer[symbol], new_row],
                    ignore_index=True
                )

                # Keep only recent history (e.g., last 50 snapshots)
                if len(self.data_buffer[symbol]) > 50:
                    self.data_buffer[symbol] = self.data_buffer[symbol].iloc[-50:]

        logger.debug(f"Updated data buffer for {len(option_chain.contracts)} contracts")

    def generate_signals(
        self,
        option_chain: Optional[OptionChainData] = None,
        apply_filters: bool = True
    ) -> List[TradingSignal]:
        """
        Generate trading signals from current market data.

        Args:
            option_chain: Option chain data (fetches if None)
            apply_filters: Whether to apply signal filters

        Returns:
            List of trading signals
        """
        logger.info("=" * 80)
        logger.info("Generating trading signals")
        logger.info("=" * 80)

        # Check market status
        if not self.check_market_status():
            logger.warning("Market not ready for trading")
            return []

        # Fetch data if not provided
        if option_chain is None:
            option_chain = self.fetch_latest_data()

        # Update buffer
        self.update_data_buffer(option_chain)

        # Build features for all contracts
        signals = []

        for symbol, contract in option_chain.contracts.items():
            try:
                signal = self._generate_signal_for_contract(symbol, contract, apply_filters)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Failed to generate signal for {symbol}: {e}")
                continue

        # Sort by probability (descending)
        signals.sort(key=lambda s: s.predicted_probability, reverse=True)

        # Limit number of signals
        max_signals = self.config.signals.max_signals_per_sweep
        if len(signals) > max_signals:
            logger.info(f"Limiting signals from {len(signals)} to {max_signals}")
            signals = signals[:max_signals]

        logger.info(f"Generated {len(signals)} trading signals")

        # Log top signals
        if signals:
            logger.info("\nTop Trading Signals:")
            for i, sig in enumerate(signals[:5], 1):
                logger.info(
                    f"{i}. {sig.symbol} - Prob: {sig.predicted_probability:.3f}, "
                    f"Price: {sig.entry_price:.2f}, Target: {sig.target_price:.2f}"
                )

        self.signals_generated.extend(signals)
        return signals

    def _generate_signal_for_contract(
        self,
        symbol: str,
        contract,
        apply_filters: bool
    ) -> Optional[TradingSignal]:
        """Generate signal for a single contract."""
        # Need sufficient history for features
        if symbol not in self.data_buffer:
            return None

        contract_df = self.data_buffer[symbol].copy()

        if len(contract_df) < 3:  # Minimum history
            return None

        # Build features
        features_df = self.feature_builder.build_features(contract_df)

        # Get latest row
        latest_row = features_df.iloc[-1]

        # Prepare features for prediction
        X, _, _ = prepare_dataset(
            features_df.iloc[[-1]],  # Only latest row
            self.config
        )

        # Get prediction
        proba = self.model.predict_proba(X)[0, 1]

        # Check probability threshold
        if proba < self.config.signals.prob_threshold:
            return None

        # Apply filters if requested
        if apply_filters:
            passed, reasons = apply_signal_filters(latest_row, self.config)
            if not passed:
                logger.debug(f"Signal filtered out for {symbol}: {reasons}")
                return None
        else:
            reasons = []

        # Create signal
        latest_snapshot = contract.latest_snapshot
        signal = TradingSignal(
            timestamp=get_ist_now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol=symbol,
            underlying=contract.underlying,
            strike=contract.strike,
            option_type=contract.option_type,
            entry_price=latest_snapshot.mid_price,
            predicted_probability=proba,
            target_price=latest_snapshot.mid_price * 2.0,
            stop_loss_price=latest_snapshot.mid_price * 0.6,
            spot_price=latest_snapshot.spot_price,
            volume=latest_snapshot.volume,
            open_interest=latest_snapshot.open_interest,
            iv=latest_snapshot.iv,
            delta=latest_snapshot.delta,
            filters_passed=reasons,
        )

        return signal

    def save_signals(self, signals: List[TradingSignal], filepath: str) -> None:
        """
        Save signals to file.

        Args:
            signals: List of signals
            filepath: Output file path
        """
        if not signals:
            logger.info("No signals to save")
            return

        signals_df = pd.DataFrame([sig.to_dict() for sig in signals])
        signals_df.to_csv(filepath, index=False)
        logger.info(f"Saved {len(signals)} signals to {filepath}")


def execute_signals_with_dhan(signals: List[TradingSignal]) -> None:
    """
    Execute signals by placing orders via Dhan API.

    Args:
        signals: List of trading signals

    Note:
        This is a placeholder. Implement actual order placement logic here.
    """
    logger.info("=" * 80)
    logger.info(f"Executing {len(signals)} signals")
    logger.info("=" * 80)

    for signal in signals:
        logger.info(f"Signal: {signal.symbol}")
        logger.info(f"  Entry: {signal.entry_price:.2f}")
        logger.info(f"  Target: {signal.target_price:.2f}")
        logger.info(f"  Stop Loss: {signal.stop_loss_price:.2f}")
        logger.info(f"  Probability: {signal.predicted_probability:.3f}")

        # TODO: Implement actual order placement
        # Example:
        # order = dhan_client.place_order(
        #     symbol=signal.symbol,
        #     quantity=calculate_quantity(signal.entry_price),
        #     order_type="LIMIT",
        #     price=signal.entry_price
        # )
        # logger.info(f"Order placed: {order['order_id']}")

    logger.info("Signal execution complete (placeholder)")
