# src/dhan_api.py

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from loguru import logger

from .config import SECRETS, get_api_config, get_symbol_id_map

# --- Constants ---
DHAN_API_URL = "https://api.dhan.co"
OPTION_CHAIN_ENDPOINT = "/v2/optionchain"
EXPIRY_LIST_ENDPOINT = "/v2/optionchain/expirylist"
FUND_LIMIT_ENDPOINT = "/v2/fundlimit"
# The correct, unified segment for all NSE F&O instruments (both stocks and indices)
NSE_FNO_SEGMENT = "NSE_FNO"

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

    def get_expiry_list(self, symbol: str) -> list[str] | None:
        security_id_str = self.symbol_id_map.get(symbol)
        if not security_id_str:
            logger.warning(f"Security ID not found for symbol '{symbol}'. Skipping.")
            return None

        url = f"{DHAN_API_URL}{EXPIRY_LIST_ENDPOINT}"
        params = {
            "securityId": security_id_str,
            "exchangeSegment": NSE_FNO_SEGMENT,
        }

        try:
            response = self.session.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if response.status_code == 200 and data.get("status") == "failure":
                if "no contracts found" in data.get("remarks", "").lower():
                    logger.info(f"No option contracts found for {symbol}. Skipping.")
                else:
                    logger.warning(f"API request for {symbol} failed with remarks: {data.get('remarks')}")
                return None

            if data.get("status", "failure") == "success":
                return data.get("data", {}).get("expiryDateList", [])
            else:
                logger.error(f"API returned failure when fetching expiry list for {symbol}: {data.get('remarks')}")
                return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching expiry list for {symbol}: {e.response.text}")
            return None
        except Exception as e:
            logger.exception(f"An unexpected error occurred while fetching expiry list for {symbol}: {e}")
            return None

    def get_option_chain(self, symbol: str):
        expiry_dates = self.get_expiry_list(symbol)
        if not expiry_dates:
            return None

        nearest_expiry = expiry_dates[0]
        logger.info(f"Using nearest expiry '{nearest_expiry}' for {symbol}.")

        security_id_str = self.symbol_id_map.get(symbol)

        url = f"{DHAN_API_URL}{OPTION_CHAIN_ENDPOINT}"
        params = {
            "securityId": security_id_str,
            "exchangeSegment": NSE_FNO_SEGMENT,
            "expiryDate": nearest_expiry
        }

        try:
            logger.debug(f"Requesting Option Chain for {symbol} with params: {params}")
            response = self.session.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("status", "failure") == "success":
                return data.get("data")
            else:
                logger.error(f"API returned failure when fetching option chain for {symbol}: {data.get('remarks')}")
                return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching option chain for {symbol}: {e.response.text}")
            return None
        except Exception as e:
            logger.exception(f"An unexpected error occurred while fetching option chain for {symbol}: {e}")
            return None