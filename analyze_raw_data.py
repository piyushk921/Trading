"""
Diagnostic script to analyze raw options data and understand why we're getting such low positive rates.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

def analyze_json_file(file_path):
    """Analyze a single JSON file."""
    print(f"\n{'='*80}")
    print(f"Analyzing: {file_path.name}")
    print(f"{'='*80}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Check structure
    print(f"\nFile structure:")
    print(f"  Type: {type(data)}")

    if isinstance(data, list):
        print(f"  Total records: {len(data)}")
        if len(data) > 0:
            print(f"\nFirst record sample:")
            first = data[0]
            for key, value in first.items():
                print(f"    {key}: {value} (type: {type(value).__name__})")

            # Convert to DataFrame for analysis
            df = pd.DataFrame(data)

    elif isinstance(data, dict):
        print(f"  Keys: {list(data.keys())}")

        # Try to find the actual data - could be nested lists
        for key in data.keys():
            if isinstance(data[key], list):
                print(f"\n  '{key}' contains {len(data[key])} records")
                if len(data[key]) > 0:
                    df = pd.DataFrame(data[key])
                    break

        # If no lists found, the dict itself might be contract -> timeseries mapping
        # Example: {"HDFCBANK_1000.0_CE": [...], "HDFCBANK_1000.0_PE": [...]}
        if 'df' not in locals():
            print(f"\n  Detected contract->timeseries structure")
            print(f"  Total contracts: {len(data)}")

            # Sample a few contracts to understand structure
            sample_keys = list(data.keys())[:3]
            print(f"\n  Examining sample contracts:")

            for sample_key in sample_keys:
                sample_data = data[sample_key]
                print(f"\n    {sample_key}:")
                print(f"      Type: {type(sample_data)}")
                if isinstance(sample_data, list):
                    print(f"      Length: {len(sample_data)}")
                    if len(sample_data) > 0:
                        print(f"      First item: {sample_data[0]}")
                elif isinstance(sample_data, dict):
                    print(f"      Keys: {list(sample_data.keys())[:10]}")

                    # If all_history exists, show its structure
                    if 'all_history' in sample_data:
                        history = sample_data['all_history']
                        print(f"      all_history type: {type(history)}")
                        if isinstance(history, list):
                            print(f"      all_history length: {len(history)}")
                            if len(history) > 0:
                                print(f"      First history item: {history[0]}")
                        elif isinstance(history, dict):
                            print(f"      all_history keys: {list(history.keys())[:10]}")

            all_records = []
            for contract_key in data.keys():
                contract_data = data[contract_key]

                if isinstance(contract_data, list):
                    # Each item in the list is a snapshot
                    for snapshot in contract_data:
                        if isinstance(snapshot, dict):
                            # Add the contract identifier to each record
                            snapshot['contract'] = contract_key
                            all_records.append(snapshot)
                elif isinstance(contract_data, dict):
                    # Check if this dict contains timeseries data in nested fields
                    if 'all_history' in contract_data:
                        # Extract the actual timeseries from all_history
                        history = contract_data['all_history']
                        if isinstance(history, list):
                            for snapshot in history:
                                if isinstance(snapshot, dict):
                                    snapshot['contract'] = contract_key
                                    all_records.append(snapshot)
                        elif isinstance(history, dict):
                            # Single snapshot
                            history['contract'] = contract_key
                            all_records.append(history)
                    else:
                        # Single snapshot as dict (no nested history)
                        contract_data['contract'] = contract_key
                        all_records.append(contract_data)

            if all_records:
                print(f"\n  Flattened {len(all_records):,} total records from {len(data)} contracts")
                df = pd.DataFrame(all_records)
            else:
                print("\n  Could not extract records from contract data")

    if 'df' not in locals():
        print("Could not parse data into DataFrame")
        return

    print(f"\n{'='*80}")
    print("DATAFRAME ANALYSIS")
    print(f"{'='*80}")
    print(f"\nTotal rows: {len(df):,}")
    print(f"\nColumns ({len(df.columns)}): {list(df.columns)[:20]}")  # Limit to first 20
    if len(df.columns) > 20:
        print(f"  ... and {len(df.columns) - 20} more columns")
    print(f"\nData types (first 20):")
    print(df.dtypes.head(20))

    # Analyze timestamps
    if 'timestamp' in df.columns:
        df['dt'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('dt')

        print(f"\n{'='*80}")
        print("TIMESTAMP ANALYSIS")
        print(f"{'='*80}")
        print(f"First timestamp: {df['dt'].min()}")
        print(f"Last timestamp: {df['dt'].max()}")
        print(f"Duration: {df['dt'].max() - df['dt'].min()}")

        # Check gaps between snapshots
        time_diffs = df['dt'].diff()
        print(f"\nTime gaps between snapshots:")
        print(f"  Mean: {time_diffs.mean()}")
        print(f"  Median: {time_diffs.median()}")
        print(f"  Min: {time_diffs.min()}")
        print(f"  Max: {time_diffs.max()}")

        # Most common gaps
        print(f"\nMost common time gaps:")
        gap_seconds = time_diffs.dt.total_seconds()
        print(gap_seconds.value_counts().head(10))

    # Analyze prices
    price_fields = [col for col in df.columns if 'price' in col.lower() or col in ['ltp', 'close', 'last_price']]

    if price_fields:
        print(f"\n{'='*80}")
        print("PRICE ANALYSIS")
        print(f"{'='*80}")
        print(f"Price-related fields found: {price_fields}")

        for field in price_fields:
            print(f"\n{field}:")
            print(f"  Min: {df[field].min()}")
            print(f"  Max: {df[field].max()}")
            print(f"  Mean: {df[field].mean():.2f}")
            print(f"  Median: {df[field].median():.2f}")
            print(f"  Non-zero values: {(df[field] > 0).sum()}/{len(df)}")

    # Analyze option types
    if 'option_type' in df.columns:
        print(f"\n{'='*80}")
        print("OPTION TYPE DISTRIBUTION")
        print(f"{'='*80}")
        print(df['option_type'].value_counts())

    # Analyze symbols/underlyings
    if 'underlying' in df.columns:
        print(f"\n{'='*80}")
        print("TOP 10 UNDERLYINGS")
        print(f"{'='*80}")
        print(df['underlying'].value_counts().head(10))

    # Most important: Analyze actual price movements
    contract_field = 'contract' if 'contract' in df.columns else 'symbol'
    price_field = None

    # Find the price field (prioritize 'price' over 'close' as 'close' might be all zeros)
    for possible_price in ['ltp', 'price', 'last_price', 'close']:
        if possible_price in df.columns:
            price_field = possible_price
            break

    if contract_field in df.columns and price_field and 'timestamp' in df.columns:
        print(f"\n{'='*80}")
        print("PRICE MOVEMENT ANALYSIS (Critical!)")
        print(f"{'='*80}")
        print(f"Using contract field: {contract_field}")
        print(f"Using price field: {price_field}")

        # Pick a few random contracts and analyze their intraday moves
        sample_symbols = df[contract_field].value_counts().head(20).index.tolist()

        movements_1_5x = 0
        movements_2x = 0
        total_contracts = 0

        print(f"\nAnalyzing {len(sample_symbols)} most active contracts...")

        for symbol in sample_symbols[:20]:  # Analyze top 20
            symbol_df = df[df[contract_field] == symbol].sort_values('dt')

            if len(symbol_df) < 2:
                continue

            total_contracts += 1
            prices = symbol_df[price_field].values

            # Check each snapshot: did price go 1.5x or 2x from this point?
            for i in range(len(prices) - 1):
                current_price = prices[i]
                if current_price <= 0:
                    continue

                future_prices = prices[i+1:]
                max_future = future_prices.max()

                multiplier = max_future / current_price

                if multiplier >= 2.0:
                    movements_2x += 1
                elif multiplier >= 1.5:
                    movements_1_5x += 1

        print(f"\nResults from {total_contracts} contracts:")
        print(f"  Snapshots that achieved 1.5x: {movements_1_5x}")
        print(f"  Snapshots that achieved 2x: {movements_2x}")

        if movements_2x == 0 and movements_1_5x == 0:
            print(f"\n⚠️  WARNING: NO 1.5x or 2x movements found in sample!")
            print(f"   This suggests:")
            print(f"   1. Snapshots are too infrequent (missing peaks)")
            print(f"   2. OR options simply don't move that much in this data")
            print(f"   3. OR wrong price field is being used")

def main():
    """Analyze recent data files."""
    import sys

    if len(sys.argv) > 1:
        # Use file/directory path provided as argument
        input_path = Path(sys.argv[1])
        if not input_path.exists():
            print(f"Path {input_path} not found!")
            return

        if input_path.is_dir():
            # If directory provided, find all JSON files in it
            json_files = sorted(input_path.glob("*.json"))
            if not json_files:
                print(f"No JSON files found in {input_path}")
                return
            print(f"Found {len(json_files)} JSON files in directory")
            # Analyze the most recent file
            file_path = json_files[-1]
            print(f"Analyzing most recent file: {file_path.name}\n")
            analyze_json_file(file_path)
        else:
            # Analyze the specific file
            analyze_json_file(input_path)
    else:
        # Default behavior: look for directory
        data_dir = Path("data/raw_last4days")

        if not data_dir.exists():
            print(f"Directory {data_dir} not found!")
            print(f"Usage: python {sys.argv[0]} <json_file_path>")
            return

        json_files = sorted(data_dir.glob("*.json"))

        if not json_files:
            print(f"No JSON files found in {data_dir}")
            return

        print(f"Found {len(json_files)} JSON files")

        # Analyze the most recent file in detail
        latest_file = json_files[-1]
        analyze_json_file(latest_file)

    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
