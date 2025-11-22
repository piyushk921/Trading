"""
Signal filtering rules for live trading.

Implements filters to reduce bad trades and manage risk.
"""

import pandas as pd
from typing import Tuple, List, Optional

from ..config import Config, get_config
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


class SignalFilter:
    """
    Signal filtering rules.

    Applies various filters to ensure signal quality.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize signal filter.

        Args:
            config: Configuration object
        """
        self.config = config or get_config()
        self.signal_config = self.config.signals

    def check_price_range(self, price: float) -> Tuple[bool, str]:
        """Check if price is within acceptable range."""
        if price < self.signal_config.min_signal_price:
            return False, f"Price {price:.2f} below minimum {self.signal_config.min_signal_price}"

        if price > self.signal_config.max_signal_price:
            return False, f"Price {price:.2f} above maximum {self.signal_config.max_signal_price}"

        return True, "price_range_ok"

    def check_volume(self, volume: int) -> Tuple[bool, str]:
        """Check if volume meets minimum requirement."""
        if volume < self.signal_config.min_volume:
            return False, f"Volume {volume} below minimum {self.signal_config.min_volume}"

        return True, "volume_ok"

    def check_open_interest(self, oi: int) -> Tuple[bool, str]:
        """Check if open interest meets minimum requirement."""
        if oi < self.signal_config.min_open_interest:
            return False, f"OI {oi} below minimum {self.signal_config.min_open_interest}"

        return True, "oi_ok"

    def check_spread(self, spread_pct: float) -> Tuple[bool, str]:
        """Check if bid-ask spread is acceptable."""
        if spread_pct > self.signal_config.max_bid_ask_spread_pct:
            return False, f"Spread {spread_pct:.2f}% above maximum {self.signal_config.max_bid_ask_spread_pct}%"

        return True, "spread_ok"

    def check_liquidity(
        self,
        volume: int,
        oi: int,
        bid_qty: int,
        ask_qty: int
    ) -> Tuple[bool, str]:
        """
        Comprehensive liquidity check.

        Args:
            volume: Trading volume
            oi: Open interest
            bid_qty: Bid quantity
            ask_qty: Ask quantity

        Returns:
            Tuple of (passed, reason)
        """
        # Volume check
        passed, reason = self.check_volume(volume)
        if not passed:
            return False, reason

        # OI check
        passed, reason = self.check_open_interest(oi)
        if not passed:
            return False, reason

        # Check bid/ask quantities (ensure there's liquidity on both sides)
        min_qty = 100  # Minimum quantity on each side
        if bid_qty < min_qty or ask_qty < min_qty:
            return False, f"Insufficient bid/ask qty: bid={bid_qty}, ask={ask_qty}"

        return True, "liquidity_ok"

    def check_greeks(
        self,
        delta: float,
        gamma: float,
        theta: float,
        vega: float
    ) -> Tuple[bool, str]:
        """
        Check if Greeks are within reasonable ranges.

        Args:
            delta: Delta
            gamma: Gamma
            theta: Theta
            vega: Vega

        Returns:
            Tuple of (passed, reason)
        """
        # Avoid extreme deltas (too far OTM or ITM)
        if abs(delta) < 0.1:
            return False, f"Delta {delta:.3f} too low (too far OTM)"

        if abs(delta) > 0.9:
            return False, f"Delta {delta:.3f} too high (too deep ITM)"

        # Check for reasonable gamma (not too low)
        if gamma < 0.001:
            return False, f"Gamma {gamma:.4f} too low"

        return True, "greeks_ok"

    def check_iv(self, iv: float) -> Tuple[bool, str]:
        """
        Check if IV is within reasonable range.

        Args:
            iv: Implied volatility (percentage)

        Returns:
            Tuple of (passed, reason)
        """
        # Avoid extremely low or high IV
        if iv < 5.0:
            return False, f"IV {iv:.2f}% too low"

        if iv > 100.0:
            return False, f"IV {iv:.2f}% too high"

        return True, "iv_ok"

    def check_moneyness(
        self,
        spot_price: float,
        strike: float,
        option_type: str
    ) -> Tuple[bool, str]:
        """
        Check if option moneyness is acceptable.

        Args:
            spot_price: Underlying price
            strike: Strike price
            option_type: "CE" or "PE"

        Returns:
            Tuple of (passed, reason)
        """
        moneyness_pct = (spot_price - strike) / strike * 100

        # For calls: avoid deep OTM (strike much higher than spot)
        if option_type == "CE":
            if moneyness_pct < -20:  # Strike > 20% above spot
                return False, f"Call too far OTM: moneyness {moneyness_pct:.1f}%"
            if moneyness_pct > 10:  # Strike > 10% below spot
                return False, f"Call too deep ITM: moneyness {moneyness_pct:.1f}%"

        # For puts: avoid deep OTM (strike much lower than spot)
        elif option_type == "PE":
            if moneyness_pct > 20:  # Strike > 20% below spot
                return False, f"Put too far OTM: moneyness {moneyness_pct:.1f}%"
            if moneyness_pct < -10:  # Strike > 10% above spot
                return False, f"Put too deep ITM: moneyness {moneyness_pct:.1f}%"

        return True, "moneyness_ok"


