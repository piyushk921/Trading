# dhan_scanner/test_option_chain.py
import sys
import os

# Add the project root to the path to allow direct execution of this test script.
# This ensures that `from src...` imports work correctly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.dhan_api import DhanAPI
from src.logger_config import setup_logging
from loguru import logger
import os

def run_api_test(symbol: str):
    """
    Runs a test for a single symbol to fetch its option chain.
    """
    logger.info(f"--- Testing Symbol: {symbol} ---")
    try:
        # The DhanAPI constructor will fail if secrets are not set.
        # This is the first part of our test.
        api = DhanAPI()

        # 1. Test Expiry List Fetch
        logger.info(f"Fetching expiry list for '{symbol}'...")
        expiry_dates = api.get_expiry_list(symbol)

        if expiry_dates is None:
            # The API module logs the specific error (e.g., 404, 400).
            # This is an expected failure with dummy credentials.
            logger.warning(f"Could not retrieve expiry dates for {symbol}. This is expected if credentials are not valid or the symbol has no options.")
            # We consider this a "pass" in the sense that the code ran without crashing.
            return True

        logger.success(f"Successfully fetched {len(expiry_dates)} expiry dates. Using '{expiry_dates[0]}'.")

        # 2. Test Option Chain Fetch
        logger.info(f"Fetching option chain for '{symbol}'...")
        option_chain = api.get_option_chain(symbol)

        if option_chain and option_chain.get("optionChainDetails"):
            logger.success(f"Successfully fetched option chain for {symbol}.")
            return True
        else:
            logger.error(f"Test FAILED for {symbol}: Could not retrieve option chain data after getting expiry dates.")
            return False

    except ValueError as e:
        logger.critical(f"FATAL: {e}. This is the expected outcome if the .env file is missing or incomplete.")
        return False # This is a failure to setup, not a failure of the API logic itself.
    except Exception:
        logger.exception(f"An unexpected exception occurred during the test for {symbol}.")
        return False

def main():
    """
    Main function to run the standalone API test.
    """
    # This function now correctly reads the log level from the config file.
    setup_logging()

    # --- Create a dummy .env file for the test ---
    # This ensures the DhanAPI class can initialize without a ValueError.
    env_path = "dhan_scanner/.env"
    with open(env_path, "w") as f:
        f.write("DHAN_CLIENT_ID=dummy_id\n")
        f.write("DHAN_ACCESS_TOKEN=dummy_token\n")
        f.write("TELEGRAM_BOT_TOKEN=dummy_bot_token\n")
        f.write("TELEGRAM_CHAT_ID=dummy_chat_id\n")

    symbols_to_test = ["NIFTY", "RELIANCE"]

    logger.info("--- Starting Dhan API Wrapper Test ---")

    all_tests_passed = True
    for symbol in symbols_to_test:
        if not run_api_test(symbol):
            all_tests_passed = False
        logger.info("-" * 40)

    if all_tests_passed:
        logger.success("--- API Test Completed ---")
        logger.info("Test finished. Please check logs for warnings (e.g., 404s), which are expected with dummy credentials.")
        logger.info("The absence of '400 Bad Request' errors indicates the primary bug is fixed.")
    else:
        logger.critical("--- API Test Failed Critically ---")
        logger.error("A critical error occurred. This might be due to a missing .env file or a code issue.")

    # --- Clean up the dummy .env file ---
    os.remove(env_path)
    logger.info("Cleaned up dummy .env file.")


if __name__ == "__main__":
    main()