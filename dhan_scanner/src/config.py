# src/config.py

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# --- Constants ---
# Define the base directory of the project.
# Assumes this script is in `src/`, so `Path(__file__).parent.parent` is the project root.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Configuration Loading ---

def load_config(config_path=None):
    """
    Loads the YAML configuration file.

    Args:
        config_path (str, optional): The path to the config.yaml file.
                                     Defaults to BASE_DIR/config/config.yaml.

    Returns:
        dict: A dictionary containing the configuration parameters.
              Returns an empty dict if the file is not found.
    """
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
    """
    Loads secrets from environment variables.

    This function explicitly loads from a .env file for local development ease,
    but in production, environment variables should be set directly.

    Returns:
        dict: A dictionary containing the required secrets.

    Raises:
        ValueError: If any of the required environment variables are not set.
    """
    # --- Robust .env file loading ---
    # Checks for both `.env` and `.env.txt` to handle common Windows file naming issues.
    path_exact = BASE_DIR / ".env"
    path_with_txt = BASE_DIR / ".env.txt"

    dotenv_path_to_load = None

    if path_exact.exists():
        logger.info(f"Found credentials file at: {path_exact}")
        dotenv_path_to_load = path_exact
    elif path_with_txt.exists():
        logger.warning(f"Found credentials file at '{path_with_txt}'.")
        logger.warning("This is likely because the file was saved as a text file.")
        logger.warning("For best practice, please rename it to just '.env'.")
        dotenv_path_to_load = path_with_txt
    else:
        logger.warning(f"No .env file found at '{path_exact}' or '{path_with_txt}'.")
        logger.warning("The application will rely on system environment variables.")

    if dotenv_path_to_load:
        load_dotenv(dotenv_path=dotenv_path_to_load)

    required_secrets = [
        "DHAN_CLIENT_ID",
        "DHAN_ACCESS_TOKEN",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]

    secrets = {key: os.getenv(key) for key in required_secrets}

    missing_secrets = [key for key, value in secrets.items() if value is None]

    if missing_secrets:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_secrets)}. "
            "Please set them in your environment or a .env file in the project root."
        )

    return secrets

# --- Main Configuration Objects ---

# Load configuration and secrets when the module is imported.
# This makes them available as global objects for other modules to use.
CONFIG = load_config()
try:
    SECRETS = get_secrets()
except ValueError as e:
    print(f"FATAL: {e}")
    # For this structure, other modules importing this will see the error.
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
    """Loads the symbol to security ID mapping from the JSON file."""
    map_path = BASE_DIR / "config" / "symbol_to_id.json"
    if not map_path.exists():
        logger.error(f"Symbol to ID map file not found at {map_path}")
        return {}
    with open(map_path, "r") as f:
        import json
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from {map_path}")
            return {}

def get_symbol_segment_map():
    """Loads the symbol to API segment mapping from the JSON file."""
    map_path = BASE_DIR / "config" / "symbol_to_segment.json"
    if not map_path.exists():
        logger.error(f"Symbol to Segment map file not found at {map_path}")
        return {}
    with open(map_path, "r") as f:
        import json
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from {map_path}")
            return {}

if __name__ == "__main__":
    # Example of how to use this module and a simple test
    # Note: For this standalone test, logger might not be configured.
    # We are using basic print statements here intentionally.
    print("--- Configuration Loaded ---")
    print(f"Scan Interval: {get_scanner_config().get('scan_interval_minutes')} minutes")
    print(f"Signal Threshold: {get_signal_config().get('oi_change_percent_threshold')}%")

    print("\n--- Secrets (checking if loaded) ---")
    try:
        secrets_test = get_secrets()
        print("Secrets loaded successfully.")
    except ValueError as e:
        print(f"Secrets check failed as expected (if .env is missing): {e}")


    print("\n--- Universe ---")
    symbols = get_universe_symbols()
    print(f"Found {len(symbols)} symbols in universe: {symbols[:5]}...")

    print("\n--- Symbol ID Map ---")
    symbol_map = get_symbol_id_map()
    print(f"Found {len(symbol_map)} symbol mappings: {list(symbol_map.keys())[:5]}...")