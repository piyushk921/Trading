# Options ML System - Low Positive Rate Fix Summary

## Problem Identified

Your analysis showed that **only 1 out of 275,268 records (0.0004%)** achieved the target price movement. This made the ML model unable to learn meaningful patterns.

### Root Causes

1. **Target Too Aggressive**: System was configured to find **2x (100% gain)** price movements
   - 2x moves are extremely rare in intraday options trading
   - Even with a 6+ hour lookahead window (9:15 AM to 3:30 PM), very few options double in price

2. **Horizon Too Long**: Default horizon was **end-of-day (EOD)**
   - While this seems generous, it creates stale signals
   - Options that spike early in the day won't be predicted hours in advance
   - Better to focus on near-term (30-60 min) predictions

3. **Data Sparsity**: If snapshots are collected infrequently (every 5+ minutes)
   - Price spikes between snapshots are completely missed
   - The labeling algorithm only sees prices at snapshot times

## Changes Made

### 1. Updated Target Multiplier (config.py:85)

**Before:**
```python
target_multiplier: float = 2.0  # Looking for 2x moves
```

**After:**
```python
target_multiplier: float = 1.5  # Looking for 1.5x moves (50% gain)
```

**Impact:** 1.5x moves are much more common in options trading, especially for near-the-money contracts.

### 2. Updated Horizon Window (config.py:90)

**Before:**
```python
horizon_minutes: Optional[int] = None  # None = end-of-day
```

**After:**
```python
horizon_minutes: Optional[int] = 60  # 60 minutes lookahead
```

**Impact:** Focus on near-term moves that are more predictable and actionable.

### 3. Updated Backtest Configuration (config.py:177)

**Before:**
```python
take_profit_multiplier: float = 2.0
```

**After:**
```python
take_profit_multiplier: float = 1.5
```

**Impact:** Backtest profit target now matches the training target.

### 4. Updated Signal Threshold (config.py:142)

**Before:**
```python
prob_threshold: float = 0.7
```

**After:**
```python
prob_threshold: float = 0.6
```

**Impact:** Slightly lower threshold since 1.5x is easier to achieve than 2x.

## Next Steps

### Step 1: Verify the Improvements

Run the verification script on your raw data to confirm the new configuration produces better results:

```bash
python verify_label_improvements.py data/raw/your_data_file.json
```

This will show you:
- How many positive examples you get with different configurations
- Comparison of 1.5x @ 60min vs 2.0x @ EOD
- Recommendations for your specific dataset

**Expected Results:**
- Old config (2.0x @ EOD): ~0.0004% positive rate
- New config (1.5x @ 60min): **5-15% positive rate** (if data quality is good)

If you still get <1% positive rate, it suggests data collection issues (see troubleshooting below).

### Step 2: Regenerate Training Data

Once you confirm the new config works better, regenerate your training dataset:

```bash
cd options_ml
python scripts/prepare_training_data.py \
    --input data/raw/your_data.json \
    --output data/processed/training_data_1.5x_60min.parquet
```

### Step 3: Retrain the Model

Train a new model with the improved dataset:

```bash
python scripts/train_model.py \
    --data data/processed/training_data_1.5x_60min.parquet \
    --output models/model_1.5x_60min.pkl
```

### Step 4: Evaluate Performance

Compare the new model to the old one:

```bash
python scripts/evaluate_model.py \
    --model models/model_1.5x_60min.pkl \
    --data data/processed/training_data_1.5x_60min.parquet
```

## Troubleshooting

### If Positive Rate is Still <1% After Changes

This indicates **data collection issues**, not configuration issues:

#### Issue 1: Snapshots Too Infrequent

**Problem:** If you collect data every 5-10 minutes, price spikes between snapshots are missed.

**Solution:** Collect data more frequently
```python
# In config.py, line 37
api_fetch_gap_seconds: int = 60  # Reduce from 4 to 60 seconds (or lower)
```

