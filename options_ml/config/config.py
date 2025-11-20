"""
Configuration management for options ML system.

Centralizes all parameters including paths, model settings, trading filters,
and feature engineering options.
"""

import os
import yaml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List


@dataclass
class PathConfig:
    """File and directory paths."""

    # Base directories
    data_dir: str = "data"
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    models_dir: str = "models"
    results_dir: str = "results"
    logs_dir: str = "logs"

    # Specific files
    training_data_file: str = "data/processed/training_data.parquet"
    feature_names_file: str = "models/feature_names.json"


@dataclass
class DataConfig:
    """Data collection and processing parameters."""

    # API constraints
    api_fetch_gap_seconds: int = 4  # Dhan API rate limit

    # Data filtering
    min_snapshots_per_contract: int = 3  # Minimum history for training
    max_price: float = 1000.0  # Filter out very expensive options
    min_price: float = 2.0  # Filter out very cheap options

    # Time parameters
    market_open_time: str = "09:15:00"
    market_close_time: str = "15:30:00"

    # Symbols (can be loaded from file)
    underlying_symbols: List[str] = field(default_factory=lambda: [
        "NIFTY", "BANKNIFTY", "HDFCBANK", "RELIANCE", "TCS",
        "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC"
    ])


@dataclass
class FeatureConfig:
    """Feature engineering parameters."""

    # Lookback windows (in number of snapshots)
    lookback_windows: List[int] = field(default_factory=lambda: [1, 2, 3, 5])

    # Time-based lookback (in minutes)
    time_lookback_minutes: List[int] = field(default_factory=lambda: [10, 30, 60])

    # Rolling statistics
    compute_rolling_stats: bool = True
    rolling_window_sizes: List[int] = field(default_factory=lambda: [3, 5])

    # Cross-sectional features
    compute_cross_sectional: bool = True

    # Moneyness bins for classification
    moneyness_bins: List[float] = field(default_factory=lambda: [
        -0.10, -0.05, -0.02, 0.02, 0.05, 0.10
    ])


@dataclass
class LabelConfig:
    """Labeling parameters for target variable."""

    # Target multiplier (2.0 means 2x, 1.5 means 1.5x)
    target_multiplier: float = 2.0

    # Lookahead horizon in minutes (None = end of day)
    horizon_minutes: Optional[int] = None

    # Alternative horizons for multi-model training
    alternative_horizons: List[int] = field(default_factory=lambda: [30, 60, 120, 240])

    # Whether to compute time-to-target
    compute_time_to_target: bool = True

    # Whether to compute max future return
    compute_max_return: bool = True


@dataclass
class ModelConfig:
    """ML model parameters."""

    # Model type
    model_type: str = "lightgbm"  # or "xgboost"

    # LightGBM/XGBoost hyperparameters
    n_estimators: int = 500
    learning_rate: float = 0.05
    max_depth: int = 7
    num_leaves: int = 31
    min_child_samples: int = 20
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    reg_alpha: float = 0.1
    reg_lambda: float = 0.1

    # Class imbalance handling
    scale_pos_weight: Optional[float] = None  # Auto-calculated if None
    class_weight: Optional[str] = "balanced"  # or None

    # Training parameters
    early_stopping_rounds: int = 50
    verbose: int = 100
    random_state: int = 42
    n_jobs: int = -1

    # Validation strategy
    validation_method: str = "time_series_split"  # or "walk_forward"
    n_splits: int = 5
    test_size: float = 0.2


@dataclass
class SignalConfig:
    """Signal generation and filtering parameters."""

    # Probability threshold for signal
    prob_threshold: float = 0.7

    # Alternative thresholds for evaluation
    evaluation_thresholds: List[float] = field(default_factory=lambda: [
        0.5, 0.6, 0.7, 0.8, 0.9
    ])

    # Liquidity filters
    min_volume: int = 100000
    min_open_interest: int = 50000

    # Spread filter
    max_bid_ask_spread_pct: float = 5.0  # percentage

    # Price filters
    min_signal_price: float = 3.0
    max_signal_price: float = 500.0

    # Time filters
    min_minutes_to_close: int = 30  # Don't enter after 3:00 PM

    # Position sizing
    max_signals_per_sweep: int = 5
    max_signals_per_underlying: int = 2


