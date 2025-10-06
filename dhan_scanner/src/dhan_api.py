# src/dhan_api.py

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from loguru import logger

from .config import SECRETS, get_api_config, get_symbol_id_map
from .utils import get_correct_expiry_date

# --- Constants ---
DHAN_API_URL = "https://api.dhan.co"
EXPIRY_LIST_ENDPOINT = "/v2/optionchain/expirylist"
OPTION_CHAIN_ENDPOINT = "/v2/optionchain"
FUND_LIMIT_ENDPOINT = "/v2/fundlimit"
# The required segment for all F&O instruments as per user instruction.
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

    def get_expiry_list(self, symbol: str):
        """
        Fetches the list of all available expiry dates for a given underlying symbol.
        This endpoint uses POST with a different segment logic than the option chain.
        """
        security_id_val = self.symbol_id_map.get(symbol)
        if not security_id_val:
            logger.warning(f"No Security ID for {symbol} to fetch expiry list.")
            return None

        try:
            security_id = int(security_id_val)
        except (ValueError, TypeError):
            logger.error(f"Invalid Security ID format for {symbol}: '{security_id_val}'")
            return None

        # Determine segment for expiry list endpoint (IDX_I or EQ_O)
        segment = "IDX_I" if symbol.upper() in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"] else "EQ_O"
        url = f"{DHAN_API_URL}{EXPIRY_LIST_ENDPOINT}"
        payload = {"UnderlyingScrip": security_id, "UnderlyingSeg": segment}

        try:
            response = self.session.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status", "failure") == "success" and data.get("data"):
                logger.info(f"Found {len(data['data'])} expiry dates for {symbol}.")
                return data["data"]
            else:
                logger.error(f"API returned failure for expiry list for {symbol}: {data.get('remarks')}")
                return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching expiry list for {symbol}: {e.response.text}")
            return None
        except Exception:
            logger.exception(f"Unexpected error fetching expiry list for {symbol}.")
            return None

    def get_option_chain(self, symbol: str):
        """
        Fetches the full option chain using a robust two-step process, with GET request
        and a unified NSE_FNO segment as per user instruction.
        """
        # Step 1: Get the list of actual, valid expiry dates from the API
        expiry_dates = self.get_expiry_list(symbol)
        if not expiry_dates:
            logger.warning(f"Could not retrieve expiry dates for {symbol}. Cannot fetch option chain.")
            return None

        # Step 2: Select the correct expiry date from the list using our logic
        expiry_date = get_correct_expiry_date(symbol, expiry_dates)
        if not expiry_date:
            logger.warning(f"No suitable future expiry date found for {symbol}. Skipping.")
            return None

        logger.info(f"Selected expiry '{expiry_date}' for {symbol} from API list.")

        # Step 3: Fetch the option chain using the validated expiry date
        security_id_val = self.symbol_id_map.get(symbol)
        try:
            security_id = int(security_id_val)
        except (ValueError, TypeError):
            logger.error(f"Invalid Security ID format for {symbol}: '{security_id_val}'.")
            return None

        url = f"{DHAN_API_URL}{OPTION_CHAIN_ENDPOINT}"
        # Parameters for the GET request, with corrected keys and segment.
        params = {
            "securityId": security_id,
            "exchangeSegment": NSE_FNO_SEGMENT, # Using the required unified segment
            "expiryDate": expiry_date
        }

        try:
            logger.debug(f"Requesting Option Chain for {symbol} with GET params: {params}")
            response = self.session.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("status", "failure") == "success" and data.get("data"):
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
        except Exception:
            logger.exception(f"An unexpected error occurred while fetching option chain for {symbol}.")
            return None