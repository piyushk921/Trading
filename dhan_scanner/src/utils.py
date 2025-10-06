# src/utils.py

from datetime import datetime

# --- Strike Calculation Utilities ---

def choose_strike_step(symbol, ltp, strike_config):
    """
    Determines the appropriate strike step based on the symbol type and LTP.
    """
    if symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]:
        return strike_config.get("index_step", 50)

    stock_steps = strike_config.get("stock_steps", [])
    for rule in stock_steps:
        if ltp < rule["max_ltp"]:
            return rule["step"]
    # Default to a larger step if LTP is very high
    return 100

def calculate_atm_strike(ltp, strike_step):
    """Calculates the At-The-Money (ATM) strike by rounding to the nearest step."""
    return round(ltp / strike_step) * strike_step

def get_strikes_to_check(atm_strike, strike_step, num_strikes_around):
    """
    Generates a list of strikes to check around the ATM strike.
    """
    strikes = [atm_strike]
    for i in range(1, num_strikes_around + 1):
        strikes.append(atm_strike + (i * strike_step))
        strikes.append(atm_strike - (i * strike_step))
    return sorted(strikes)

def find_closest_available_strike(target_strike, available_strikes):
    """
    Finds the closest strike from a list of available strikes to a target strike.
    """
    if not available_strikes:
        return None
    return min(available_strikes, key=lambda x: abs(x - target_strike))

# --- Expiry Date Selection Utilities ---

def get_correct_expiry_date(symbol: str, available_expiries: list[str]) -> str | None:
    """
    Selects the correct expiry date from a list of available dates provided by the API.

    Args:
        symbol (str): The symbol, e.g., "NIFTY".
        available_expiries (list[str]): A list of date strings in 'YYYY-MM-DD' format.

    Returns:
        str | None: The selected expiry date string, or None if no suitable date is found.
    """
    if not available_expiries:
        return None

    today = datetime.now().date()

    # 1. Parse and filter for future dates
    future_expiries = []
    for date_str in available_expiries:
        try:
            expiry_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if expiry_date >= today:
                future_expiries.append(expiry_date)
        except ValueError:
            continue # Ignore invalid date formats

    if not future_expiries:
        return None

    # 2. Sort the dates
    future_expiries.sort()

    # 3. Select the expiry based on the symbol
    selected_date = None
    if symbol == "NIFTY":
        # For NIFTY, the rule is the nearest weekly expiry.
        selected_date = future_expiries[0]
    else:
        # For others, find the nearest monthly expiry.
        # Heuristic: The monthly expiry is the last one in its month.
        for i, current_date in enumerate(future_expiries):
            # If it's the last date in our list, it must be a monthly expiry
            if i + 1 == len(future_expiries):
                selected_date = current_date
                break

            # If the next date is in a different month, then this one is monthly
            next_date = future_expiries[i+1]
            if current_date.month != next_date.month:
                selected_date = current_date
                break

    # If no monthly expiry was found (e.g., only weeklys left this month),
    # default to the nearest expiry to ensure we always get data.
    if not selected_date and future_expiries:
        selected_date = future_expiries[0]

    return selected_date.strftime("%Y-%m-%d") if selected_date else None