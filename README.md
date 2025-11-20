# Options ML Trading System

A **production-grade intraday options ML system** for Indian markets using the Dhan API. This system predicts whether an option will **double (2x)** from the current price within a configurable time horizon.

## 🎯 Key Features

- **Comprehensive Feature Engineering**: 50+ features including Greeks, moneyness, liquidity, spreads, and momentum indicators
- **Robust Label Generation**: Time-aware labeling with no data leakage
- **Production-Ready Models**: LightGBM/XGBoost with proper time-series validation
- **Event-Driven Backtesting**: Realistic simulation with risk management
- **Live Inference Engine**: Real-time signal generation with filters
- **Fully Typed**: Complete type hints throughout the codebase
- **Extensive Logging**: Comprehensive logging for debugging and monitoring
- **Unit Tests**: Test coverage for critical components

## 📁 Project Structure

```
options_ml/
├── config/              # Configuration management
│   ├── __init__.py
│   └── config.py        # Centralized config (paths, parameters, thresholds)
├── data/                # Data ingestion and storage
│   ├── __init__.py
│   ├── schemas.py       # Pydantic data models
│   ├── loader.py        # Load historical data
│   ├── storage.py       # Save processed data
│   └── ingest_dhan.py   # Dhan API client (mock + real)
├── features/            # Feature engineering
│   ├── __init__.py
│   └── feature_builder.py  # Build 50+ features
├── labeling/            # Target label creation
│   ├── __init__.py
│   └── label_builder.py    # 2x label generation
├── modeling/            # ML models
│   ├── __init__.py
│   ├── models.py        # Model wrapper (LightGBM/XGBoost)
│   ├── dataset.py       # Dataset preparation
│   ├── train.py         # Training pipeline
│   └── evaluate.py      # Model evaluation
├── backtest/            # Backtesting
│   ├── __init__.py
│   ├── simulator.py     # Event-driven backtest
│   └── metrics.py       # Trading performance metrics
├── live/                # Live trading
│   ├── __init__.py
│   ├── inference.py     # Live signal generation
│   └── signal_rules.py  # Signal filters
├── utils/               # Utilities
│   ├── __init__.py
│   ├── logging_utils.py
│   ├── time_utils.py
│   └── io_utils.py
├── scripts/             # Entry point scripts
│   ├── prepare_training_data.py
│   ├── train_model.py
│   ├── evaluate_model.py
│   ├── run_backtest.py
│   └── run_live_inference_example.py
└── tests/               # Unit tests
    ├── test_features.py
    ├── test_labeling.py
    └── test_modeling.py
```

## 🚀 Quick Start

### 1. Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Prepare Training Data

Place your raw JSON files (with option chain data) in `data/raw/`, then:

```bash
python options_ml/scripts/prepare_training_data.py \
    --input-dir data/raw \
    --output-file data/processed/training_data.parquet \
    --target-multiplier 2.0
```

This will:
- Load all JSON files from the input directory
- Build 50+ features for each snapshot
- Generate 2x labels with proper lookahead logic
- Save processed data to Parquet format

### 3. Train Model

```bash
python options_ml/scripts/train_model.py \
    --input-file data/processed/training_data.parquet \
    --output-dir models/run_001 \
    --model-type lightgbm
```

This will:
- Load prepared training data
- Split data by time (70% train, 15% val, 15% test)
- Train LightGBM model with early stopping
- Save model and artifacts to `models/run_001/`

### 4. Evaluate Model

```bash
python options_ml/scripts/evaluate_model.py \
    --model-dir models/run_001/model \
    --test-data data/processed/training_data.parquet \
    --output-dir results/evaluation
```

This generates:
- Threshold analysis (precision/recall at different probability cutoffs)
- Calibration curves
- Feature importance rankings
- ROC-AUC, PR-AUC, Brier score

### 5. Run Backtest

```bash
python options_ml/scripts/run_backtest.py \
    --model-dir models/run_001/model \
    --data-file data/processed/training_data.parquet \
    --output-dir results/backtest
```

This simulates trading with:
- Entry at mid price when signal triggered
- 2x take profit target
- -40% stop loss
- End-of-day auto-exit
- Realistic slippage and brokerage

### 6. Live Inference (Mock Mode)

```bash
python options_ml/scripts/run_live_inference_example.py \
    --model-dir models/run_001/model \
    --use-mock \
    --output-file results/live_signals.csv
```

For real trading:
1. Set environment variables:
   ```bash
   export DHAN_CLIENT_ID="your_client_id"
   export DHAN_ACCESS_TOKEN="your_access_token"
   ```
2. Run without `--use-mock`:
   ```bash
   python options_ml/scripts/run_live_inference_example.py \
       --model-dir models/run_001/model \
       --output-file results/live_signals.csv
   ```

## 📊 Data Format

Your raw JSON files should follow this structure:

```json
{
  "SYMBOL_STRIKE_TYPE": {
    "all_history": [
      {
        "timestamp": "2025-11-19 09:20:17",
        "spot_price": 987.55,
        "price": 4.55,
        "volume": 631400,
        "open_interest": 7184650,
        "oi_change": -13200,
        "bid_price": 4.55,
        "ask_price": 4.6,
        "bid_qty": 4400,
        "ask_qty": 2750,
        "iv": 17.13,
        "delta": 0.31588,
        "gamma": 0.01578,
        "theta": -0.70231,
        "vega": 0.468,
        "open": 0.0,
        "high": 0.0,
        "low": 0.0,
        "close": 0.0
      }
    ],
    "volume_history": [631400, ...]
  }
}
```

## ⚙️ Configuration

Create a `config.yaml` file to override defaults:

```yaml
paths:
  data_dir: "data"
  models_dir: "models"

labels:
  target_multiplier: 2.0  # 2x target
  horizon_minutes: null   # null = EOD

model:
  model_type: "lightgbm"
  n_estimators: 500
  learning_rate: 0.05
  max_depth: 7

signals:
  prob_threshold: 0.7     # Min probability for signal
  min_volume: 100000
  min_open_interest: 50000
  max_bid_ask_spread_pct: 5.0

backtest:
  stop_loss_pct: -40.0
  take_profit_multiplier: 2.0
  brokerage_per_trade: 20.0
  slippage_bps: 5.0
```

Load config in scripts:
```bash
python options_ml/scripts/train_model.py --config config.yaml
```

## 🧪 Testing

Run unit tests:

```bash
# Run all tests
pytest options_ml/tests/ -v

# Run with coverage
pytest options_ml/tests/ --cov=options_ml --cov-report=html

# Run specific test file
pytest options_ml/tests/test_features.py -v
```

## 📈 Feature Engineering

The system generates 50+ features including:

**Static Features:**
- Moneyness (absolute, log, distance to ATM)
- Option type (CE/PE encoding)
- Greeks (delta, gamma, theta, vega)
- Implied volatility

**Liquidity Features:**
- Volume, Open Interest
- Bid-ask spread (absolute and percentage)
- Order book imbalance

**Momentum Features:**
- Price returns (1, 2, 3, 5 lags)
- Greek changes
- Rolling volatility
- Volume momentum

**Cross-Sectional Features:**
- IV rank within chain
- OI rank within chain
- Volume rank within chain

**Time Features:**
- Minutes since market open
- Cyclical encoding (sin/cos)

## 🎯 Label Definition

For each snapshot at time `t`:
1. Current option price: `P(t)`
2. Target price: `P(t) * 2.0` (configurable multiplier)
3. Look ahead in the contract's future path until:
   - End of day (15:30 IST), or
   - Configured horizon (e.g., 60 minutes)
4. Label = 1 if max future price >= target price
5. Label = 0 otherwise

**Key guarantee:** No data leakage - labels only use strictly future data.

## 🔧 Dhan API Integration

Replace the mock client with actual Dhan API calls in `data/ingest_dhan.py`:

```python
from dhanhq import dhanhq

class DhanAPIClient:
    def __init__(self, client_id, access_token):
        self.client_id = client_id
        self.access_token = access_token
        self.dhan = dhanhq(client_id, access_token)

    def fetch_option_chain(self, underlying, expiry=None):
        # Implement using Dhan's option chain API
        response = self.dhan.get_option_chain(underlying, expiry)
        return self._parse_response(response)
```

## 📊 Performance Metrics

The system tracks:

**Model Metrics:**
- ROC-AUC, PR-AUC
- Precision, Recall, F1 at various thresholds
- Brier score (calibration)
- Feature importance

**Trading Metrics:**
- Win rate (% of trades hitting 2x)
- Profit factor
- Average P&L per trade
- Max drawdown
- Sharpe ratio
- Risk/reward ratio
- Exit reason breakdown

## 🚦 Signal Filters

Before generating signals, the system applies:

1. **Price filters**: Min ₹3, Max ₹500
2. **Liquidity filters**: Min volume, min OI
3. **Spread filter**: Max bid-ask spread 5%
4. **Greek filters**: Delta between 0.1 and 0.9
5. **IV filter**: IV between 5% and 100%
6. **Moneyness filter**: Not too deep OTM or ITM
7. **Time filter**: At least 30 min to market close

## 🔒 Risk Management

**Per Trade:**
- Fixed position size (configurable)
- 2x take profit target
- -40% stop loss
- Max holding period (optional)
- End-of-day auto-exit

**Portfolio:**
- Max simultaneous positions
- Max signals per sweep
- Max signals per underlying
- Daily loss limit

## 🐛 Troubleshooting

**Q: No trades in backtest?**
- Lower `prob_threshold` in config
- Check signal filters (min volume, OI, spread)
- Verify data has sufficient history

**Q: Low win rate?**
- Model may need more training data
- Try different features or model parameters
- Check label definition (2x might be too aggressive)

**Q: High positive class imbalance?**
- This is expected (2x moves are rare)
- System uses class weights and proper metrics
- Consider trying 1.5x multiplier for more positives

## 📝 License

This project is for educational and research purposes.

## ⚠️ Disclaimer

This system is provided for educational purposes only. Trading options involves substantial risk. Past performance does not guarantee future results. Always test thoroughly in paper trading before using real capital.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📧 Support

For questions or issues, please open a GitHub issue.

---

**Built with ❤️ for quantitative options trading**