@dataclass
class BacktestConfig:
    """Backtesting parameters."""

    # Entry/exit
    entry_method: str = "mid"  # "mid", "ask", "last"
    exit_method: str = "mid"

    # Risk management
    stop_loss_pct: float = -40.0  # Negative percentage
    take_profit_multiplier: float = 2.0  # Same as target

    # Holding period
    max_holding_minutes: Optional[int] = None  # None = until EOD

    # Costs
    brokerage_per_trade: float = 20.0  # Flat fee
    slippage_bps: float = 5.0  # Basis points

    # Portfolio
    initial_capital: float = 100000.0
    position_size_fixed: float = 10000.0  # Fixed amount per trade
    max_positions: int = 10


@dataclass
class LiveConfig:
    """Live trading parameters."""

    # Dhan API credentials (loaded from environment)
    dhan_client_id: str = field(default_factory=lambda: os.getenv("DHAN_CLIENT_ID", ""))
    dhan_access_token: str = field(default_factory=lambda: os.getenv("DHAN_ACCESS_TOKEN", ""))

    # Refresh intervals
    data_refresh_seconds: int = 60  # How often to fetch new data
    signal_check_seconds: int = 120  # How often to check for signals

    # Safety limits
    max_trades_per_day: int = 20
    max_loss_per_day: float = -5000.0

    # Signal output
    save_signals_to_file: bool = True
    signals_file: str = "results/live_signals.csv"


@dataclass
class Config:
    """Master configuration object."""

    paths: PathConfig = field(default_factory=PathConfig)
    data: DataConfig = field(default_factory=DataConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    labels: LabelConfig = field(default_factory=LabelConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    signals: SignalConfig = field(default_factory=SignalConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    live: LiveConfig = field(default_factory=LiveConfig)

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return asdict(self)

    def save(self, path: str) -> None:
        """Save configuration to YAML file."""
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)

    @classmethod
    def from_dict(cls, config_dict: dict) -> "Config":
        """Load configuration from dictionary."""
        return cls(
            paths=PathConfig(**config_dict.get("paths", {})),
            data=DataConfig(**config_dict.get("data", {})),
            features=FeatureConfig(**config_dict.get("features", {})),
            labels=LabelConfig(**config_dict.get("labels", {})),
            model=ModelConfig(**config_dict.get("model", {})),
            signals=SignalConfig(**config_dict.get("signals", {})),
            backtest=BacktestConfig(**config_dict.get("backtest", {})),
            live=LiveConfig(**config_dict.get("live", {}))
        )

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from YAML file."""
        with open(path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)

    def ensure_directories(self) -> None:
        """Create all necessary directories."""
        dirs = [
            self.paths.data_dir,
            self.paths.raw_data_dir,
            self.paths.processed_data_dir,
            self.paths.models_dir,
            self.paths.results_dir,
            self.paths.logs_dir,
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


# Global config instance
_global_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def load_config(path: str) -> Config:
    """
    Load configuration from file and set as global config.

    Args:
        path: Path to YAML config file

    Returns:
        Config instance
    """
    global _global_config
    _global_config = Config.from_yaml(path)
    return _global_config


def set_config(config: Config) -> None:
    """
    Set the global configuration instance.

    Args:
        config: Config instance to set as global
    """
    global _global_config
    _global_config = config


# Create a default config file if needed
def create_default_config(output_path: str = "config.yaml") -> None:
    """
    Create a default configuration file.

    Args:
        output_path: Where to save the config file
    """
    config = Config()
    config.save(output_path)
    print(f"Default configuration saved to {output_path}")


if __name__ == "__main__":
    # Generate default config for reference
    create_default_config("config_default.yaml")
