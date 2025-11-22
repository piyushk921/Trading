#!/usr/bin/env python3
"""
Subsample large dataset for faster training and testing.

Use this to create a smaller dataset from your full data for:
- Quick testing
- Systems with limited RAM
- Faster iteration
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from options_ml.data.loader import load_multiple_json_files
from options_ml.utils.logging_utils import setup_logger

logger = setup_logger(__name__)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Subsample large dataset")
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Directory containing raw JSON files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw_subset",
        help="Output directory for subsampled data"
    )
    parser.add_argument(
        "--sample-rate",
        type=float,
        default=0.3,
        help="Fraction of data to keep (0.3 = 30%%, default: 0.3)"
    )
    parser.add_argument(
        "--recent-days",
        type=int,
        default=None,
        help="Use only N most recent days (alternative to sample-rate)"
    )
    parser.add_argument(
        "--symbols-per-underlying",
        type=int,
        default=None,
        help="Keep only N symbols per underlying (e.g., 5 strikes per stock)"
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("SUBSAMPLING DATASET")
    logger.info("=" * 80)
    logger.info(f"Input directory: {args.input_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Sample rate: {args.sample_rate}")

    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Load data
    input_path = Path(args.input_dir)
    json_files = sorted(list(input_path.glob("*.json")))

    if not json_files:
        logger.error(f"No JSON files found in {input_path}")
        sys.exit(1)

    logger.info(f"Found {len(json_files)} JSON files")

    # Filter by recent days if specified
    if args.recent_days:
        logger.info(f"Keeping only {args.recent_days} most recent days")
        json_files = json_files[-args.recent_days:]
        logger.info(f"Selected {len(json_files)} files")

    # Load and subsample
    for json_file in json_files:
        logger.info(f"Processing {json_file.name}...")

        # Load JSON
        import json
        with open(json_file, 'r') as f:
            data = json.load(f)

        logger.info(f"  Original: {len(data)} symbols")

        # Subsample by symbol
        if args.sample_rate < 1.0:
            import random
            symbols = list(data.keys())
            n_keep = int(len(symbols) * args.sample_rate)
            sampled_symbols = random.sample(symbols, n_keep)
            data = {k: v for k, v in data.items() if k in sampled_symbols}
            logger.info(f"  After sampling: {len(data)} symbols")

        # Limit symbols per underlying
        if args.symbols_per_underlying:
            from collections import defaultdict
            by_underlying = defaultdict(list)

            for symbol in data.keys():
                underlying = symbol.split('_')[0]
                by_underlying[underlying].append(symbol)

            filtered_data = {}
            for underlying, symbols in by_underlying.items():
                keep_symbols = symbols[:args.symbols_per_underlying]
                for symbol in keep_symbols:
                    filtered_data[symbol] = data[symbol]

            data = filtered_data
            logger.info(f"  After limiting per underlying: {len(data)} symbols")

        # Save subsampled data
        output_file = Path(args.output_dir) / json_file.name
        with open(output_file, 'w') as f:
            json.dump(data, f)

        logger.info(f"  Saved to {output_file}")

    logger.info("\n" + "=" * 80)
    logger.info("SUBSAMPLING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Subsampled data saved to: {args.output_dir}")
    logger.info(f"\nNext step: Run prepare_training_data.py with --input-dir {args.output_dir}")


if __name__ == "__main__":
    main()
