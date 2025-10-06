# src/utils.py

from datetime import datetime, timedelta
from calendar import monthrange

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

# --- Expiry Date Calculation Utilities ---

def get_last_tuesday_of_month(year, month):
    """Calculates the date of the last Tuesday of a given month and year."""
    # Last day of the month (day_of_week: 0=Mon, 1=Tue, ..., 6=Sun)
    last_day_of_month, num_days = monthrange(year, month)
    last_date = datetime(year, month, num_days)

    # Calculate how many days to subtract to get to the last Tuesday
    # 1 is the weekday for Tuesday
    offset = (last_date.weekday() - 1) % 7
    last_tuesday = last_date - timedelta(days=offset)
    return last_tuesday

def get_next_tuesday(from_date):
    """Finds the date of the very next Tuesday from a given date."""
    days_ahead = (1 - from_date.weekday() + 7) % 7
    if days_ahead == 0: # If today is Tuesday, get next Tuesday
        days_ahead = 7
    return from_date + timedelta(days=days_ahead)

def get_correct_expiry_date(symbol: str) -> str:
    """
    Determines the correct expiry date string based on the symbol, following user rules.
    - NIFTY: Weekly expiry (nearest upcoming Tuesday).
    - All others: Monthly expiry (last Tuesday of the current month).
    Returns the date in YYYY-MM-DD format as required by the API.
    """
    today = datetime.now().date()

    if symbol == "NIFTY":
        # Find the nearest upcoming Tuesday for weekly expiry
        expiry_date = get_next_tuesday(today)
    else:
        # For all other stocks and indices, find the last Tuesday of the current month
        expiry_date = get_last_tuesday_of_month(today.year, today.month)
        # If the last Tuesday has already passed this month, get the last Tuesday of the next month
        if today > expiry_date.date():
            next_month = today.month % 12 + 1
            next_year = today.year + today.month // 12
            expiry_date = get_last_tuesday_of_month(next_year, next_month)

    return expiry_date.strftime("%Y-%m-%d")