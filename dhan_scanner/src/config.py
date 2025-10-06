# src/config.py

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# --- Constants ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Embedded Symbol Maps ---
# This map is now embedded directly into the code to prevent file-not-found errors
# and make the application more robust and self-contained.
SYMBOL_TO_ID_MAP = {
    "011NSETEST": "1", "021NSETEST": "2", "031NSETEST": "3", "041NSETEST": "4", "051NSETEST": "5",
    "061NSETEST": "6", "071NSETEST": "7", "081NSETEST": "8", "091NSETEST": "9", "101NSETEST": "10",
    "111NSETEST": "11", "121NSETEST": "12", "131NSETEST": "13", "141NSETEST": "14", "151NSETEST": "15",
    "161NSETEST": "16", "171NSETEST": "17", "181NSETEST": "18", "360ONE": "403", "ABB": "13",
    "ABCAPITAL": "523", "ADANIENSOL": "3504", "ADANIENT": "3506", "ADANIGREEN": "3861",
    "ADANIPORTS": "3529", "ALKEM": "1719", "AMBER": "2601", "AMBUJACEM": "114", "ANGELONE": "4075",
    "APLAPOLLO": "143", "APOLLOHOSP": "157", "ASHOKLEY": "202", "ASIANPAINT": "212", "ASTRAL": "226",
    "AUBANK": "2323", "AUROPHARMA": "236", "AXISBANK": "242", "BAJAJ-AUTO": "275", "BAJAJFINSV": "281",
    "BAJFINANCE": "278", "BALKRISIND": "291", "BALRAMCHIN": "297", "BANDHANBNK": "2623",
    "BANKBARODA": "301", "BANKINDIA": "303", "BANKNIFTY": "26001", "BATAINDIA": "322", "BDL": "2787",
    "BEL": "328", "BERGEPAINT": "341", "BHARATFORG": "358", "BHARTIARTL": "363", "BHEL": "367",
    "BIOCON": "374", "BLUESTARCO": "395", "BOSCHLTD": "2181", "BPCL": "401", "BRITANNIA": "416",
    "BSE": "443", "BSOFT": "383", "CAMS": "4225", "CANBK": "439", "CANFINHOME": "442", "CDSL": "2525",
    "CENTURYTEX": "468", "CGPOWER": "1195", "CHAMBLFERT": "475", "CHOLAFIN": "504", "CIPLA": "526",
    "COALINDIA": "4420", "COFORGE": "2374", "COLPAL": "544", "CONCOR": "558", "COROMANDEL": "572",
    "CROMPTON": "586", "CUB": "600", "CUMMINSIND": "603", "CYIENT": "1410", "DABUR": "620",
    "DALBHARAT": "628", "DEEPAKNTR": "651", "DELHIVERY": "4955", "DELTAcorp": "664", "DIVISLAB": "703",
    "DIXON": "2553", "DLF": "694", "DMART": "2376", "DRREDDY": "727", "EICHERMOT": "772",
    "ESCORTS": "804", "ETERNAL": "4889", "EXIDEIND": "822", "FEDERALBNK": "841", "FINNIFTY": "26011",
    "FORTIS": "890", "GAIL": "918", "GLENMARK": "972", "GMRINFRA": "995", "GNFC": "1003",
    "GODREJCP": "1008", "GODREJPROP": "4215", "GRANULES": "1032", "GRASIM": "1035",
    "GUJGASLTD": "1801", "HAL": "2764", "HAVELLS": "1121", "HCLTECH": "1152", "HDFCAMC": "3015",
    "HDFCBANK": "1154", "HDFCLIFE": "2552", "HEROMOTOCO": "1191", "HFCL": "1194", "HINDALCO": "1223",
    "HINDCOPPER": "1226", "HINDPETRO": "1230", "HINDUNILVR": "1232", "HINDZINC": "1234",
    "HUDCO": "2443", "ICICIBANK": "1284", "ICICIGI": "2573", "ICICIPRULI": "2179", "IDEA": "1298",
    "IDFC": "1303", "IDFCFIRSTB": "3103", "IEX": "2538", "IGL": "1330", "IIFL": "4722",
    "INDHOTEL": "1346", "INDIACEM": "1338", "INDIANB": "1343", "INDIGO": "1794", "INDUSINDBK": "1357",
    "INDUSTOWER": "4273", "INFY": "1394", "INOXWIND": "1537", "IOC": "1403", "IPCALAB": "1406",
    "IRCTC": "3787", "IREDA": "5865", "IRFC": "4450", "ITC": "1474", "JINDALSTEL": "1502",
    "JIOFIN": "5793", "JKCEMENT": "1512", "JSWENERGY": "4318", "JSWSTEEL": "1529", "JUBLFOOD": "4390",
    "KALYANKJIL": "4790", "KAYNES": "5325", "KEI": "1618", "KFINTECH": "5426", "KOTAKBANK": "1660",
    "KPITTECH": "3412", "LAURUSLABS": "2115", "LICHSGFIN": "1765", "LICI": "5040", "LODHA": "4628",
    "LT": "1736", "LTF": "4639", "LTIM": "5387", "LUPIN": "1778", "M&M": "1828", "M&MFIN": "1829",
    "MANAPPURAM": "4416", "MANKIND": "5633", "MARICO": "1859", "MARUTI": "1869", "MAXHEALTH": "4261",
    "MAZDOCK": "4233", "MCX": "2031", "METROPOLIS": "3426", "MFSL": "1834", "MIDCPNIFTY": "26037",
    "MOTHERSON": "3326", "MPHASIS": "1850", "MRF": "1941", "MUTHOOTFIN": "4683", "NATIONALUM": "2007",
    "NAUKRI": "4264", "NAVINFLUOR": "2013", "NBCC": "2055", "NCC": "2018", "NESTLEIND": "2032",
    "NHPC": "4252", "NIFTY": "26000", "NIFTYNXT50": "26002", "NMDC": "2060", "NTPC": "2103",
    "NUVAMA": "5885", "NYKAA": "4888", "OBEROIRLTY": "4569", "OFSS": "1429", "OIL": "2204",
    "ONGC": "2214", "PAGEIND": "4204", "PATANJALI": "5123", "PAYTM": "4887", "PEL": "2333",
    "PERSISTENT": "4208", "PETRONET": "2306", "PFC": "2312", "PGEL": "2661", "PHOENIXLTD": "2325",
    "PIDILITIND": "2328", "PIIND": "4554", "PNB": "2374", "PNBHOUSING": "2123", "POLICYBZR": "4886",
    "POLYCAB": "3439", "POWERGRID": "2351", "POWERINDIA": "3948", "PPLPHARMA": "5135",
    "PRESTIGE": "4593", "RBLBANK": "2124", "RECLTD": "2430", "RELIANCE": "2475", "RVNL": "3481",
    "SAIL": "2533", "SAMMAANCAP": "4514", "SBICARD": "3934", "SBILIFE": "2579", "SBIN": "2574",
    "SHREECEM": "2667", "SHRIRAMFIN": "2674", "SIEMENS": "2694", "SOLARINDS": "2708",
    "SONACOMS": "4729", "SRF": "2720", "SUNPHARMA": "2769", "SUNTV": "2775", "SUPREMEIND": "2781",
    "SUZLON": "2787", "SYNGENE": "1793", "TATACONSUM": "2841", "TATAELXSI": "2867",
    "TATAMOTORS": "2885", "TATAPOWER": "2888", "TATASTEEL": "2892", "TATATECH": "5900",
    "TCS": "2903", "TECHM": "2918", "TIINDIA": "4815", "TITAGARH": "2986", "TITAN": "2992",
    "TORNTPHARM": "3015", "TORNTPOWER": "3018", "TRENT": "3048", "TVSMOTOR": "3082",
    "ULTRACEMCO": "3103", "UNIONBANK": "3116", "UNITDSPR": "1845", "UNOMINDA": "3134",
    "UPL": "3140", "VBL": "2120", "VEDL": "2650", "VOLTAS": "3193", "WIPRO": "3238",
    "YESBANK": "3277", "ZEEL": "3307", "ZOMATO": "4739", "ZYDUSLIFE": "432"
}

