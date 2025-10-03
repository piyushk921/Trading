# src/utils.py

from .config import get_strike_selection_config

def choose_strike_step(symbol: str, ltp: float) -> int:
    """
    Determines the appropriate strike step for a given symbol and its LTP.

    Args:
        symbol (str): The trading symbol (e.g., "NIFTY", "RELIANCE").
        ltp (float): The Last Traded Price of the underlying security.

    Returns:
        int: The calculated strike step (e.g., 50, 100 for indices; 1, 5, 10 for stocks).
    """
    config = get_strike_selection_config()

    # Check for index symbols first
    if "NIFTY" in symbol.upper(): # A simple check for NIFTY and BANKNIFTY
        return config.get("index_step", 50)

    # Apply rules for stock options based on LTP
    stock_steps = config.get("stock_steps", [])
    for rule in sorted(stock_steps, key=lambda x: x['max_ltp']):
        if ltp < rule['max_ltp']:
            return rule['step']

    # Fallback to a default step if no rule matches (e.g., for very high priced stocks)
    # The last rule in a well-formed config should have a very high max_ltp, making this rare.
    return stock_steps[-1]['step'] if stock_steps else 10

def calculate_atm_strike(ltp: float, strike_step: int) -> int:
    """
    Calculates the At-The-Money (ATM) strike by rounding the LTP to the nearest
    multiple of the strike step.

    Args:
        ltp (float): The Last Traded Price.
        strike_step (int): The distance between consecutive strike prices.

    Returns:
        int: The calculated ATM strike price.
    """
    return round(ltp / strike_step) * strike_step

def get_strikes_to_check(atm_strike: int, strike_step: int, num_strikes_around: int) -> list[int]:
    """
    Generates a list of strikes to check, centered around the ATM strike.

    Args:
        atm_strike (int): The At-The-Money strike price.
        strike_step (int): The step between strikes.
        num_strikes_around (int): The number of strikes to include on either side of ATM.
                                  (e.g., 2 for ATM-2, ATM-1, ATM, ATM+1, ATM+2).

    Returns:
        list[int]: A sorted list of strike prices to be analyzed.
    """
    strikes = [atm_strike]
    for i in range(1, num_strikes_around + 1):
        strikes.append(atm_strike - (i * strike_step))
        strikes.append(atm_strike + (i * strike_step))

    return sorted(strikes)

def find_closest_available_strike(target_strike: int, available_strikes: list[int]) -> int | None:
    """
    Finds the closest available strike from the option chain data to a target strike.

    This is necessary because the calculated theoretical strike (e.g., 21350) might
    not be present in the API response if it's illiquid or for other reasons.

    Args:
        target_strike (int): The theoretically calculated strike price.
        available_strikes (list[int]): A list of actual strike prices from the API.

    Returns:
        int | None: The closest strike price available, or None if the list is empty.
    """
    if not available_strikes:
        return None

    # Find the strike with the minimum absolute difference from the target
    closest_strike = min(available_strikes, key=lambda x: abs(x - target_strike))
    return closest_strike

if __name__ == "__main__":
    print("--- Testing Strike Utility Functions ---")

    # Test case 1: NIFTY
    nifty_ltp = 21342
    nifty_step = choose_strike_step("NIFTY", nifty_ltp)
    nifty_atm = calculate_atm_strike(nifty_ltp, nifty_step)
    nifty_strikes = get_strikes_to_check(nifty_atm, nifty_step, 2)
    print(f"\nNIFTY LTP: {nifty_ltp}")
    print(f"  - Calculated Step: {nifty_step} (Expected: 50)")
    print(f"  - Calculated ATM: {nifty_atm} (Expected: 21350)")
    print(f"  - Strikes to Check: {nifty_strikes} (Expected: [21250, 21300, 21350, 21400, 21450])")

    # Test case 2: Low-priced stock
    stock1_ltp = 88.5
    stock1_step = choose_strike_step("STOCKA", stock1_ltp)
    stock1_atm = calculate_atm_strike(stock1_ltp, stock1_step)
    stock1_strikes = get_strikes_to_check(stock1_atm, stock1_step, 2)
    print(f"\nStock A LTP: {stock1_ltp}")
    print(f"  - Calculated Step: {stock1_step} (Expected: 1)")
    print(f"  - Calculated ATM: {stock1_atm} (Expected: 89)")
    print(f"  - Strikes to Check: {stock1_strikes} (Expected: [87, 88, 89, 90, 91])")

    # Test case 3: Mid-priced stock
    stock2_ltp = 347.2
    stock2_step = choose_strike_step("STOCKB", stock2_ltp)
    stock2_atm = calculate_atm_strike(stock2_ltp, stock2_step)
    stock2_strikes = get_strikes_to_check(stock2_atm, stock2_step, 2)
    print(f"\nStock B LTP: {stock2_ltp}")
    print(f"  - Calculated Step: {stock2_step} (Expected: 5)")
    print(f"  - Calculated ATM: {stock2_atm} (Expected: 345)")
    print(f"  - Strikes to Check: {stock2_strikes} (Expected: [335, 340, 345, 350, 355])")

    # Test case 4: High-priced stock
    stock3_ltp = 1255
    stock3_step = choose_strike_step("STOCKC", stock3_ltp)
    stock3_atm = calculate_atm_strike(stock3_ltp, stock3_step)
    stock3_strikes = get_strikes_to_check(stock3_atm, stock3_step, 2)
    print(f"\nStock C LTP: {stock3_ltp}")
    print(f"  - Calculated Step: {stock3_step} (Expected: 10)")
    print(f"  - Calculated ATM: {stock3_atm} (Expected: 1260)")
    print(f"  - Strikes to Check: {stock3_strikes} (Expected: [1240, 1250, 1260, 1270, 1280])")

    # Test case 5: Finding closest strike
    available = [21300, 21400, 21500]
    target = 21342
    closest = find_closest_available_strike(21350, available)
    print(f"\nClosest strike to 21350 in {available} is: {closest} (Expected: 21400)")
    available = [21300, 21350, 21400]
    closest = find_closest_available_strike(21350, available)
    print(f"Closest strike to 21350 in {available} is: {closest} (Expected: 21350)")