**Example:**
- Price at 9:15:00 = 100
- Price at 9:15:30 = 180 (spike!)
- Price at 9:20:00 = 95

If you only snapshot at 9:15:00 and 9:20:00, you miss the 180 spike entirely.

#### Issue 2: Wrong Price Field

**Problem:** Using 'close' instead of 'price', or 'price' is zero/stale.

**Solution:** Verify in your data that the 'price' field has valid, real-time values:
```python
import json
with open('data/raw/your_data.json') as f:
    data = json.load(f)

# Check a sample contract
sample = data['HDFCBANK_1000.0_CE']['all_history'][0]
print(f"Price: {sample['price']}")  # Should be non-zero
print(f"Timestamp: {sample['timestamp']}")  # Should have sub-minute precision
```

#### Issue 3: Filtering Out Volatile Options

**Problem:** Pre-filtering removed the most volatile (and profitable) options.

**Solution:** Temporarily remove moneyness filters to see all options:
```python
# In prepare_training_data.py, comment out moneyness filtering
# Or set very wide filters:
config.data.min_price = 1.0   # Allow cheaper options
config.data.max_price = 5000.0  # Allow expensive options
```

### If You Want Even More Positive Examples

Try these alternative configurations:

1. **1.3x target @ 60 min** - Easier target, more samples
   ```python
   target_multiplier: float = 1.3
   horizon_minutes: Optional[int] = 60
   ```

2. **1.5x target @ 120 min** - Longer window for 1.5x moves
   ```python
   target_multiplier: float = 1.5
   horizon_minutes: Optional[int] = 120
   ```

3. **Multi-target approach** - Train separate models for different targets
   ```python
   # Use alternative_horizons to train multiple models
   alternative_horizons: List[int] = [30, 60, 120]
   ```

## Expected Positive Rates

Based on typical options data:

| Target | Horizon | Expected Positive Rate | Notes |
|--------|---------|------------------------|-------|
| 2.0x   | EOD     | 0.1% - 1%              | Very rare, hard to train |
| 1.5x   | EOD     | 2% - 5%                | More realistic |
| 1.5x   | 120 min | 5% - 10%               | Good balance |
| 1.5x   | 60 min  | 8% - 15%               | Recommended ✓ |
| 1.3x   | 60 min  | 15% - 25%              | High sample count |
| 1.3x   | 30 min  | 20% - 30%              | Very short-term |

## Data Collection Best Practices

To maximize the quality of your training data:

1. **Collect Every 30-60 Seconds During Market Hours**
   - Captures intraday volatility spikes
   - Don't miss rapid price movements

2. **Focus on Near-the-Money Options**
   - ATM ± 5 strikes have the most volatility
   - Deep ITM/OTM options move slowly

3. **Store All Fields**
   - Greeks (delta, gamma, theta, vega, IV)
   - Order book (bid/ask, volumes)
   - Open interest changes
   - Spot price (underlying stock price)

4. **Validate Data Quality**
   - Check for zeros in price field
   - Verify timestamps are sequential
   - Ensure no gaps >5 minutes (except market close)

## Configuration Files

All changes were made to:
- **options_ml/config/config.py** - Main configuration

Files created:
- **verify_label_improvements.py** - Script to test different configurations

## Contact & Support

If you're still seeing low positive rates after following these steps, check:

1. Run `verify_label_improvements.py` to see actual rates
2. Inspect raw data timestamps (should be <2 min apart)
3. Verify 'price' field has non-zero values
4. Check if dataset includes high-volatility periods (market opens, news events)

## Summary

✓ Changed target from 2.0x to 1.5x (more realistic)
✓ Changed horizon from EOD to 60 minutes (near-term focus)
✓ Updated backtest and signal configs to match
✓ Created verification script to test configurations

**Expected improvement:** From 0.0004% to 8-15% positive rate (assuming good data quality)

If positive rate is still <1%, the issue is data collection frequency, not configuration.
