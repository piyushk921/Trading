# src/dhan_api.py

import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from loguru import logger

from .config import SECRETS, get_api_config, get_symbol_id_map, get_symbol_segment_map
from .utils import get_monthly_expiry_date

# --- Constants ---
DHAN_API_URL = "https://api.dhan.co"
OPTION_CHAIN_ENDPOINT = "/v2/optionchain"
EXPIRY_LIST_ENDPOINT = "/v2/optionchain/expirylist"
FUND_LIMIT_ENDPOINT = "/v2/fundlimit" # Corrected endpoint for health checks

# --- API Client Setup ---

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    """
    Creates a requests session that automatically retries on specific HTTP status codes.
    This is crucial for handling transient network or server-side issues.
    """
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

class DhanAPI:
    """
    A wrapper for the Dhan API to fetch option chain data.
    """
    def __init__(self):
        api_config = get_api_config()
        self.client_id = SECRETS.get("DHAN_CLIENT_ID")
        self.access_token = SECRETS.get("DHAN_ACCESS_TOKEN")
        self.symbol_id_map = get_symbol_id_map()
        self.symbol_segment_map = get_symbol_segment_map()

        if not self.client_id or not self.access_token:
            raise ValueError("DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN must be set.")

        self.headers = {
            "Content-Type": "application/json",
            "access-token": self.access_token,
            "client-id": self.client_id,
        }

        self.session = requests_retry_session(
            retries=api_config.get("max_retries", 3),
            backoff_factor=api_config.get("backoff_factor", 0.5),
        )

    def check_api_health(self) -> bool:
        """
        Performs a simple API call to check if the access token is valid.
        Returns True if the token is valid, False otherwise.
        """
        url = f"{DHAN_API_URL}{FUND_LIMIT_ENDPOINT}"
        try:
            # Use a short timeout and no retries for this simple check
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                logger.success("Dhan API token is valid.")
                return True
            elif response.status_code == 401:
                logger.critical("Dhan API token is INVALID (Unauthorized). Please generate a new one.")
                return False
            else:
                logger.error(f"Received unexpected status code {response.status_code} during API health check.")
                return False
        except requests.RequestException as e:
            logger.error(f"API health check failed due to a network error: {e}")
            return False

    def get_expiry_list(self, symbol: str) -> list[str] | None:
        """Fetches the list of valid expiry dates for a given underlying symbol."""
        security_id_str = self.symbol_id_map.get(symbol)
        segment = self.symbol_segment_map.get(symbol)

        if not security_id_str or not segment:
            logger.warning(f"Security ID or Segment not found for symbol '{symbol}' in get_expiry_list. Skipping.")
            return None

        url = f"{DHAN_API_URL}{EXPIRY_LIST_ENDPOINT}"
        payload = {
            "UnderlyingScrip": int(security_id_str),
            "UnderlyingSeg": segment,
        }

        try:
            response = self.session.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status", "failure") == "success":
                expiry_dates = data.get("data", {}).get("ExpiryDateList", [])
                logger.debug(f"Found {len(expiry_dates)} expiry dates for {symbol}: {expiry_dates}")
                return expiry_dates
            else:
                logger.error(f"API returned failure when fetching expiry list for {symbol}: {data.get('remarks')}")
                return None
        except Exception as e:
            logger.exception(f"An error occurred while fetching expiry list for {symbol}: {e}")
            return None

    def get_option_chain(self, symbol: str):
        """
        Fetches the full option chain for a given symbol using a two-step process:
        1. Fetch the list of valid expiry dates.
        2. Use the nearest expiry date to fetch the option chain.
        """
        # Step 1: Get the list of valid expiry dates
        expiry_dates = self.get_expiry_list(symbol)
        if not expiry_dates:
            logger.warning(f"Could not retrieve expiry dates for {symbol}. Cannot fetch option chain.")
            return None

        # Use the first expiry in the list, which is the nearest one.
        nearest_expiry = expiry_dates[0]
        logger.info(f"Using nearest expiry '{nearest_expiry}' for {symbol}.")

        # Step 2: Fetch the option chain using the valid expiry date
        security_id_str = self.symbol_id_map.get(symbol)
        segment = self.symbol_segment_map.get(symbol)

        url = f"{DHAN_API_URL}{OPTION_CHAIN_ENDPOINT}"
        payload = {
            "UnderlyingScrip": int(security_id_str),
            "UnderlyingSeg": segment,
            "Expiry": nearest_expiry
        }

        try:
            logger.debug(f"Requesting Option Chain for {symbol} with payload: {payload}")
            response = self.session.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("status", "failure") == "success":
                return data.get("data") # Return the actual data payload
            else:
                logger.error(f"API returned failure when fetching option chain for {symbol}: {data.get('remarks')}")
                return None
        except Exception as e:
            logger.exception(f"An error occurred while fetching option chain for {symbol}: {e}")
            return None

if __name__ == "__main__":
    # A simple test to verify the API call works.
    # To run this directly: python -m src.dhan_api
    # Make sure you have a .env file in the `dhan_scanner` root.

    # This test uses print() because the logger may not be initialized
    # when running this script standalone.
    print("--- Testing Dhan API Wrapper ---")

    # Create a dummy .env file for testing if it doesn't exist
    from pathlib import Path
    if not (Path(__file__).resolve().parent.parent / ".env").exists():
        with open(Path(__file__).resolve().parent.parent / ".env", "w") as f:
            f.write("DHAN_CLIENT_ID=your_id\n")
            f.write("DHAN_ACCESS_TOKEN=your_token\n")
            f.write("TELEGRAM_BOT_TOKEN=your_bot_token\n")
            f.write("TELEGRAM_CHAT_ID=your_chat_id\n")
        print("Created a dummy .env file. Please fill it with your credentials.")

    try:
        api = DhanAPI()
        symbol_to_test = "NIFTY"
        print(f"Fetching option chain for '{symbol_to_test}'...")

        # This will fail if credentials are fake, but it tests the code path.
        option_chain_data = api.get_option_chain(symbol_to_test)

        if option_chain_data:
            print("--- API Response Summary ---")
            print(f"Status: {option_chain_data.get('status')}")
            print(f"LTP: {option_chain_data.get('underlyingLtp')}")
            print(f"Total Strikes in Chain: {len(option_chain_data.get('optionChainDetails', []))}")
            if option_chain_data.get('optionChainDetails'):
                 print(f"First strike details: {option_chain_data['optionChainDetails'][0]}")
        else:
            print("\nFailed to fetch option chain. This is expected if credentials are not set.")
            print("Please ensure your .env file is configured correctly.")

    except ValueError as e:
        print(f"FATAL: {e}")