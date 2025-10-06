# src/dhan_api.py

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from loguru import logger

from .config import SECRETS, get_api_config, get_symbol_id_map, get_symbol_segment_map
from .utils import get_correct_expiry_date

# --- Constants ---
DHAN_API_URL = "https://api.dhan.co"
# The correct endpoint for the v2 Option Chain API, as per user's finding.
OPTION_CHAIN_ENDPOINT = "/v2/optionchain"
FUND_LIMIT_ENDPOINT = "/v2/fundlimit"

# --- API Client Setup ---
def requests_retry_session(
    retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None
):
    session = session or requests.Session()
    retry = Retry(
        total=retries, read=retries, connect=retries,
        backoff_factor=backoff_factor, status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

class DhanAPI:
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
        url = f"{DHAN_API_URL}{FUND_LIMIT_ENDPOINT}"
        try:
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

    def get_option_chain(self, symbol: str):
        """
        Fetches the full option chain for a given symbol using the correct endpoint,
        payload structure, and rule-based expiry date.
        """
        expiry_date = get_correct_expiry_date(symbol)
        logger.info(f"Using calculated expiry '{expiry_date}' for {symbol}.")

        security_id_str = self.symbol_id_map.get(symbol)
        segment = self.symbol_segment_map.get(symbol)

        if not security_id_str or not segment:
            logger.warning(f"Security ID or Segment not found for symbol '{symbol}'. Skipping.")
            return None

        url = f"{DHAN_API_URL}{OPTION_CHAIN_ENDPOINT}"
        # Corrected payload keys as per the user's finding in the documentation.
        payload = {
            "securityId": security_id_str,
            "exchangeSegment": segment,
            "expiryDate": expiry_date
        }

        try:
            logger.debug(f"Requesting Option Chain for {symbol} with payload: {payload}")
            response = self.session.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("status", "failure") == "success" and data.get("data"):
                # The correct data structure is nested under 'data' and then 'oc'
                return {
                    "underlyingLtp": data["data"].get("last_price"),
                    "optionChainDetails": data["data"].get("oc")
                }
            else:
                logger.error(f"API returned failure when fetching option chain for {symbol}: {data.get('remarks')}")
                return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching option chain for {symbol}: {e.response.text}")
            return None
        except Exception as e:
            logger.exception(f"An unexpected error occurred while fetching option chain for {symbol}: {e}")
            return None