#!/usr/bin/env python3
"""
Verification script to test the new labeling configuration.

This script will:
1. Load your raw data
2. Test multiple target multipliers (1.3x, 1.5x, 2.0x)
3. Test multiple horizon windows (30, 60, 120 minutes, EOD)
4. Show how many positive examples you get with each configuration

Run this to verify that the new config (1.5x @ 60 min) produces better results.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys


def load_json_data(json_file):
    """Load raw options data from JSON file."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data


def flatten_to_dataframe(raw_data):
    """Convert contract->timeseries structure to flat DataFrame."""
    all_records = []

    for contract_name, contract_data in raw_data.items():
        if not isinstance(contract_data, dict):
            continue

        all_history = contract_data.get('all_history', [])

        for snapshot in all_history:
            record = snapshot.copy()
            record['contract'] = contract_name
            all_records.append(record)

    df = pd.DataFrame(all_records)

    # Convert timestamp to datetime
    if 'timestamp' in df.columns:
        df['dt'] = pd.to_datetime(df['timestamp'])

    return df


def count_positive_examples(df, target_multiplier, horizon_minutes):
    """
    Count how many snapshots achieve the target multiplier within the horizon.

    Args:
        df: DataFrame with columns ['contract', 'dt', 'price']
        target_multiplier: e.g., 1.5 for 1.5x, 2.0 for 2x
        horizon_minutes: int or None (None = end of day)

    Returns:
        dict with statistics
    """
    contracts = df['contract'].unique()
    total_snapshots = 0
    positive_snapshots = 0

    for contract in contracts:
        contract_df = df[df['contract'] == contract].sort_values('dt').reset_index(drop=True)

        if len(contract_df) < 2:
            continue

        # Get end of day time
        first_dt = contract_df.iloc[0]['dt']
        eod_time = first_dt.replace(hour=15, minute=30, second=0)

        for i in range(len(contract_df) - 1):
            current_row = contract_df.iloc[i]
            current_price = current_row['price']
            current_time = current_row['dt']

            # Skip zero prices
            if current_price <= 0:
                continue

            total_snapshots += 1

            # Calculate target price
            target_price = current_price * target_multiplier

            # Determine horizon
            if horizon_minutes is not None:
                horizon_end = current_time + timedelta(minutes=horizon_minutes)
            else:
                horizon_end = eod_time

            # Cap at EOD
            horizon_end = min(horizon_end, eod_time)

            # Check future snapshots within horizon
            achieved = False
            for j in range(i + 1, len(contract_df)):
                future_row = contract_df.iloc[j]
                future_price = future_row['price']
                future_time = future_row['dt']

                # Stop if beyond horizon
                if future_time > horizon_end:
                    break

                # Check if target achieved
                if future_price >= target_price:
                    achieved = True
                    break

            if achieved:
                positive_snapshots += 1

    positive_rate = (positive_snapshots / total_snapshots * 100) if total_snapshots > 0 else 0

    return {
        'total_snapshots': total_snapshots,
        'positive_snapshots': positive_snapshots,
        'positive_rate_pct': positive_rate
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_label_improvements.py <path_to_json_file>")
        print("Example: python verify_label_improvements.py data/raw/options_data.json")
        sys.exit(1)

    json_file = sys.argv[1]

    if not Path(json_file).exists():
        print(f"Error: File not found: {json_file}")
        sys.exit(1)

    print("="*80)
    print("LABEL CONFIGURATION VERIFICATION")
    print("="*80)
    print(f"\nLoading data from: {json_file}")

    # Load data
    raw_data = load_json_data(json_file)
    df = flatten_to_dataframe(raw_data)

    print(f"Total records: {len(df):,}")
    print(f"Unique contracts: {df['contract'].nunique():,}")

    # Test configurations
    target_multipliers = [1.3, 1.5, 2.0]
    horizons = [30, 60, 120, None]  # None = EOD

    print("\n" + "="*80)
    print("TESTING DIFFERENT CONFIGURATIONS")
    print("="*80)

    results = []

    for target in target_multipliers:
        for horizon in horizons:
            horizon_str = f"{horizon} min" if horizon is not None else "EOD"

            print(f"\nTesting: {target}x target @ {horizon_str} horizon...")

            stats = count_positive_examples(df, target, horizon)

            results.append({
                'target': target,
                'horizon': horizon_str,
                'total': stats['total_snapshots'],
                'positive': stats['positive_snapshots'],
                'rate_pct': stats['positive_rate_pct']
            })

            print(f"  Total snapshots: {stats['total_snapshots']:,}")
            print(f"  Positive snapshots: {stats['positive_snapshots']:,}")
            print(f"  Positive rate: {stats['positive_rate_pct']:.2f}%")

    # Summary table
    print("\n" + "="*80)
    print("SUMMARY TABLE")
    print("="*80)
    print(f"\n{'Target':<10} {'Horizon':<12} {'Total':<12} {'Positive':<12} {'Rate %':<10}")
    print("-" * 80)

    for r in results:
        print(f"{r['target']}x{' ':<7} {r['horizon']:<12} {r['total']:<12,} {r['positive']:<12,} {r['rate_pct']:<10.2f}")

    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    # Find best configuration (highest positive rate > 1%)
    good_configs = [r for r in results if r['rate_pct'] > 1.0 and r['positive'] > 100]

    if good_configs:
        best = max(good_configs, key=lambda x: x['rate_pct'])
        print(f"\n✓ RECOMMENDED CONFIG:")
        print(f"  Target: {best['target']}x")
        print(f"  Horizon: {best['horizon']}")
        print(f"  Positive rate: {best['rate_pct']:.2f}%")
        print(f"  Positive samples: {best['positive']:,}")
    else:
        print("\n⚠ WARNING: No configuration produced >1% positive rate")
        print("  Possible issues:")
        print("  1. Data collection frequency is too low (snapshots too far apart)")
        print("  2. Price spikes occur between snapshots and are missed")
        print("  3. Options in dataset don't move much intraday")
        print("\n  Suggestions:")
        print("  - Try 1.3x target instead of 1.5x")
        print("  - Collect data more frequently (every 30-60 seconds)")
        print("  - Focus on near-the-money options (more volatile)")

    # NEW config comparison
    print("\n" + "="*80)
    print("NEW CONFIG PERFORMANCE (1.5x @ 60 min)")
    print("="*80)

    new_config = [r for r in results if r['target'] == 1.5 and r['horizon'] == '60 min'][0]
    old_config = [r for r in results if r['target'] == 2.0 and r['horizon'] == 'EOD'][0]

    print(f"\nOLD: 2.0x @ EOD = {old_config['rate_pct']:.2f}% positive rate ({old_config['positive']:,} samples)")
    print(f"NEW: 1.5x @ 60 min = {new_config['rate_pct']:.2f}% positive rate ({new_config['positive']:,} samples)")

    if new_config['positive'] > old_config['positive']:
        improvement = (new_config['positive'] / max(old_config['positive'], 1)) - 1
        print(f"\n✓ IMPROVEMENT: {improvement*100:.1f}% more positive samples!")
    else:
        print(f"\n⚠ No improvement - consider collecting data more frequently")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
