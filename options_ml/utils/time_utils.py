"""
Time and date utilities for options trading.

Handles IST timezone, market hours, and timestamp parsing.
"""

from datetime import datetime, time, timedelta
from typing import Optional
import pytz


# Indian Standard Time timezone
IST = pytz.timezone("Asia/Kolkata")

# Market hours
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)


def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse timestamp string to datetime object.

    Args:
        timestamp_str: Timestamp string in various formats

    Returns:
        datetime object (timezone-naive or aware)

    Raises:
        ValueError: If timestamp format is not recognized
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    # Try ISO format
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        raise ValueError(f"Unable to parse timestamp: {timestamp_str}")


def get_ist_now() -> datetime:
    """
    Get current time in IST.

    Returns:
        Current datetime in IST timezone
    """
    return datetime.now(IST)


def is_market_hours(
    dt: Optional[datetime] = None,
    open_time: time = MARKET_OPEN,
    close_time: time = MARKET_CLOSE,
) -> bool:
    """
    Check if given datetime is within market hours.

    Args:
        dt: Datetime to check (default: current time in IST)
        open_time: Market open time
        close_time: Market close time

    Returns:
        True if within market hours, False otherwise
    """
    if dt is None:
        dt = get_ist_now()

    # Ensure datetime is in IST
    if dt.tzinfo is None:
        dt = IST.localize(dt)
    elif dt.tzinfo != IST:
        dt = dt.astimezone(IST)

    current_time = dt.time()

    # Check if it's a weekday (Monday=0, Sunday=6)
    if dt.weekday() >= 5:  # Saturday or Sunday
        return False

    return open_time <= current_time <= close_time


def minutes_to_market_close(
    dt: Optional[datetime] = None,
    close_time: time = MARKET_CLOSE,
) -> float:
    """
    Calculate minutes remaining until market close.

    Args:
        dt: Reference datetime (default: current time in IST)
        close_time: Market close time

    Returns:
        Minutes to market close (negative if market is closed)
    """
    if dt is None:
        dt = get_ist_now()

    # Ensure datetime is in IST
    if dt.tzinfo is None:
        dt = IST.localize(dt)
    elif dt.tzinfo != IST:
        dt = dt.astimezone(IST)

    # Create closing datetime for today
    close_dt = dt.replace(
        hour=close_time.hour,
        minute=close_time.minute,
        second=close_time.second,
        microsecond=0
    )

    # Calculate difference
    delta = close_dt - dt
    return delta.total_seconds() / 60.0


def minutes_between(dt1: datetime, dt2: datetime) -> float:
    """
    Calculate minutes between two datetimes.

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        Minutes between dt1 and dt2 (positive if dt2 > dt1)
    """
    delta = dt2 - dt1
    return delta.total_seconds() / 60.0


def add_minutes(dt: datetime, minutes: float) -> datetime:
    """
    Add minutes to a datetime.

    Args:
        dt: Base datetime
        minutes: Minutes to add

    Returns:
        New datetime
    """
    return dt + timedelta(minutes=minutes)


def encode_time_of_day(dt: datetime) -> tuple[float, float, float]:
    """
    Encode time of day as cyclical features and minutes since open.

    Args:
        dt: Datetime to encode

    Returns:
        Tuple of (minutes_since_open, sin_time, cos_time)
    """
    # Minutes since market open
    market_open_dt = dt.replace(
        hour=MARKET_OPEN.hour,
        minute=MARKET_OPEN.minute,
        second=0,
        microsecond=0
    )
    minutes_since_open = minutes_between(market_open_dt, dt)

    # Cyclical encoding (assuming 6 hour 15 min market = 375 minutes)
    total_market_minutes = 375.0
    angle = (minutes_since_open / total_market_minutes) * 2 * 3.14159265359

    import math
    sin_time = math.sin(angle)
    cos_time = math.cos(angle)

    return minutes_since_open, sin_time, cos_time


def get_date_string(dt: Optional[datetime] = None) -> str:
    """
    Get date string in YYYY-MM-DD format.

    Args:
        dt: Datetime (default: current IST time)

    Returns:
        Date string
    """
    if dt is None:
        dt = get_ist_now()
    return dt.strftime("%Y-%m-%d")


def get_timestamp_string(dt: Optional[datetime] = None) -> str:
    """
    Get timestamp string in standard format.

    Args:
        dt: Datetime (default: current IST time)

    Returns:
        Timestamp string
    """
    if dt is None:
        dt = get_ist_now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")