def apply_signal_filters(
    row: pd.Series,
    config: Optional[Config] = None
) -> Tuple[bool, List[str]]:
    """
    Apply all signal filters to a data row.

    Args:
        row: Data row with option snapshot
        config: Configuration object

    Returns:
        Tuple of (passed_all_filters, list_of_passed_filter_names)
    """
    filter_obj = SignalFilter(config)
    passed_filters = []
    failed_reason = None

    # 1. Price range
    passed, reason = filter_obj.check_price_range(row['price'])
    if not passed:
        return False, [reason]
    passed_filters.append(reason)

    # 2. Liquidity (volume + OI)
    passed, reason = filter_obj.check_liquidity(
        row['volume'],
        row['open_interest'],
        row.get('bid_qty', 0),
        row.get('ask_qty', 0)
    )
    if not passed:
        return False, [reason]
    passed_filters.append(reason)

    # 3. Spread
    if 'bid_ask_spread_pct' in row:
        passed, reason = filter_obj.check_spread(row['bid_ask_spread_pct'])
        if not passed:
            return False, [reason]
        passed_filters.append(reason)

    # 4. Greeks
    passed, reason = filter_obj.check_greeks(
        row['delta'],
        row['gamma'],
        row['theta'],
        row['vega']
    )
    if not passed:
        return False, [reason]
    passed_filters.append(reason)

    # 5. IV
    passed, reason = filter_obj.check_iv(row['iv'])
    if not passed:
        return False, [reason]
    passed_filters.append(reason)

    # 6. Moneyness
    passed, reason = filter_obj.check_moneyness(
        row['spot_price'],
        row['strike'],
        row['option_type']
    )
    if not passed:
        return False, [reason]
    passed_filters.append(reason)

    return True, passed_filters


def filter_signals_by_underlying(
    signals: List,
    max_per_underlying: int = 2
) -> List:
    """
    Limit number of signals per underlying.

    Args:
        signals: List of TradingSignal objects
        max_per_underlying: Maximum signals per underlying

    Returns:
        Filtered list of signals
    """
    underlying_counts = {}
    filtered_signals = []

    for signal in signals:
        underlying = signal.underlying
        count = underlying_counts.get(underlying, 0)

        if count < max_per_underlying:
            filtered_signals.append(signal)
            underlying_counts[underlying] = count + 1

    return filtered_signals


def rank_signals(
    signals: List,
    method: str = "probability"
) -> List:
    """
    Rank and sort signals.

    Args:
        signals: List of TradingSignal objects
        method: Ranking method ("probability", "volume", "oi")

    Returns:
        Sorted list of signals
    """
    if method == "probability":
        return sorted(signals, key=lambda s: s.predicted_probability, reverse=True)
    elif method == "volume":
        return sorted(signals, key=lambda s: s.volume, reverse=True)
    elif method == "oi":
        return sorted(signals, key=lambda s: s.open_interest, reverse=True)
    else:
        return signals
