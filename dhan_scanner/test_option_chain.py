# dhan_scanner/test_option_chain.py

import sys
from pathlib import Path

# Add the project root to the Python path to allow for absolute imports
# This is a common pattern for making scripts in subdirectories runnable
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.dhan_api import DhanAPI
from src.config import get_universe_symbols

def test_single_symbol(symbol: str):
    """
    Tests the Dhan API option chain fetch for a single symbol and prints a summary.
    """
    print(f"--- Testing Symbol: {symbol} ---")

    try:
        # This will raise a ValueError if secrets are not configured.
        # The __main__ block below handles this.
        api = DhanAPI()

        print(f"Fetching option chain for '{symbol}'...")
        option_chain_data = api.get_option_chain(symbol)

        if not option_chain_data:
            print("\n[FAIL] Failed to fetch option chain.")
            print("Possible reasons:")
            print("- Invalid DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN in your .env file.")
            print("- The symbol may not have an active option chain.")
            print("- Dhan API might be down or returning an error.")
            return

        print("\n[SUCCESS] API call successful. Response summary:")
        print("-" * 40)

        # Print high-level details
        ltp = option_chain_data.get("underlyingLtp")
        print(f"Underlying LTP: {ltp}")
        print(f"Total Strikes in Chain: {len(option_chain_data.get('optionChainDetails', []))}")

        # Inspect the first strike to understand the data structure
        if option_chain_data.get('optionChainDetails'):
            first_strike = option_chain_data['optionChainDetails'][0]
            print("\n--- Structure of the first strike in the chain ---")
            print(f"Strike Price: {first_strike.get('strikePrice')}")

            # CE Data
            ce_data = first_strike.get('callOptionDetails', {})
            print("\nCall Option Keys:")
            if ce_data:
                print(f"  - {'Total Buy Qty:':<25} {ce_data.get('totalBuyQty')}")
                print(f"  - {'Total Sell Qty:':<25} {ce_data.get('totalSellQty')}")
                print(f"  - {'LTP:':<25} {ce_data.get('ltp')}")
                print(f"  - {'Bid Price:':<25} {ce_data.get('bidPrice')}")
                print(f"  - {'Ask Price:':<25} {ce_data.get('askPrice')}")
                print(f"  - {'Open Interest:':<25} {ce_data.get('openInterest')}")
                print(f"  - {'Change in OI:':<25} {ce_data.get('changeInOI')}")
                print(f"  - {'Volume:':<25} {ce_data.get('volume')}")
                print(f"  - {'Implied Volatility (IV):':<25} {ce_data.get('iv')}")
            else:
                print("  (No call option details found)")

            # PE Data
            pe_data = first_strike.get('putOptionDetails', {})
            print("\nPut Option Keys:")
            if pe_data:
                print(f"  - {'Open Interest:':<25} {pe_data.get('openInterest')}")
                print(f"  - {'Change in OI:':<25} {pe_data.get('changeInOI')}")
                print(f"  - {'Volume:':<25} {pe_data.get('volume')}")
            else:
                print("  (No put option details found)")

        print("-" * 40)

    except ValueError as e:
        # This catches the error from DhanAPI.__init__ if secrets are missing
        print(f"\n[FATAL ERROR] {e}")
        print("Please create a .env file in the 'dhan_scanner' directory with your credentials.")
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Check for .env file and guide user if it's missing.
    if not (project_root / ".env").exists():
        print("[SETUP REQUIRED] The .env file is missing.")
        print("Please create a file named '.env' in the 'dhan_scanner' directory")
        print("and add your Dhan and Telegram credentials to it, like so:\n")
        print("DHAN_CLIENT_ID=your_client_id")
        print("DHAN_ACCESS_TOKEN=your_access_token")
        print("TELEGRAM_BOT_TOKEN=your_bot_token")
        print("TELEGRAM_CHAT_ID=your_chat_id")
        sys.exit(1)

    # Use a default symbol from the universe or take one from the command line
    if len(sys.argv) > 1:
        symbol_to_test = sys.argv[1].upper()
    else:
        universe = get_universe_symbols()
        if universe:
            symbol_to_test = universe[0] # Default to the first symbol in the universe
        else:
            print("[ERROR] Universe file is empty. Cannot select a default symbol.")
            sys.exit(1)

    test_single_symbol(symbol_to_test)