# --- Configuration Loading ---

def load_config(config_path=None):
    """Loads the YAML configuration file."""
    if config_path is None:
        config_path = BASE_DIR / "config" / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        logger.error(f"Configuration file not found at {config_path}")
        return {}

    with open(config_path, "r") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Could not parse YAML configuration file: {e}")
            return {}

def get_secrets():
    """Loads secrets from environment variables or a .env file."""
    path_exact = BASE_DIR / ".env"
    path_with_txt = BASE_DIR / ".env.txt"

    dotenv_path_to_load = None
    if path_exact.exists():
        dotenv_path_to_load = path_exact
    elif path_with_txt.exists():
        dotenv_path_to_load = path_with_txt

    if dotenv_path_to_load:
        logger.info(f"Loading credentials from: {dotenv_path_to_load}")
        load_dotenv(dotenv_path=dotenv_path_to_load)
    else:
        logger.warning("No .env file found. Relying on system environment variables.")

    required_secrets = ["DHAN_CLIENT_ID", "DHAN_ACCESS_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    secrets = {key: os.getenv(key) for key in required_secrets}

    missing_secrets = [key for key, value in secrets.items() if value is None]
    if missing_secrets:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_secrets)}. Please set them in your environment or a .env file.")

    return secrets

# --- Main Configuration Objects ---
CONFIG = load_config()
try:
    SECRETS = get_secrets()
except ValueError as e:
    logger.critical(e)
    SECRETS = {}

# --- Helper Functions to Access Config ---

def get_scanner_config():
    return CONFIG.get("scanner", {})

def get_signal_config():
    return CONFIG.get("signal", {})

def get_liquidity_config():
    return CONFIG.get("liquidity", {})

def get_strike_selection_config():
    return CONFIG.get("strike_selection", {})

def get_api_config():
    return CONFIG.get("api", {})

def get_logging_config():
    return CONFIG.get("logging", {})

def get_universe_symbols():
    """Reads the universe symbols from the specified file."""
    universe_path = BASE_DIR / "config" / "universe_symbols.txt"
    if not universe_path.exists():
        logger.error(f"Universe file not found at {universe_path}")
        return []
    with open(universe_path, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def get_symbol_id_map():
    """Returns the embedded symbol-to-ID map."""
    return SYMBOL_TO_ID_MAP