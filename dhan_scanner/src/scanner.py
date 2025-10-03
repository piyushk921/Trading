# src/scanner.py

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

from .dhan_api import DhanAPI
from .config import (
    get_scanner_config, get_signal_config, get_liquidity_config,
    get_universe_symbols
)
from .utils import (
    choose_strike_step, calculate_atm_strike, get_strikes_to_check,
    find_closest_available_strike
)
from .notifier import TelegramNotifier

# In-memory cache to store the previous scan's OI data.
# Format: {symbol: {strike_price: {"ce_oi": val, "pe_oi": val}}}
PREVIOUS_SCAN_OI = {}
# A lock to ensure thread-safe access to the shared OI cache
CACHE_LOCK = threading.Lock()

class Scanner:
    """
    The core scanning engine. It fetches data, processes signals, and manages the scan loop.
    """
    def __init__(self, gui_queue=None):
        """
        Initializes the Scanner.

        Args:
            gui_queue (queue.Queue, optional): A queue to send messages/signals to the GUI.
        """
        self.running = False
        self.scan_thread = None
        self.gui_queue = gui_queue

        # Load configuration
        self.scanner_config = get_scanner_config()
        self.signal_config = get_signal_config()
        self.liquidity_config = get_liquidity_config()
        self.universe = get_universe_symbols()

        # Initialize API client and Notifier
        try:
            self.api = DhanAPI()
            self.notifier = TelegramNotifier()
        except ValueError as e:
            logger.critical(str(e))
            raise  # Re-raise the exception to prevent startup

        logger.info("Scanner initialized.")

    def _send_to_gui(self, message):
        """Sends a message to the GUI queue if it's available."""
        if self.gui_queue:
            self.gui_queue.put(message)

    def start(self):
        """
        Performs a health check and starts the scanning process in a separate thread if healthy.
        """
        if self.running:
            logger.warning("Scanner is already running.")
            return

        # --- Pre-run Health Check ---
        logger.info("Performing API health check before starting...")
        self._send_to_gui("LOG:INFO:Validating API token...")
        if not self.api.check_api_health():
            error_msg = "API token is invalid. Please update it in your .env file and restart."
            logger.critical(error_msg)
            self._send_to_gui(f"LOG:CRITICAL:{error_msg}")
            # Do not start the scanner if the token is bad
            return

        self.running = True
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.scan_thread.start()
        logger.info("Scanner started.")
        self._send_to_gui("LOG:INFO:Scanner started.")

    def stop(self):
        """Stops the scanning process."""
        if not self.running:
            logger.warning("Scanner is not running.")
            return

        self.running = False
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join() # Wait for the thread to finish
        logger.info("Scanner stopped.")
        self._send_to_gui("LOG:INFO:Scanner stopped.")

    def _scan_loop(self):
        """The main loop that runs continuously while `self.running` is True."""
        scan_interval_seconds = self.scanner_config.get("scan_interval_minutes", 5) * 60

        while self.running:
            start_time = time.time()
            logger.info("Starting new scan cycle...")
            self._send_to_gui("LOG:INFO:Starting new scan cycle...")

            self.run_scan_cycle()

            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.info(f"Scan cycle finished in {elapsed_time:.2f} seconds.")
            self._send_to_gui(f"LOG:INFO:Scan cycle finished in {elapsed_time:.2f}s.")

            # Wait for the next scan, but check for stop signal periodically
            wait_time = max(0, scan_interval_seconds - elapsed_time)
            for _ in range(int(wait_time)):
                if not self.running:
                    break
                time.sleep(1)

    def run_scan_cycle(self):
        """
        Executes a single scan cycle over the entire universe of symbols using a thread pool.
        """
        concurrency = self.scanner_config.get("concurrency", 4)
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            # Create a future for each symbol scan
            future_to_symbol = {
                executor.submit(self.process_symbol, symbol): symbol for symbol in self.universe
            }

            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    future.result()
                except Exception:
                    logger.exception(f"'{symbol}' generated an unhandled exception in process_symbol.")
                    self._send_to_gui(f"LOG:ERROR:'{symbol}' generated an exception.")

    def process_symbol(self, symbol: str):
        """
        Fetches and processes option chain data for a single symbol.
        This method is executed in parallel by the thread pool.
        """
        # 1. Fetch data
        option_chain_data = self.api.get_option_chain(symbol)
        if not option_chain_data or not option_chain_data.get("optionChainDetails"):
            logger.warning(f"No option chain data for {symbol}.")
            return None

        ltp = option_chain_data.get("underlyingLtp")
        if not ltp:
            logger.warning(f"No LTP found for {symbol}.")
            return None

        # 2. Determine strikes to check
        strike_step = choose_strike_step(symbol, ltp)
        atm_strike = calculate_atm_strike(ltp, strike_step)
        num_strikes_around = self.scanner_config.get("strikes_to_check", 2)
        target_strikes = get_strikes_to_check(atm_strike, strike_step, num_strikes_around)

        # 3. Map target strikes to available strikes from API response
        available_strikes = [d['strikePrice'] for d in option_chain_data["optionChainDetails"]]
        strikes_to_process = {} # {actual_strike: strike_data_dict}
        for target in target_strikes:
            closest_strike = find_closest_available_strike(target, available_strikes)
            if closest_strike:
                for strike_data in option_chain_data["optionChainDetails"]:
                    if strike_data['strikePrice'] == closest_strike:
                        strikes_to_process[closest_strike] = strike_data
                        break

        if not strikes_to_process:
            logger.debug(f"No relevant strikes found for {symbol} around LTP {ltp}.")
            return None

        # 4. Process each strike for signals and update cache
        new_oi_data_for_symbol = {}
        for strike_price, strike_data in strikes_to_process.items():
            ce_details = strike_data.get('callOptionDetails', {})
            pe_details = strike_data.get('putOptionDetails', {})

            if not self._is_liquid(ce_details, pe_details):
                logger.debug(f"Skipping illiquid strike {strike_price} for {symbol}")
                continue

            current_ce_oi = ce_details.get('openInterest', 0)
            current_pe_oi = pe_details.get('openInterest', 0)

            new_oi_data_for_symbol[strike_price] = {
                "ce_oi": current_ce_oi,
                "pe_oi": current_pe_oi,
            }

            with CACHE_LOCK:
                previous_oi = PREVIOUS_SCAN_OI.get(symbol, {}).get(strike_price)

            if not previous_oi:
                logger.debug(f"First scan for {symbol} at strike {strike_price}. Caching OI.")
                continue

            # Calculate OI change
            ce_oi_change_pct = self._calculate_oi_change(current_ce_oi, previous_oi["ce_oi"])
            pe_oi_change_pct = self._calculate_oi_change(current_pe_oi, previous_oi["pe_oi"])

            # Check for signals
            self._check_for_signal(
                symbol, ltp, strike_price, ce_oi_change_pct, pe_oi_change_pct
            )

        # 5. Atomically update the global cache for this symbol
        if new_oi_data_for_symbol:
            with CACHE_LOCK:
                PREVIOUS_SCAN_OI[symbol] = new_oi_data_for_symbol

        return {"symbol": symbol, "ltp": ltp, "status": "processed"}

    def _is_liquid(self, ce_details, pe_details):
        """Checks if a strike is liquid based on configured rules."""
        min_vol = self.liquidity_config.get("min_option_volume", 0)
        min_oi = self.liquidity_config.get("min_open_interest", 0)
        max_spread_pct = self.liquidity_config.get("max_spread_percentage", 100.0)

        # Check volume and OI for both sides
        if ce_details.get('volume', 0) < min_vol or pe_details.get('volume', 0) < min_vol:
            return False
        if ce_details.get('openInterest', 0) < min_oi or pe_details.get('openInterest', 0) < min_oi:
            return False

        # Check bid-ask spread for the call side (as a proxy)
        bid = ce_details.get('bidPrice', 0)
        ask = ce_details.get('askPrice', 0)
        if bid > 0 and ask > 0:
            spread = ask - bid
            mid_price = (ask + bid) / 2
            if mid_price > 0:
                spread_pct = (spread / mid_price) * 100
                if spread_pct > max_spread_pct:
                    return False

        return True

    def _calculate_oi_change(self, current_oi, prev_oi):
        """Calculates the percentage change in Open Interest."""
        if prev_oi == 0:
            return 999.99 if current_oi > 0 else 0.0 # Handle division by zero
        return ((current_oi - prev_oi) / prev_oi) * 100

    def _check_for_signal(self, symbol, ltp, strike, ce_change, pe_change):
        """Applies the signal logic and notifies if a signal is found."""
        threshold = self.signal_config.get("oi_change_percent_threshold", 30.0)
        signal_found = None

        if ce_change <= -threshold and pe_change > 0:
            signal_found = "LONG"
        elif pe_change <= -threshold and ce_change > 0:
            signal_found = "SHORT"

        if signal_found:
            log_message = (f"Signal: {signal_found} {symbol} @ {ltp} | Strike: {strike} | "
                           f"CE ΔOI: {ce_change:.2f}%, PE ΔOI: {pe_change:.2f}%")
            # Use a different log level for signals to make them stand out
            logger.success(log_message)
            self._send_to_gui(f"LOG:SUCCESS:{log_message}")

            telegram_message = (
                f"📈 *{signal_found} Signal Detected* 📉\n\n"
                f"*Symbol:* `{symbol}`\n"
                f"*LTP:* `{ltp}`\n"
                f"*Trigger Strike:* `{strike}`\n\n"
                f"*CE ΔOI:* `{ce_change:.2f}%`\n"
                f"*PE ΔOI:* `{pe_change:.2f}%`"
            )
            self.notifier.send_notification(telegram_message)

            # Send structured data to the GUI queue if it exists
            if self.gui_queue:
                gui_signal_data = {
                    "type": "SIGNAL",
                    "direction": signal_found,
                    "symbol": symbol,
                    "ltp": ltp,
                    "strike": strike,
                    "ce_change": ce_change,
                    "pe_change": pe_change,
                }
                self.gui_queue.put(gui_signal_data)


if __name__ == "__main__":
    # A simple test to run the scanner in standalone mode without the GUI
    from src.logger_config import setup_logging
    setup_logging()

    logger.info("--- Running Scanner in Standalone Mode ---")
    logger.info("This will run for one cycle and then stop.")

    # Mock the stop function to run only one cycle for testing
    def mock_scan_loop(self):
        logger.info("Starting new scan cycle...")
        self.run_scan_cycle()
        logger.info("Scan cycle finished.")
        self.running = False # Stop after one run

    try:
        # Temporarily replace the real loop with our mock
        Scanner._scan_loop = mock_scan_loop

        scanner = Scanner()
        scanner.start()

        while scanner.running:
            time.sleep(0.5)

        logger.info("--- Standalone Scanner Test Complete ---")

    except ValueError as e:
        logger.critical(f"Could not start scanner: {e}")
    except Exception:
        logger.exception("An unexpected error occurred during standalone test.")