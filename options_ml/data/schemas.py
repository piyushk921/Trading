"""
Data schemas for options trading system.

This module defines Pydantic models for type-safe data validation and serialization
of option snapshots and contracts.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class OptionSnapshot(BaseModel):
    """
    A single snapshot of an option contract at a specific point in time.

    Attributes:
        timestamp: ISO format timestamp or datetime string
        spot_price: Underlying asset price
        price: Option premium price
        volume: Trading volume
        open_interest: Open interest
        oi_change: Change in open interest
        bid_price: Best bid price
        ask_price: Best ask price
        bid_qty: Bid quantity
        ask_qty: Ask quantity
        iv: Implied volatility (percentage)
        delta: Delta Greek
        gamma: Gamma Greek
        theta: Theta Greek
        vega: Vega Greek
        open: Open price (often zero from API)
        high: High price (often zero from API)
        low: Low price (often zero from API)
        close: Close price (often zero from API)
    """

    timestamp: str
    spot_price: Optional[float] = None  # Made optional - some data sources don't include it
    price: float
    volume: int
    open_interest: int
    oi_change: int
    bid_price: float
    ask_price: float
    bid_qty: int
    ask_qty: int
    iv: float
    delta: float
    gamma: float
    theta: float
    vega: float
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate and normalize timestamp format."""
        # Try to parse to ensure it's valid
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                # Try ISO format
                datetime.fromisoformat(v)
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {v}")
        return v

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump()

    @property
    def mid_price(self) -> float:
        """Calculate mid price from bid-ask."""
        return (self.bid_price + self.ask_price) / 2.0

    @property
    def bid_ask_spread(self) -> float:
        """Calculate absolute bid-ask spread."""
        return self.ask_price - self.bid_price

    @property
    def bid_ask_spread_pct(self) -> float:
        """Calculate bid-ask spread as percentage of mid price."""
        mid = self.mid_price
        if mid <= 0:
            return 0.0
        return (self.bid_ask_spread / mid) * 100.0

    @property
    def order_book_imbalance(self) -> float:
        """
        Calculate order book imbalance.

        Returns:
            Value between -1 (all ask) and 1 (all bid)
        """
        total = self.bid_qty + self.ask_qty
        if total == 0:
            return 0.0
        return (self.bid_qty - self.ask_qty) / total


class OptionContract(BaseModel):
    """
    Represents a complete option contract with historical snapshots.

    Attributes:
        symbol: Full option symbol (e.g., "HDFCBANK_1000.0_CE")
        underlying: Underlying asset symbol
        strike: Strike price
        option_type: "CE" for call, "PE" for put
        expiry: Expiry date (YYYY-MM-DD format)
        all_history: List of all snapshots for this contract
        volume_history: Quick access to volume history
    """

    symbol: str
    underlying: str
    strike: float
    option_type: Literal["CE", "PE"]
    expiry: Optional[str] = None
    all_history: list[OptionSnapshot] = Field(default_factory=list)
    volume_history: list[int] = Field(default_factory=list)

    @classmethod
    def from_symbol(cls, symbol: str, history_data: dict) -> "OptionContract":
        """
        Parse contract from symbol and raw history data.

        Args:
            symbol: Option symbol like "HDFCBANK_1000.0_CE"
            history_data: Dict with 'all_history' and 'volume_history'

        Returns:
            OptionContract instance
        """
        # Parse symbol: UNDERLYING_STRIKE_TYPE
        parts = symbol.rsplit("_", 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid symbol format: {symbol}")

        underlying = parts[0]
        strike = float(parts[1])
        option_type = parts[2]

        if option_type not in ["CE", "PE"]:
            raise ValueError(f"Invalid option type: {option_type}")

        # Parse snapshots
        snapshots = [
            OptionSnapshot(**snap_data)
            for snap_data in history_data.get("all_history", [])
        ]

        return cls(
            symbol=symbol,
            underlying=underlying,
            strike=strike,
            option_type=option_type,
            all_history=snapshots,
            volume_history=history_data.get("volume_history", [])
        )

    def get_snapshot_at(self, index: int) -> Optional[OptionSnapshot]:
        """Get snapshot at specific index."""
        if 0 <= index < len(self.all_history):
            return self.all_history[index]
        return None

    @property
    def latest_snapshot(self) -> Optional[OptionSnapshot]:
        """Get the most recent snapshot."""
        if self.all_history:
            return self.all_history[-1]
        return None


class OptionChainData(BaseModel):
    """
    Complete option chain data for multiple contracts.

    Attributes:
        date: Trading date
        contracts: Dictionary mapping symbol to OptionContract
    """

    date: Optional[str] = None
    contracts: dict[str, OptionContract] = Field(default_factory=dict)

    @classmethod
    def from_raw_json(cls, raw_data: dict, date: Optional[str] = None) -> "OptionChainData":
        """
        Parse raw JSON data from Dhan API format.

        Args:
            raw_data: Dictionary with symbol keys and history data
            date: Optional trading date

        Returns:
            OptionChainData instance
        """
        contracts = {}
        for symbol, history_data in raw_data.items():
            try:
                contract = OptionContract.from_symbol(symbol, history_data)
                contracts[symbol] = contract
            except Exception as e:
                # Log and skip invalid contracts
                print(f"Warning: Failed to parse contract {symbol}: {e}")
                continue

        return cls(date=date, contracts=contracts)

    def get_contract(self, symbol: str) -> Optional[OptionContract]:
        """Get contract by symbol."""
        return self.contracts.get(symbol)

    def filter_by_underlying(self, underlying: str) -> dict[str, OptionContract]:
        """Get all contracts for a specific underlying."""
        return {
            symbol: contract
            for symbol, contract in self.contracts.items()
            if contract.underlying == underlying
        }

    @property
    def total_contracts(self) -> int:
        """Total number of contracts."""
        return len(self.contracts)

    @property
    def unique_underlyings(self) -> set[str]:
        """Get set of unique underlying symbols."""
        return {contract.underlying for contract in self.contracts.values()}


class TrainingFeatureRow(BaseModel):
    """
    A single row of training data with features and label.

    This represents the flattened feature vector for ML training.
    """

    # Identifiers
    symbol: str
    timestamp: str
    underlying: str
    strike: float
    option_type: str

    # Target variable
    label_2x: int  # 0 or 1
    time_to_2x_minutes: Optional[float] = None  # Time until 2x achieved, or None
    max_future_return: Optional[float] = None  # Max return achieved in horizon

    # Features will be added dynamically
    # This is just a base schema

    class Config:
        extra = "allow"  # Allow additional fields for features
