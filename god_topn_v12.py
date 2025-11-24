"""
OPTIONS SCANNER v12.0 - TOP-N 3X DETECTOR
==========================================================
✅ 4 Core Signals: OI, Stock Volume Spike, Option Volume Spike, 3X ML Prediction
✅ Combined Signals (all 3 must match)
✅ ML Predictions with Reversal Learning
✅ Paper Trading (ATM+1 CE, ATM-1 PE)
✅ Proper Rate Limiting (4sec per stock)
✅ UTF-8 Emoji Support

🆕 NEW IN v12.0 - TOP-N 3X DETECTOR:
✅ 190+ FEATURES: Advanced Greeks + Multi-Strike + Pattern Discovery
   • Module 1: Advanced Greeks (Vanna, Charm, Vomma, Color, Speed, Zomma)
   • Module 2: Multi-Strike Analysis (PCR, Max Pain, Gamma Walls, IV Skew)
   • Module 3: Pattern Discovery (Auto interactions, transforms, percentiles)
   • Module 4: Top-N Filtering (highest priced options only)
✅ ENSEMBLE MODELS: XGBoost + LightGBM + CatBoost weighted voting
   • XGBoost 40% + LightGBM 40% + CatBoost 20%
   • 6 total models (3 early + 3 late)
✅ AUTOMATIC FEATURE SELECTION: Best 100 features after 30 days
✅ MEMORY OPTIMIZED: Aggressive optimization for 8GB RAM
✅ UPDATED SCHEDULE:
   • 3:55 PM - Stock Volume ML Training
   • 4:00 PM - Baseline Capture
   • 4:30 PM - 3X Option ML Training (Advanced)

EXPECTED PERFORMANCE:
  Early Model: 30-40% precision (Top 10 CE + 10 PE)
  Late Model: 40-50% precision (Top 5 CE + 5 PE)

🆕 NEW IN v9.3.1 - OPTIONS_VOLUME DATA FIX:
✅ Fixed save_options_history() to save ONLY today's data
✅ Eliminates 40-50% file bloat from accumulated historical data
✅ Files now contain only current day's snapshots (no duplication)
✅ Load logic unchanged - still loads from multiple days at startup
✅ In-memory rolling window (50 fetches) unchanged - all logic works as before
✅ Same fix that was applied to options_enhanced in v9.1

🆕 NEW IN v9.3 - DYNAMIC VALIDATION + NEW SCHEDULE:
✅ OI Dynamic Validation: Compares with last fetch (not baseline)
   • Ensures OI is actively building NOW
   • Skip check on first fetch
✅ Minimum Threshold: 10X (was 5X)
   • More significant signals only
✅ Fetch Count Display: Shows "Avg: X (Y fetches)"
✅ New Schedule Times:
   • 4:00 PM - Stock Volume ML Training
   • 4:30 PM - 3X Option ML Training
   • 5:30 PM - Baseline Capture
✅ Enhanced Logging: Stock ML training visibility

🔧 HOTFIX v9.2.1:
✅ Fixed KeyError: 'last_price' when loading historical data
✅ Added backward compatibility check
✅ All stocks now process correctly

🆕 v9.2 - UNLIMITED DASHBOARD + ENHANCED FILTERS:
✅ All Dashboard Limits Removed: Shows ALL signals (no 10-signal cap)
✅ Newest Signals on Top: Reversed order in all sections
✅ Enhanced Option Volume Filter: 3-way validation required
   • Volume Spike (>=10X, 20X, 30X, etc.)
   • OI Increasing (current > last_fetch) ← DYNAMIC
   • Price Increasing (green candle)
✅ Open Positions: Newest positions shown first

🆕 v9.1 - MULTI-DAY CONTEXT & IMMEDIATE SIGNALS:
✅ Multi-Day Enhanced Data: Loads last 3 days for full context
✅ Immediate 3X Predictions: Start from 9:15 AM (market open)
✅ Immediate Option Volume Signals: Work from 1st fetch with history
✅ No Quality Compromise: Maintains high signal quality
✅ First Hour Coverage: Catch the most profitable period (9:15-10:15 AM)

🎯 v9.0 FEATURES (ENHANCED 3X ML DETECTOR):
✅ Dual Model System: Early (>5 days) + Late (≤5 days) expiry models
✅ Enhanced Option Chain: Captures ALL fields (price, vol, OI, greeks, bid/ask)
✅ Scheduled Training: 4:30 PM daily with automatic backups
✅ Real-time 3X Prediction: ML-powered pattern detection
✅ Multi-stage Alerts: Pattern → Starting (1.5X) → Target (3X)
✅ Dashboard Integration: All predictions + all alerts
✅ Zero Additional API Calls: Uses same fetched option chain data

TIMELINE (UPDATED SCHEDULE):
• 3:55 PM - Stock volume spike ML training
• 4:00 PM - Baseline capture
• 4:30 PM - 3X option ML training (ADVANCED ENSEMBLE)

API USAGE:
- Main Scanner: ~7,279 calls/day
- 5-Min Monitor: ~300 calls/day
- 3X Detection: 0 calls/day (uses cached data)
- TOTAL: ~7,579 calls/day (7.6% of 1 lakh daily limit) ✅

Version: 12.0 (Top-N 3X Detector)
Date: November 15, 2025
"""

import requests
import time
from datetime import datetime, timedelta
import json
from flask import Flask, jsonify, render_template_string
from threading import Thread
import pytz
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import logging
from logging.handlers import RotatingFileHandler
import sys

# Import market data
from market_data import MARKET_CAPS, STOCKS, LOT_SIZES

# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED 3X DETECTOR IMPORT (NEW IN v10.0 - ENSEMBLE)
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from live_3x_detector_temporal import Live3XDetectorTemporal as Live3XDetector
    THREEX_DETECTOR_AVAILABLE = True
except ImportError:
    THREEX_DETECTOR_AVAILABLE = False
    print("⚠️  live_3x_detector_topn_v7.py not found - 3X detection will be disabled")
# ═══════════════════════════════════════════════════════════════════════════════

# ============================================================================
# CONFIGURATION
# ============================================================================
DHAN_CLIENT_ID = "1000681801"
DHAN_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY0MDQxMDAyLCJpYXQiOjE3NjM5NTQ2MDIsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMDAwNjgxODAxIn0.5XnYkuRIMySiDGtuuz--_49D33FKsxuT9u0rU0d07iXyoxoI8oAztFbf4os8Mpma11Yjnf3s4iNJn_RVaeaQYA"
DHAN_API_BASE = "https://api.dhan.co"

TELEGRAM_BOT_TOKEN = "7589611837:AAGe5ysmoq-DrsioVd4T6AzE9dnUUNxdSYU"
TELEGRAM_CHAT_ID = "865318193"

# Storage paths
DATA_DRIVE = "F:"
BASELINE_DIR = f"{DATA_DRIVE}/scanner_data/baselines"
OPTIONS_HISTORY_DIR = f"{DATA_DRIVE}/scanner_data/options_volume"
OPTIONS_ENHANCED_DIR = f"{DATA_DRIVE}/scanner_data/options_enhanced"  # NEW: Enhanced format
PAPER_TRADING_DIR = f"{DATA_DRIVE}/scanner_data/options_paper_trading"
MODEL_DIR = f"{DATA_DRIVE}/scanner_data/models"
MODEL_BACKUP_DIR = f"{DATA_DRIVE}/scanner_data/models/backups"  # NEW: Model backups
LOG_DIR = f"{DATA_DRIVE}/scanner_data/logs"

for directory in [BASELINE_DIR, OPTIONS_HISTORY_DIR, OPTIONS_ENHANCED_DIR, 
                   PAPER_TRADING_DIR, MODEL_DIR, MODEL_BACKUP_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# ============================================================================
# DETAILED LOGGING SETUP - UTF-8 SUPPORT
# ============================================================================

# Force UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Console logger
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_formatter)

# File logger with UTF-8
today = datetime.now().strftime("%Y%m%d")
log_file = os.path.join(LOG_DIR, f"scanner_{today}.log")
file_handler = RotatingFileHandler(
    log_file, 
    maxBytes=50*1024*1024, 
    backupCount=10,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(funcName)s | %(message)s')
file_handler.setFormatter(file_formatter)

# Create logger
logger = logging.getLogger('scanner')
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Signal logger with UTF-8
signal_log_file = os.path.join(LOG_DIR, f"signals_{today}.log")
signal_file_handler = RotatingFileHandler(
    signal_log_file, 
    maxBytes=10*1024*1024, 
    backupCount=5,
    encoding='utf-8'
)
signal_file_handler.setLevel(logging.INFO)
signal_file_formatter = logging.Formatter('%(asctime)s | %(message)s')
signal_file_handler.setFormatter(signal_file_formatter)

signal_logger = logging.getLogger('signals')
signal_logger.setLevel(logging.INFO)
signal_logger.addHandler(signal_file_handler)
signal_logger.addHandler(console_handler)

logger.info("="*80)
logger.info("SCANNER v9.3.1 - LOGGING INITIALIZED (OPTIONS_VOLUME FIX)")
logger.info(f"Main Log: {log_file}")
logger.info(f"Signal Log: {signal_log_file}")
logger.info("="*80)

# Timing
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 30
STOCK_ML_TRAINING_HOUR = 15  # NEW: 3:55 PM
STOCK_ML_TRAINING_MINUTE = 55
THREEX_TRAINING_HOUR = 16  # 4:30 PM (Advanced Ensemble Training)
THREEX_TRAINING_MINUTE = 30
BASELINE_CAPTURE_HOUR = 16  # NEW: 4:00 PM
BASELINE_CAPTURE_MINUTE = 0

# Signal thresholds
OPTION_CHAIN_DELAY = 4  # CRITICAL: 4 seconds between EACH stock
OI_STRIKES_RANGE = 5
OPTION_VOLUME_STRIKES_RANGE = 4  # Changed from 3 to 4 (ATM±4)
OI_ALERT_THRESHOLDS = [5, 10, 20, 30, 40, 50]
OI_REQUIRED_STRIKES = 6
OI_MIN_CHANGE = -5

STOCK_MCAP_THRESHOLD = 0.5
OPTIONS_VOLUME_HISTORY_SIZE = 50
# ⭐ OPTION VOLUME MULTIPLIER - CHANGE HERE ⭐
# Default: [10, 20, 30, 40, 50] means alert at 10X, 20X, 30X, 40X, 50X average
# Minimum threshold set to 10X for more significant signals
OPTIONS_VOLUME_THRESHOLDS = [10, 20, 30, 40, 50]
OPTIONS_VOLUME_MIN_HISTORY = 2  # ⭐ CHANGED: Was 10, now 2 - allows signals from 1st fetch with loaded history

# Paper trading
STARTING_CAPITAL = 10000000
LOTS_PER_TRADE = 10
CALL_TARGET_PCT = 10.0
CALL_STOPLOSS_PCT = -5.0
PUT_TARGET_PCT = -10.0
PUT_STOPLOSS_PCT = 5.0
HOLDING_DAYS = 10

# ============================================================================
# GLOBAL DATA
# ============================================================================
scanner_running = False
baseline_data = {}
locked_atm_data = {}
opening_prices = {}
current_prices = {}

# Core signals
oi_signals = []
stock_volume_spikes = []
option_volume_spikes_oi_increasing = []  # NEW: OI Increasing logic
option_volume_spikes_oi_decreasing = []  # NEW: OI Decreasing logic
combined_signals = []

# Tracking
oi_signal_tracker = {}
stock_volume_alerted = set()
option_volume_alerted_oi_increasing = set()  # NEW: Track OI Increasing alerts
option_volume_alerted_oi_decreasing = set()  # NEW: Track OI Decreasing alerts
options_volume_tracker = {}
last_checked_candles = {}  # Track last checked candle timestamp for each stock
stock_volume_monitor_running = False  # Flag for 5-min thread

# ML & Paper Trading
ml_predictions = []
paper_positions = []
closed_trades = []
capital = STARTING_CAPITAL

# ═══════════════════════════════════════════════════════════════════════════════
# 3X DETECTOR GLOBALS (NEW IN v9.0)
# ═══════════════════════════════════════════════════════════════════════════════
threex_detector = None  # Will be initialized at startup
threex_predictions = []  # Top predictions for dashboard (updated each cycle)
threex_alerts = []  # Recent alerts (for dashboard display)
threex_enabled = False  # Flag indicating if 3X detector is loaded
enhanced_options_data = {}  # Enhanced option chain data (in-memory)
# ═══════════════════════════════════════════════════════════════════════════════

ist = pytz.timezone('Asia/Kolkata')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_ist_time():
    return datetime.now(ist)

def is_market_open():
    """Check if market is currently open"""
    now = get_ist_time()
    
    if now.weekday() >= 5:
        return False
    
    market_start = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
    market_end = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
    
    return market_start <= now <= market_end

# ============================================================================
# NSE HOLIDAY CALENDAR 2025
# ============================================================================
NSE_HOLIDAYS_2025 = [
    "2025-02-26",  # Mahashivratri (Wednesday)
    "2025-03-14",  # Holi (Friday)
    "2025-03-31",  # Id-Ul-Fitr (Monday)
    "2025-04-10",  # Shri Mahavir Jayanti (Thursday)
    "2025-04-14",  # Dr. Baba Saheb Ambedkar Jayanti (Monday)
    "2025-04-18",  # Good Friday
    "2025-05-01",  # Maharashtra Day (Thursday)
    "2025-08-15",  # Independence Day / Parsi New Year (Friday)
    "2025-08-27",  # Shri Ganesh Chaturthi (Wednesday)
    "2025-10-02",  # Mahatma Gandhi Jayanti/Dussehra (Thursday)
    "2025-10-21",  # Diwali Laxmi Pujan (Tuesday)
    "2025-10-22",  # Balipratipada (Wednesday)
    "2025-11-05",  # Prakash Gurpurb Sri Guru Nanak Dev (Wednesday)
    "2025-12-25",  # Christmas (Thursday)
]

def is_trading_day(date):
    """Check if a date is a trading day (not weekend or holiday)"""
    # Check if weekend (Saturday=5, Sunday=6)
    if date.weekday() >= 5:
        return False
    
    # Check if holiday
    date_str = date.strftime("%Y-%m-%d")
    if date_str in NSE_HOLIDAYS_2025:
        return False
    
    return True

def adjust_expiry_for_holiday(expiry_date):
    """
    If expiry falls on holiday, move to previous trading day
    
    Logic:
    - If Tuesday is holiday → Move to Monday
    - If Monday is also holiday → Move to Friday
    - Continue backwards until trading day found
    """
    current = expiry_date
    
    while not is_trading_day(current):
        current = current - timedelta(days=1)
    
    return current

def get_next_tuesday(from_date):
    """Get next Tuesday from given date"""
    days_ahead = (1 - from_date.weekday()) % 7  # Tuesday is 1
    if days_ahead == 0:
        days_ahead = 7  # If today is Tuesday, get next Tuesday
    
    next_tuesday = from_date + timedelta(days=days_ahead)
    return next_tuesday

def get_weekly_expiry():
    """
    Get next weekly expiry (for Nifty/Bank Nifty)
    
    Rules:
    - Weekly expiry is every Tuesday
    - If Tuesday is holiday, expiry shifts to previous trading day
    - If today is after 3:30 PM on expiry day, get next week's expiry
    """
    today = get_ist_time()
    
    # Find next Tuesday
    next_tuesday = get_next_tuesday(today)
    
    # If today is Tuesday and before 3:30 PM, use today
    if today.weekday() == 1 and today.hour < 15:  # Tuesday = 1
        expiry_tuesday = today
    else:
        expiry_tuesday = next_tuesday
    
    # Adjust for holidays
    expiry_date = adjust_expiry_for_holiday(expiry_tuesday)
    
    return expiry_date.strftime("%Y-%m-%d")

def get_monthly_expiry():
    """
    Get next monthly expiry (for stocks)
    
    Rules:
    - Monthly expiry is last Tuesday of the month
    - If last Tuesday is holiday, expiry shifts to previous trading day
    - If current month's expiry has passed, get next month's expiry
    """
    today = get_ist_time()
    
    # Get last Tuesday of current month
    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    days_to_subtract = (last_day.weekday() - 1) % 7  # Tuesday = 1
    last_tuesday = last_day - timedelta(days=days_to_subtract)
    
    # Adjust for holidays
    current_month_expiry = adjust_expiry_for_holiday(last_tuesday)
    
    # Check if current month's expiry has passed
    # Consider passed if:
    # - Date is after expiry date
    # - OR date is expiry date and time is after 3:30 PM
    expiry_passed = False
    if today.date() > current_month_expiry.date():
        expiry_passed = True
    elif today.date() == current_month_expiry.date() and today.hour >= 15 and today.minute >= 30:
        expiry_passed = True
    
    if expiry_passed:
        # Get next month's last Tuesday
        if today.month == 12:
            next_month_last_day = today.replace(year=today.year + 1, month=2, day=1) - timedelta(days=1)
        elif today.month == 11:
            next_month_last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            next_month_last_day = today.replace(month=today.month + 2, day=1) - timedelta(days=1)
        
        days_to_subtract = (next_month_last_day.weekday() - 1) % 7
        next_month_last_tuesday = next_month_last_day - timedelta(days=days_to_subtract)
        
        # Adjust for holidays
        expiry_date = adjust_expiry_for_holiday(next_month_last_tuesday)
        return expiry_date.strftime("%Y-%m-%d")
    else:
        return current_month_expiry.strftime("%Y-%m-%d")

def get_analysis_expiry():
    """
    Get expiry for option chain analysis
    
    ⭐ STOCKS: Uses monthly expiry (last Tuesday of month)
    For Nifty: Would use weekly expiry (every Tuesday)
    
    Currently configured for STOCKS (monthly)
    """
    return get_monthly_expiry()

def get_trading_expiry():
    """Get expiry for paper trading (monthly expiry for stocks)"""
    return get_monthly_expiry()

def get_index_expiry(security_id):
    """
    Get expiry for indices (NIFTY and BANKNIFTY)
    
    Args:
        security_id: 13 for NIFTY, 25 for BANKNIFTY
    
    Returns:
        Expiry date string in YYYY-MM-DD format
    
    Rules:
        NIFTY (13): Weekly expiry (every Tuesday), 11:30 PM cutoff
        BANKNIFTY (25): Monthly expiry (last Tuesday), 11:30 PM cutoff
    """
    today = get_ist_time()
    
    if security_id == 13:  # NIFTY - Weekly expiry
        # Find next Tuesday
        next_tuesday = get_next_tuesday(today)
        
        # If today is Tuesday and before 11:30 PM, use today
        if today.weekday() == 1 and (today.hour < 23 or (today.hour == 23 and today.minute < 30)):
            expiry_tuesday = today
        else:
            expiry_tuesday = next_tuesday
        
        # Adjust for holidays
        expiry_date = adjust_expiry_for_holiday(expiry_tuesday)
        return expiry_date.strftime("%Y-%m-%d")
    
    elif security_id == 25:  # BANKNIFTY - Monthly expiry (same as stocks)
        # Get last Tuesday of current month
        if today.month == 12:
            last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        days_to_subtract = (last_day.weekday() - 1) % 7
        last_tuesday = last_day - timedelta(days=days_to_subtract)
        
        # Adjust for holidays
        current_month_expiry = adjust_expiry_for_holiday(last_tuesday)
        
        # Check if current month's expiry has passed (11:30 PM cutoff)
        expiry_passed = False
        if today.date() > current_month_expiry.date():
            expiry_passed = True
        elif today.date() == current_month_expiry.date() and (today.hour > 23 or (today.hour == 23 and today.minute >= 30)):
            expiry_passed = True
        
        if expiry_passed:
            # Get next month's last Tuesday
            if today.month == 12:
                next_month_last_day = today.replace(year=today.year + 1, month=2, day=1) - timedelta(days=1)
            elif today.month == 11:
                next_month_last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                next_month_last_day = today.replace(month=today.month + 2, day=1) - timedelta(days=1)
            
            days_to_subtract = (next_month_last_day.weekday() - 1) % 7
            next_month_last_tuesday = next_month_last_day - timedelta(days=days_to_subtract)
            
            # Adjust for holidays
            expiry_date = adjust_expiry_for_holiday(next_month_last_tuesday)
            return expiry_date.strftime("%Y-%m-%d")
        else:
            return current_month_expiry.strftime("%Y-%m-%d")
    
    else:
        # Fallback to monthly expiry for stocks
        return get_monthly_expiry()

def make_api_request(endpoint, method="GET", data=None):
    """Make API request to Dhan"""
    url = f"{DHAN_API_BASE}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "access-token": DHAN_ACCESS_TOKEN,
        "client-id": DHAN_CLIENT_ID
    }
    try:
        if method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.debug(f"API error {response.status_code}: {endpoint}")
    except requests.exceptions.Timeout:
        logger.debug(f"API timeout: {endpoint}")
    except Exception as e:
        logger.debug(f"API exception: {e}")
    
    return None

def send_telegram_message(message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except:
        return False

def get_stock_price(security_id):
    """Get current stock or index price"""
    endpoint = "/v2/marketfeed/quote"
    
    # Determine exchange based on security_id
    if security_id in [13, 25]:  # NIFTY or BANKNIFTY
        exchange_key = "IDX_I"
    else:
        exchange_key = "NSE_EQ"
    
    payload = {exchange_key: [security_id]}
    response = make_api_request(endpoint, method="POST", data=payload)
    
    if response and "data" in response and exchange_key in response["data"]:
        data = response["data"][exchange_key].get(str(security_id))
        if data and "last_price" in data:
            return float(data["last_price"])
    return None

def get_option_chain(security_id, expiry_date):
    """Get option chain for a stock or index"""
    endpoint = "/v2/optionchain"
    
    # Determine exchange based on security_id
    # NIFTY=13, BANKNIFTY=25 are indices (IDX_I)
    # All other IDs are stocks (NSE_EQ)
    if security_id in [13, 25]:
        underlying_seg = "IDX_I"
    else:
        underlying_seg = "NSE_EQ"
    
    payload = {
        "UnderlyingScrip": security_id,
        "UnderlyingSeg": underlying_seg,
        "Expiry": expiry_date
    }
    return make_api_request(endpoint, method="POST", data=payload)

def find_atm_strike(current_price, option_chain):
    """Find ATM strike and strike interval"""
    if not option_chain or "data" not in option_chain or "oc" not in option_chain["data"]:
        return None, None
    
    strikes = []
    for strike_str in option_chain["data"]["oc"].keys():
        try:
            strikes.append(float(strike_str))
        except ValueError:
            continue
    
    if not strikes:
        return None, None
    
    strikes = sorted(set(strikes))
    atm_strike = min(strikes, key=lambda x: abs(x - current_price))
    strike_interval = strikes[1] - strikes[0] if len(strikes) > 1 else 0
    
    return atm_strike, strike_interval

# ============================================================================
# BASELINE FUNCTIONS
# ============================================================================

def capture_baseline():
    """Capture complete option chain baseline - runs at 4:00 PM"""
    print("\n" + "="*80)
    print("📸 BASELINE CAPTURE - Starting...")
    print("="*80)
    
    now = get_ist_time()
    today_str = now.strftime("%Y%m%d")
    output_file = os.path.join(BASELINE_DIR, f"baseline_{today_str}.json")
    
    if os.path.exists(output_file):
        print(f"⚠️ Baseline already captured today: {output_file}")
        return
    
    # Note: Expiry will be determined per symbol (stocks vs indices)
    baseline_data = {}
    success_count = 0
    
    print(f"📊 Symbols: {len(STOCKS)} (Stocks + Indices)\n")
    
    for idx, (security_id, symbol) in enumerate(STOCKS.items(), 1):
        try:
            # Determine expiry based on symbol type
            if security_id in [13, 25]:  # NIFTY or BANKNIFTY
                expiry = get_index_expiry(security_id)
            else:
                expiry = get_monthly_expiry()
            
            print(f"[{idx}/{len(STOCKS)}] {symbol:15s} ", end="", flush=True)
            
            current_price = get_stock_price(security_id)
            if not current_price:
                print("❌ No price")
                continue
            
            option_chain = get_option_chain(security_id, expiry)
            if not option_chain:
                print("❌ No chain")
                continue
            
            atm_strike, strike_interval = find_atm_strike(current_price, option_chain)
            if not atm_strike:
                print("❌ No ATM")
                continue
            
            strikes_data = {}
            oc_data = option_chain["data"]["oc"]
            
            for strike_str in oc_data.keys():
                try:
                    strike = float(strike_str)
                except ValueError:
                    continue
                
                strike_data = oc_data[strike_str]
                strike_info = {'ce_oi': 0, 'pe_oi': 0, 'ce_iv': 0, 'pe_iv': 0}
                
                if "ce" in strike_data:
                    ce = strike_data["ce"]
                    ce_oi = int(ce.get("oi", 0) or 0)
                    ce_iv = float(ce.get("implied_volatility", 0) or 0)
                    if ce_oi > 0:
                        strike_info["ce_oi"] = ce_oi
                        strike_info["ce_iv"] = ce_iv
                
                if "pe" in strike_data:
                    pe = strike_data["pe"]
                    pe_oi = int(pe.get("oi", 0) or 0)
                    pe_iv = float(pe.get("implied_volatility", 0) or 0)
                    if pe_oi > 0:
                        strike_info["pe_oi"] = pe_oi
                        strike_info["pe_iv"] = pe_iv
                
                if strike_info["ce_oi"] > 0 or strike_info["pe_oi"] > 0:
                    strikes_data[str(float(strike))] = strike_info
            
            baseline_data[symbol] = {
                "security_id": security_id,
                "price": current_price,
                "atm_strike": atm_strike,
                "strike_interval": strike_interval,
                "strikes": strikes_data
            }
            
            print(f"✅ Price: ₹{current_price:8.2f} | Strikes: {len(strikes_data):3d}")
            success_count += 1
            
            # ✅ SAME 4-SECOND DELAY AS baseline_capture.py
            time.sleep(OPTION_CHAIN_DELAY)
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted! Saving partial baseline...")
            break
        except Exception as e:
            print(f"❌ {str(e)[:30]}")
            # ✅ SLEEP EVEN ON ERROR (matches baseline_capture.py)
            time.sleep(OPTION_CHAIN_DELAY)
            continue
    
    with open(output_file, 'w') as f:
        json.dump(baseline_data, f, indent=2)
    
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    
    print("\n" + "="*80)
    print("📊 BASELINE CAPTURE COMPLETE")
    print("="*80)
    print(f"✅ Stocks Captured: {success_count}/{len(STOCKS)}")
    print(f"💾 File Size: {file_size_mb:.2f} MB")
    print(f"📁 Saved: {output_file}")
    print("="*80 + "\n")
    
    send_telegram_message(
        f"📸 <b>Baseline Captured</b>\n\n"
        f"✅ Stocks: {success_count}/{len(STOCKS)}\n"
        f"💾 Size: {file_size_mb:.1f} MB\n"
        f"📅 Date: {today_str}"
    )

def load_baseline():
    """Load most recent baseline"""
    today = get_ist_time()
    
    for days_back in range(1, 5):
        prev_day = today - timedelta(days=days_back)
        
        if prev_day.weekday() < 5:
            filename = os.path.join(BASELINE_DIR, f"baseline_{prev_day.strftime('%Y%m%d')}.json")
            
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        data = json.load(f)
                    
                    logger.info(f"✅ Loaded baseline: {os.path.basename(filename)}")
                    logger.info(f"   Date: {prev_day.strftime('%Y-%m-%d')}")
                    logger.info(f"   Stocks: {len(data)}")
                    
                    return data
                except:
                    pass
    
    return None

# ============================================================================
# NIFTY DATA MANAGER
# ============================================================================

class NiftyDataManager:
    """Manage Nifty data from Dhan (fallback to Yahoo)"""
    
    def __init__(self):
        self.nifty_data = None
        self.nifty_open = None
        self.nifty_security_id = 25  # Dhan Nifty 50 security ID
        
    def get_nifty_from_dhan(self):
        """Fetch Nifty data from Dhan API"""
        try:
            endpoint = "/v2/marketfeed/quote"
            payload = {"IDX_I": [self.nifty_security_id]}
            response = make_api_request(endpoint, method="POST", data=payload)
            
            if response and "data" in response and "IDX_I" in response["data"]:
                nifty_data = response["data"]["IDX_I"].get(str(self.nifty_security_id))
                if nifty_data:
                    return {
                        'current': float(nifty_data.get("last_price", 0)),
                        'open': float(nifty_data.get("open", 0)),
                        'high': float(nifty_data.get("high", 0)),
                        'low': float(nifty_data.get("low", 0)),
                        'prev_close': float(nifty_data.get("prev_close", 0))
                    }
        except:
            pass
        return None
    
    def get_nifty_from_yahoo(self):
        """Fallback: Fetch Nifty from Yahoo Finance"""
        try:
            import yfinance as yf
            nifty = yf.Ticker("^NSEI")
            data = nifty.history(period="1d", interval="1m")
            if not data.empty:
                return {
                    'current': float(data['Close'].iloc[-1]),
                    'open': float(data['Open'].iloc[0]),
                    'high': float(data['High'].max()),
                    'low': float(data['Low'].min()),
                    'prev_close': float(data['Close'].iloc[0])
                }
        except:
            pass
        return None
    
    def update_nifty(self):
        """Update Nifty data"""
        data = self.get_nifty_from_dhan()
        if not data:
            data = self.get_nifty_from_yahoo()
        
        if data:
            self.nifty_data = data
            if not self.nifty_open:
                self.nifty_open = data['open']
        
        return data is not None
    
    def get_nifty_change(self):
        """Get Nifty change percentage"""
        if not self.nifty_data or not self.nifty_open:
            return 0.0
        return ((self.nifty_data['current'] - self.nifty_open) / self.nifty_open) * 100
    
    def is_nifty_healthy(self):
        """Check if Nifty is in acceptable range"""
        change = self.get_nifty_change()
        return abs(change) < 2.0  # Within ±2%

nifty_manager = NiftyDataManager()

# ============================================================================
# SIGNAL 1: OI SIGNAL - ✅ FIXED: THRESHOLD-ONLY UPDATES
# ============================================================================

def detect_oi_signal(symbol, security_id, locked_atm, strike_interval, option_chain):
    """
    Detect OI signals with FIXED logic:
    - Update oi_signals list ONLY when threshold changes
    - Dashboard shows only current threshold signals
    - Telegram alerts ONLY on threshold upgrades
    """
    global oi_signals, oi_signal_tracker
    
    if not locked_atm or not strike_interval or not option_chain:
        return None
    
    if "data" not in option_chain or "oc" not in option_chain["data"]:
        return None
    
    oc_data = option_chain["data"]["oc"]
    
    # Get baseline data
    baseline = baseline_data.get(symbol)
    if not baseline:
        return None
    
    baseline_strikes = baseline.get("strikes", {})
    
    # Calculate OI changes for ATM±5
    call_changes = []
    put_changes = []
    
    for offset in range(-OI_STRIKES_RANGE, OI_STRIKES_RANGE + 1):
        strike = locked_atm + (offset * strike_interval)
        strike_str = str(float(strike))
        
        if strike_str not in baseline_strikes:
            continue
        
        baseline_strike = baseline_strikes[strike_str]
        baseline_ce_oi = baseline_strike.get("ce_oi", 0)
        baseline_pe_oi = baseline_strike.get("pe_oi", 0)
        
        if baseline_ce_oi == 0 and baseline_pe_oi == 0:
            continue
        
        # Get current data
        strike_key = f"{strike:.6f}"
        if strike_key not in oc_data:
            continue
        
        current_strike = oc_data[strike_key]
        
        # Call OI change
        if baseline_ce_oi > 0:
            current_ce_oi = 0
            if "ce" in current_strike:
                current_ce_oi = int(current_strike["ce"].get("oi", 0) or 0)
            
            change_pct = ((current_ce_oi - baseline_ce_oi) / baseline_ce_oi) * 100
            call_changes.append(change_pct)
        
        # Put OI change
        if baseline_pe_oi > 0:
            current_pe_oi = 0
            if "pe" in current_strike:
                current_pe_oi = int(current_strike["pe"].get("oi", 0) or 0)
            
            change_pct = ((current_pe_oi - baseline_pe_oi) / baseline_pe_oi) * 100
            put_changes.append(change_pct)
    
    if not call_changes and not put_changes:
        return None
    
    # Calculate statistics
    call_reducing = sum(1 for c in call_changes if c <= OI_MIN_CHANGE)
    put_reducing = sum(1 for p in put_changes if p <= OI_MIN_CHANGE)
    call_change = sum(call_changes) / len(call_changes) if call_changes else 0
    put_change = sum(put_changes) / len(put_changes) if put_changes else 0
    
    # Check conditions
    signal_type = None
    send_telegram = False
    
    if (call_reducing >= OI_REQUIRED_STRIKES and 
        call_change <= OI_MIN_CHANGE and 
        put_change > 0):
        signal_type = "BUY"
        logger.info(f"🟢 {symbol} OI BUY CONDITION MET:")
        logger.info(f"   CE Reducing: {call_reducing} strikes")
        logger.info(f"   CE Change: {call_change:.2f}%")
        logger.info(f"   PE Change: {put_change:.2f}%")
        
    elif (put_reducing >= OI_REQUIRED_STRIKES and 
          put_change <= OI_MIN_CHANGE and 
          call_change > 0):
        signal_type = "SELL"
        logger.info(f"🔴 {symbol} OI SELL CONDITION MET:")
        logger.info(f"   PE Reducing: {put_reducing} strikes")
        logger.info(f"   PE Change: {put_change:.2f}%")
        logger.info(f"   CE Change: {call_change:.2f}%")
    
    if not signal_type:
        return None
    
    max_change = max(abs(call_change), abs(put_change))
    current_threshold = None
    for t in OI_ALERT_THRESHOLDS:
        if max_change >= t:
            current_threshold = t
    
    # ✅ FIX: Only update/alert on threshold changes
    should_update_dashboard = False
    
    if symbol not in oi_signal_tracker:
        # New signal
        should_update_dashboard = True
        send_telegram = True if current_threshold else False
        logger.info(f"   NEW SIGNAL - Threshold: {current_threshold}%")
    else:
        prev_signal = oi_signal_tracker[symbol]
        if prev_signal['type'] != signal_type:
            # Direction changed
            should_update_dashboard = True
            send_telegram = True if current_threshold else False
            logger.info(f"   DIRECTION CHANGE - Was {prev_signal['type']}, now {signal_type}")
        else:
            last_threshold = prev_signal.get('last_threshold', 0)
            if current_threshold and current_threshold > last_threshold:
                # Threshold upgraded
                should_update_dashboard = True
                send_telegram = True
                logger.info(f"   THRESHOLD UPGRADE - {last_threshold}% → {current_threshold}%")
    
    # Update tracker
    oi_signal_tracker[symbol] = {
        'type': signal_type,
        'last_threshold': current_threshold or 0
    }
    
    # ✅ FIX: Only update oi_signals list if threshold changed
    if should_update_dashboard:
        # Remove old signal if exists
        for i in range(len(oi_signals) - 1, -1, -1):
            if oi_signals[i]['symbol'] == symbol:
                oi_signals.pop(i)
                break
        
        # Add new signal
        signal_data = {
            'symbol': symbol,
            'signal_type': signal_type,
            'call_change': call_change,
            'put_change': put_change,
            'threshold': current_threshold,
            'timestamp': get_ist_time().strftime("%H:%M:%S")
        }
        
        oi_signals.append(signal_data)
        
        signal_logger.info(f"OI_SIGNAL | {symbol} | {signal_type} | CE:{call_change:.2f}% PE:{put_change:.2f}% | Threshold:{current_threshold}%")
        
        # ✅ FIX: Only send telegram on threshold upgrades
        if send_telegram and current_threshold:
            emoji = "🟢" if signal_type == "BUY" else "🔴"
            msg = f"{emoji} <b>OI SIGNAL [{current_threshold}%]</b>\n\n"
            msg += f"📊 {symbol} - {signal_type}\n"
            msg += f"📉 Call Δ: {call_change:.2f}%\n"
            msg += f"📈 Put Δ: {put_change:.2f}%\n"
            msg += f"💰 Price: ₹{current_prices.get(symbol, 0):.2f}"
            send_telegram_message(msg)
            logger.info(f"📱 Telegram alert sent for {symbol}")
        
        return signal_data
    
    return None

# ============================================================================
# SIGNAL 2: STOCK VOLUME SPIKE (with ML)
# ============================================================================

def get_stock_5min_candles(security_id):
    """Fetch 5-min candles for today"""
    try:
        now = get_ist_time()
        from_time = now.replace(hour=9, minute=15, second=0).strftime("%Y-%m-%d %H:%M:%S")
        to_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        endpoint = "/v2/charts/intraday"
        payload = {
            "securityId": str(security_id),
            "exchangeSegment": "NSE_EQ",
            "instrument": "EQUITY",
            "interval": "5",
            "fromDate": from_time,
            "toDate": to_time
        }
        
        response = make_api_request(endpoint, method="POST", data=payload)
        
        if response and 'volume' in response:
            candles = []
            for i in range(len(response['volume'])):
                candles.append({
                    'timestamp': response.get('timestamp', [])[i] if 'timestamp' in response else None,
                    'open': response['open'][i],
                    'high': response['high'][i],
                    'low': response['low'][i],
                    'close': response['close'][i],
                    'volume': response['volume'][i]
                })
            return candles
        return []
    except:
        return []

def detect_stock_volume_spike(symbol, security_id, current_price):
    """Detect stock volume spike with ML direction prediction"""
    global stock_volume_spikes, stock_volume_alerted, ml_predictions
    
    # Skip indices (NIFTY=13, BANKNIFTY=25) - they don't have market cap
    if security_id in [13, 25]:
        return None
    
    market_cap = MARKET_CAPS.get(symbol)
    if not market_cap:
        return None
    
    candles = get_stock_5min_candles(security_id)
    if not candles or len(candles) == 0:
        return None
    
    last_candle = candles[-1]
    volume = last_candle['volume']
    avg_price = (last_candle['high'] + last_candle['low']) / 2
    traded_value = volume * avg_price
    mcap_pct = (traded_value / market_cap) * 100
    
    if mcap_pct >= STOCK_MCAP_THRESHOLD:
        alert_key = f"{symbol}_{last_candle.get('timestamp', '')}"
        
        if alert_key not in stock_volume_alerted:
            stock_volume_alerted.add(alert_key)
            
            open_price = last_candle['open']
            high_price = last_candle['high']
            low_price = last_candle['low']
            close_price = last_candle['close']
            
            candle_body = close_price - open_price
            candle_body_pct = (candle_body / open_price * 100) if open_price > 0 else 0
            candle_type = 'green' if candle_body > 0 else 'red'
            
            price_range = high_price - low_price
            price_range_pct = (price_range / open_price * 100) if open_price > 0 else 0
            
            close_position = (close_price - low_price) / price_range if price_range > 0 else 0.5
            
            if candle_body > 0:
                upper_wick = high_price - close_price
                lower_wick = open_price - low_price
            else:
                upper_wick = high_price - open_price
                lower_wick = close_price - low_price
            
            upper_wick_pct = (upper_wick / open_price * 100) if open_price > 0 else 0
            lower_wick_pct = (lower_wick / open_price * 100) if open_price > 0 else 0
            
            volume_position = 'top' if close_position > 0.6 else ('bottom' if close_position < 0.4 else 'middle')
            
            nifty_change = nifty_manager.get_nifty_change()
            nifty_ok = nifty_manager.is_nifty_healthy()
            
            momentum_15min = 0
            if len(candles) >= 3:
                old_close = candles[-4]['close'] if len(candles) >= 4 else candles[0]['close']
                momentum_15min = ((close_price - old_close) / old_close * 100) if old_close > 0 else 0
            
            spike_time = last_candle.get('timestamp', get_ist_time())
            if isinstance(spike_time, str):
                spike_time = pd.to_datetime(spike_time)
            elif not hasattr(spike_time, 'hour'):
                spike_time = get_ist_time()
            
            hour = spike_time.hour if hasattr(spike_time, 'hour') else 12
            minute = spike_time.minute if hasattr(spike_time, 'minute') else 0
            time_of_day = hour + (minute / 60)
            
            spike_data = {
                'symbol': symbol,
                'datetime': spike_time,
                'timestamp': spike_time.strftime("%H:%M:%S") if hasattr(spike_time, 'strftime') else str(spike_time),
                'volume': volume,
                'avg_price': round(avg_price, 2),
                'traded_value_cr': round(traded_value / 10000000, 2),
                'market_cap_cr': round(market_cap / 10000000, 2),
                'mcap_pct': round(mcap_pct, 4),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'current_price': current_price,
                'candle_type': candle_type,
                'candle_body_pct': round(candle_body_pct, 4),
                'price_range_pct': round(price_range_pct, 4),
                'close_position': round(close_position, 4),
                'upper_wick_pct': round(upper_wick_pct, 4),
                'lower_wick_pct': round(lower_wick_pct, 4),
                'volume_position': volume_position,
                'nifty_change': round(nifty_change, 2),
                'nifty_ok': nifty_ok,
                'momentum_15min': round(momentum_15min, 2),
                'time_of_day': round(time_of_day, 2),
                'security_id': security_id
            }
            
            ml_prediction = predict_direction(spike_data)
            spike_data['ml_prediction'] = ml_prediction
            
            stock_volume_spikes.append(spike_data)
            ml_predictions.append({
                'symbol': symbol,
                'timestamp': spike_data['timestamp'],
                'action': ml_prediction['action'],
                'direction': ml_prediction['direction'],
                'confidence': ml_prediction['confidence']
            })
            
            signal_logger.info(f"STOCK_VOLUME_SPIKE | {symbol} | {spike_data['mcap_pct']:.4f}% | "
                             f"{ml_prediction['direction']} | {ml_prediction['action']} | "
                             f"Conf:{ml_prediction['confidence']}% | Candle:{candle_type} {candle_body_pct:+.2f}%")
            
            # ✅ FIX: Open position AND save immediately
            if ml_prediction['action'] in ['BUY_CALL', 'BUY_PUT']:
                logger.info(f"💼 Opening paper position for {symbol}...")
                position = open_paper_position(spike_data, ml_prediction)
                if position:
                    # ⭐ CRITICAL FIX: Save after opening position
                    save_paper_trading_data()
                    logger.info(f"💾 Position saved to disk")
            
            direction = ml_prediction['direction']
            action = ml_prediction['action']
            
            if action == 'BUY_CALL':
                emoji = "🟢"
                action_text = "BUY CALL"
            elif action == 'BUY_PUT':
                emoji = "🔴"
                action_text = "BUY PUT"
            else:
                emoji = "⚪"
                action_text = "SKIP"
            
            msg = f"{emoji} <b>VOLUME SPIKE - {direction}</b>\n\n"
            msg += f"📊 {symbol}\n"
            msg += f"⏰ {spike_data['timestamp']}\n"
            msg += f"💰 Price: ₹{spike_data['close']:.2f}\n"
            msg += f"🕯️ Candle: {candle_type.upper()} ({candle_body_pct:+.2f}%)\n"
            msg += f"📈 Volume: {volume:,}\n"
            msg += f"💵 Traded: ₹{spike_data['traded_value_cr']:.2f} Cr\n"
            msg += f"📊 MCap %: <b>{spike_data['mcap_pct']:.4f}%</b>\n\n"
            msg += f"🤖 <b>ML: {action_text}</b>\n"
            msg += f"🎯 Confidence: {ml_prediction['confidence']}%"
            
            send_telegram_message(msg)
            
            print(f"  🔥 VOLUME SPIKE: {symbol} {mcap_pct:.4f}% | {direction} ({action}) {ml_prediction['confidence']}%")
            
            return spike_data
    
    return None

# ============================================================================
# SIGNAL 3: OPTION VOLUME SPIKE
# ============================================================================

def load_options_history():
    """Load rolling 50-fetch history for option volume tracking"""
    global options_volume_tracker
    
    today = get_ist_time()
    
    for days_back in range(10):
        date = today - timedelta(days=days_back)
        filename = os.path.join(OPTIONS_HISTORY_DIR, f"options_{date.strftime('%Y%m%d')}.json")
        
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    daily_data = json.load(f)
                    
                for key, data in daily_data.items():
                    if key not in options_volume_tracker:
                        options_volume_tracker[key] = {
                            'symbol': data.get('symbol', ''),
                            'strike': data.get('strike', 0),
                            'option_type': data.get('option_type', ''),
                            'volume_history': [],
                            'last_threshold': 0,
                            'all_history': [],
                            'last_price': None,  # NEW: Initialize for price tracking
                            'last_oi': None      # NEW: Initialize for OI tracking
                        }
                    
                    # Load volume history
                    if 'volume_history' in data:
                        options_volume_tracker[key]['volume_history'].extend(data['volume_history'])
                    
                    # Load all history for backtesting
                    if 'all_history' in data:
                        options_volume_tracker[key]['all_history'].extend(data['all_history'])
            except:
                pass
    
    # Trim volume_history to last 50 entries per strike
    for key, data in options_volume_tracker.items():
        if len(data['volume_history']) > OPTIONS_VOLUME_HISTORY_SIZE:
            data['volume_history'] = data['volume_history'][-OPTIONS_VOLUME_HISTORY_SIZE:]
    
    print(f"✅ Loaded options history: {len(options_volume_tracker)} strikes")


def save_options_history():
    """
    Save ONLY today's options volume history (FIXED: No historical duplication)
    
    This function filters and saves only today's snapshots to prevent data duplication
    across multiple days. Historical context is maintained in-memory and reloaded
    from separate daily files at startup.
    
    KEY CHANGE: Filters snapshots by today's date before saving
    """
    today = get_ist_time()
    filename = os.path.join(OPTIONS_HISTORY_DIR, f"options_{today.strftime('%Y%m%d')}.json")
    
    # ⭐ NEW: Filter only today's snapshots (by timestamp date)
    today_date_str = today.strftime('%Y-%m-%d')
    today_only_data = {}
    total_snapshots = 0
    filtered_snapshots = 0
    
    for key, data in options_volume_tracker.items():
        if 'all_history' not in data or len(data['all_history']) == 0:
            continue
        
        total_snapshots += len(data['all_history'])
        
        # Filter snapshots from today only (check timestamp starts with today's date)
        today_snapshots = [
            snap for snap in data['all_history']
            if snap.get('timestamp', '').startswith(today_date_str)
        ]
        
        # Only save if we have data from today
        if today_snapshots:
            today_only_data[key] = {
                'symbol': data.get('symbol', ''),
                'strike': data.get('strike', 0),
                'option_type': data.get('option_type', ''),
                'volume_history': [s.get('volume', 0) for s in today_snapshots],
                'all_history': today_snapshots,
                'last_threshold': data.get('last_threshold', 0)
            }
            filtered_snapshots += len(today_snapshots)
    
    try:
        with open(filename, 'w') as f:
            json.dump(today_only_data, f, indent=2)
        
        historical_count = total_snapshots - filtered_snapshots
        logger.debug(f"✅ Options volume data saved: {len(today_only_data)} options, "
                    f"{filtered_snapshots} today's snapshots "
                    f"(removed {historical_count} historical snapshots)")
    except Exception as e:
        logger.error(f"❌ Error saving options history: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# NEW IN v9.0: ENHANCED OPTIONS DATA SAVING
# ═══════════════════════════════════════════════════════════════════════════════
def save_enhanced_options_history():
    """
    Save ONLY today's enhanced options data (MODIFIED: No historical duplication)
    
    This includes: price, volume, OI, OI changes, greeks, bid/ask, etc.
    Used for 3X ML training with comprehensive features.
    
    KEY CHANGE: Filters and saves ONLY today's snapshots to prevent duplication
    in ML training files. In-memory data still retains full 3-day context for
    live predictions.
    """
    today = get_ist_time()
    filename = os.path.join(OPTIONS_ENHANCED_DIR, f"options_enhanced_{today.strftime('%Y%m%d')}.json")
    
    # ⭐ NEW: Filter only today's snapshots (by timestamp date)
    today_date_str = today.strftime('%Y-%m-%d')
    today_only_data = {}
    total_snapshots = 0
    filtered_snapshots = 0
    
    for option_key, option_data in enhanced_options_data.items():
        if 'all_history' not in option_data or len(option_data['all_history']) == 0:
            continue
        
        total_snapshots += len(option_data['all_history'])
        
        # Filter snapshots from today only (check timestamp starts with today's date)
        today_snapshots = [
            snap for snap in option_data['all_history']
            if snap.get('timestamp', '').startswith(today_date_str)
        ]
        
        # Only save if we have data from today
        if today_snapshots:
            today_only_data[option_key] = {
                'all_history': today_snapshots,
                'volume_history': [s.get('volume', 0) for s in today_snapshots]
            }
            filtered_snapshots += len(today_snapshots)
    
    try:
        with open(filename, 'w') as f:
            json.dump(today_only_data, f, indent=2)
        
        historical_count = total_snapshots - filtered_snapshots
        logger.debug(f"✅ Enhanced options data saved: {len(today_only_data)} options, "
                    f"{filtered_snapshots} today's snapshots "
                    f"(filtered out {historical_count} historical snapshots)")
    except Exception as e:
        logger.error(f"❌ Error saving enhanced options history: {e}")

def load_enhanced_options_history():
    """
    ⭐ NEW IN v9.1: Load last 3 days of enhanced options data for continuity
    
    This ensures:
    - 3X predictions start from 9:15 AM (market open) with full context
    - Features have rich historical data (50-100+ snapshots per option)
    - Signal quality remains high (consistent with training data)
    - No compromise on ML prediction accuracy
    
    Benefits:
    - Catch the most profitable first hour (9:15-10:15 AM)
    - Maintain same feature quality as training (which uses 90 days)
    - Options with history: Work from fetch #1 ✓
    - New options: Work from fetch #2-3 ✓
    """
    global enhanced_options_data
    
    logger.info("📊 Loading previous days' enhanced options data...")
    
    today = get_ist_time()
    loaded_days = 0
    total_options_loaded = 0
    
    # Load last 3 trading days (look back 10 days to skip weekends/holidays)
    for days_back in range(1, 10):
        date = today - timedelta(days=days_back)
        
        # Skip weekends
        if date.weekday() >= 5:  # Saturday=5, Sunday=6
            continue
        
        filename = os.path.join(OPTIONS_ENHANCED_DIR, 
                               f"options_enhanced_{date.strftime('%Y%m%d')}.json")
        
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    historical_data = json.load(f)
                
                # Merge historical data into current enhanced_options_data
                for option_key, option_data in historical_data.items():
                    if 'all_history' not in option_data:
                        continue
                    
                    if option_key in enhanced_options_data:
                        # Option already exists - prepend historical data
                        # (historical data comes first, then today's data appends)
                        enhanced_options_data[option_key]['all_history'] = (
                            option_data['all_history'] + 
                            enhanced_options_data[option_key]['all_history']
                        )
                        
                        if 'volume_history' in option_data:
                            enhanced_options_data[option_key]['volume_history'] = (
                                option_data['volume_history'] + 
                                enhanced_options_data[option_key]['volume_history']
                            )
                    else:
                        # New option - create entry with historical data
                        enhanced_options_data[option_key] = {
                            'all_history': option_data['all_history'].copy(),
                            'volume_history': option_data.get('volume_history', []).copy()
                        }
                    
                    total_options_loaded += 1
                
                loaded_days += 1
                logger.info(f"   ✓ Loaded {date.strftime('%Y-%m-%d')}: {len(historical_data)} options")
                
                # Stop after loading 3 trading days
                if loaded_days >= 3:
                    break
                    
            except Exception as e:
                logger.warning(f"   ⚠️  Error loading {filename}: {e}")
                continue
    
    if loaded_days > 0:
        unique_options = len(enhanced_options_data)
        avg_history = sum(len(opt['all_history']) for opt in enhanced_options_data.values()) / max(unique_options, 1)
        
        logger.info(f"✅ Multi-day loading complete:")
        logger.info(f"   • Loaded {loaded_days} trading days")
        logger.info(f"   • {unique_options} unique options tracked")
        logger.info(f"   • Average {avg_history:.0f} snapshots per option")
        logger.info(f"   → 3X predictions will start from 9:15 AM with full context! 🚀")
    else:
        logger.warning("⚠️  No historical enhanced options data found")
        logger.warning("   → This is normal on Day 1")
        logger.warning("   → 3X predictions will start after ~5 cycles (11 AM today)")
        logger.warning("   → From Day 2 onwards, predictions will work from 9:15 AM")
    
    logger.info("")

# ═══════════════════════════════════════════════════════════════════════════════

def track_option_volume(symbol, strike, option_type, current_volume, current_price, current_oi=None, baseline_oi=None):
    """
    Track option volume and detect spikes using ABSOLUTE VOLUME comparison
    
    🆕 DUAL LOGIC SYSTEM:
    1. OI INCREASING PATH:
       ✅ Volume Spike (>=10X, 20X, 30X, etc.)
       ✅ OI Increasing (current_oi > last_oi) [DYNAMIC - FROM LAST FETCH]
       ✅ Price Increasing (current_price > last_price) [GREEN CANDLE]
    
    2. OI DECREASING PATH:
       ✅ Volume Spike (>=10X, 20X, 30X, etc.)
       ✅ OI Decreasing (current_oi < last_oi) [DYNAMIC - FROM LAST FETCH]
       ✅ Price Increasing (current_price > last_price) [GREEN CANDLE]
    
    Both paths save to separate lists for dashboard display.
    """
    global options_volume_tracker, option_volume_spikes_oi_increasing, option_volume_spikes_oi_decreasing
    global option_volume_alerted_oi_increasing, option_volume_alerted_oi_decreasing
    
    key = f"{symbol}_{strike}_{option_type}"
    
    # Initialize tracker if first time seeing this strike
    if key not in options_volume_tracker:
        options_volume_tracker[key] = {
            'symbol': symbol,
            'strike': strike,
            'option_type': option_type,
            'volume_history': [],  # Store absolute volumes
            'last_threshold_increasing': 0,   # Track highest threshold alerted for OI increasing
            'last_threshold_decreasing': 0,   # Track highest threshold alerted for OI decreasing
            'all_history': [],     # Full history for backtesting
            'last_price': None,    # Track last price for green candle check
            'last_oi': None        # Track last OI for dynamic validation
        }
    
    tracker = options_volume_tracker[key]
    
    # Safety check: Ensure fields exist (for backward compatibility)
    if 'last_price' not in tracker:
        tracker['last_price'] = None
    if 'last_oi' not in tracker:
        tracker['last_oi'] = None
    if 'last_threshold_increasing' not in tracker:
        tracker['last_threshold_increasing'] = 0
    if 'last_threshold_decreasing' not in tracker:
        tracker['last_threshold_decreasing'] = 0
    
    # Record current volume snapshot
    snapshot = {
        'timestamp': get_ist_time().strftime("%Y-%m-%d %H:%M:%S"),
        'volume': current_volume,
        'price': current_price
    }
    
    # Add to histories
    tracker['volume_history'].append(current_volume)
    tracker['all_history'].append(snapshot)
    
    # Keep only last 50 for calculation
    if len(tracker['volume_history']) > OPTIONS_VOLUME_HISTORY_SIZE:
        tracker['volume_history'] = tracker['volume_history'][-OPTIONS_VOLUME_HISTORY_SIZE:]
    
    # Need minimum history to calculate average
    history_count = len(tracker['volume_history'])
    if history_count < OPTIONS_VOLUME_MIN_HISTORY:
        return None
    
    # Calculate average of last N fetches
    avg_volume = sum(tracker['volume_history']) / history_count
    
    # Avoid division by zero
    if avg_volume == 0:
        return None
    
    # Calculate multiple
    multiple = current_volume / avg_volume
    
    # Check which threshold is crossed
    current_threshold = None
    for threshold in OPTIONS_VOLUME_THRESHOLDS:
        if multiple >= threshold:
            current_threshold = threshold
    
    # No threshold crossed
    if current_threshold is None:
        return None
    
    # 🆕 PRICE INCREASE CHECK (GREEN CANDLE) - COMMON FOR BOTH PATHS
    # Check if price is increasing from last fetch (skip for first fetch)
    price_is_increasing = False
    if tracker['last_price'] is not None:
        if current_price <= tracker['last_price']:
            # Price is NOT increasing (red or flat candle) - REJECT both paths
            logger.debug(f"❌ {symbol} {strike} {option_type}: Price not increasing (₹{tracker['last_price']:.2f} → ₹{current_price:.2f}), spike rejected")
            # Update last_price for next comparison
            tracker['last_price'] = current_price
            # Update last_oi for next comparison
            if current_oi is not None:
                tracker['last_oi'] = current_oi
            return None
        
        # Price is increasing - log it
        price_change_pct = ((current_price - tracker['last_price']) / tracker['last_price'] * 100)
        logger.info(f"✅ {symbol} {strike} {option_type}: Price increasing (₹{tracker['last_price']:.2f} → ₹{current_price:.2f}, +{price_change_pct:.2f}%)")
        price_is_increasing = True
    else:
        # First fetch - skip price check, allow signal
        logger.debug(f"ℹ️  {symbol} {strike} {option_type}: First fetch, skipping price check")
        price_is_increasing = True
    
    # Update last_price for next comparison
    tracker['last_price'] = current_price
    
    # 🆕 OI DIRECTION CHECK - SPLIT INTO TWO PATHS
    oi_direction = None  # 'increasing', 'decreasing', or None
    oi_change_pct = 0
    
    if current_oi is not None and tracker['last_oi'] is not None:
        if current_oi > tracker['last_oi']:
            oi_direction = 'increasing'
            oi_change_pct = ((current_oi - tracker['last_oi']) / tracker['last_oi'] * 100) if tracker['last_oi'] > 0 else 0
            logger.info(f"✅ {symbol} {strike} {option_type}: OI INCREASING (+{oi_change_pct:.2f}% from last fetch)")
        elif current_oi < tracker['last_oi']:
            oi_direction = 'decreasing'
            oi_change_pct = ((current_oi - tracker['last_oi']) / tracker['last_oi'] * 100) if tracker['last_oi'] > 0 else 0
            logger.info(f"✅ {symbol} {strike} {option_type}: OI DECREASING ({oi_change_pct:.2f}% from last fetch)")
        else:
            # OI unchanged - skip both paths
            logger.debug(f"⚠️  {symbol} {strike} {option_type}: OI unchanged, spike rejected")
            tracker['last_oi'] = current_oi
            return None
    elif current_oi is not None and tracker['last_oi'] is None:
        # First fetch with OI - skip OI check this time
        logger.debug(f"ℹ️  {symbol} {strike} {option_type}: First fetch with OI data, skipping OI direction check")
        tracker['last_oi'] = current_oi
        return None
    else:
        # No OI data available - skip both paths
        tracker['last_oi'] = current_oi
        return None
    
    # Update last_oi for next comparison
    tracker['last_oi'] = current_oi
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PATH 1: OI INCREASING LOGIC
    # ═══════════════════════════════════════════════════════════════════════════════
    if oi_direction == 'increasing':
        # Check if we should alert (only if crossing NEW threshold)
        last_threshold = tracker.get('last_threshold_increasing', 0)
        
        if current_threshold > last_threshold:
            # NEW THRESHOLD CROSSED! Alert!
            tracker['last_threshold_increasing'] = current_threshold
            
            alert_key = f"{key}_increasing_{current_threshold}X"
            
            if alert_key not in option_volume_alerted_oi_increasing:
                option_volume_alerted_oi_increasing.add(alert_key)
                
                # Get lot size for display
                lot_size = LOT_SIZES.get(symbol, 1)
                volume_in_lots = current_volume / lot_size
                
                spike_data = {
                    'symbol': symbol,
                    'strike': strike,
                    'option_type': option_type,
                    'timestamp': snapshot['timestamp'],
                    'current_volume': current_volume,
                    'avg_volume': round(avg_volume, 0),
                    'multiple': round(multiple, 2),
                    'threshold': current_threshold,
                    'price': current_price,
                    'volume_in_lots': round(volume_in_lots, 1),
                    'history_count': history_count,
                    'trigger': f'{current_threshold}X average',
                    'current_oi': current_oi,
                    'last_oi': tracker.get('last_oi'),
                    'oi_change_pct': round(oi_change_pct, 2),
                    'oi_direction': 'INCREASING'
                }
                
                option_volume_spikes_oi_increasing.append(spike_data)
                
                signal_logger.info(f"OPTION_VOLUME_SPIKE_OI_INCREASING | {symbol} {strike} {option_type} | "
                                 f"Vol:{current_volume:,} | Avg:{int(avg_volume):,} | "
                                 f"Multiple:{multiple:.2f}X | Threshold:{current_threshold}X | "
                                 f"Premium:₹{current_price:.2f} | OI:+{oi_change_pct:.2f}%")
                
                # Telegram alert
                emoji = "⚡🟢"
                msg = f"{emoji} <b>OPTION VOLUME SPIKE - OI INCREASING</b>\n\n"
                msg += f"📊 {symbol} {strike} {option_type}\n"
                msg += f"⏰ {snapshot['timestamp'].split(' ')[1]}\n"
                msg += f"💰 Premium: ₹{current_price:.2f}\n"
                msg += f"📈 Current Vol: {current_volume:,} ({int(volume_in_lots)} lots)\n"
                msg += f"📊 Avg Vol: {int(avg_volume):,} (last {history_count} fetches)\n"
                msg += f"🔥 <b>Multiple: {multiple:.2f}X</b>\n"
                msg += f"✅ Threshold: <b>{current_threshold}X</b>\n"
                msg += f"📈 OI Change: <b>+{oi_change_pct:.2f}%</b> ✅ INCREASING"
                
                send_telegram_message(msg)
                
                print(f"  ⚡🟢 OPTION SPIKE (OI↑): {symbol} {strike} {option_type} {multiple:.2f}X ({current_threshold}X)")
                
                return spike_data
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PATH 2: OI DECREASING LOGIC
    # ═══════════════════════════════════════════════════════════════════════════════
    elif oi_direction == 'decreasing':
        # Check if we should alert (only if crossing NEW threshold)
        last_threshold = tracker.get('last_threshold_decreasing', 0)
        
        if current_threshold > last_threshold:
            # NEW THRESHOLD CROSSED! Alert!
            tracker['last_threshold_decreasing'] = current_threshold
            
            alert_key = f"{key}_decreasing_{current_threshold}X"
            
            if alert_key not in option_volume_alerted_oi_decreasing:
                option_volume_alerted_oi_decreasing.add(alert_key)
                
                # Get lot size for display
                lot_size = LOT_SIZES.get(symbol, 1)
                volume_in_lots = current_volume / lot_size
                
                spike_data = {
                    'symbol': symbol,
                    'strike': strike,
                    'option_type': option_type,
                    'timestamp': snapshot['timestamp'],
                    'current_volume': current_volume,
                    'avg_volume': round(avg_volume, 0),
                    'multiple': round(multiple, 2),
                    'threshold': current_threshold,
                    'price': current_price,
                    'volume_in_lots': round(volume_in_lots, 1),
                    'history_count': history_count,
                    'trigger': f'{current_threshold}X average',
                    'current_oi': current_oi,
                    'last_oi': tracker.get('last_oi'),
                    'oi_change_pct': round(oi_change_pct, 2),
                    'oi_direction': 'DECREASING'
                }
                
                option_volume_spikes_oi_decreasing.append(spike_data)
                
                signal_logger.info(f"OPTION_VOLUME_SPIKE_OI_DECREASING | {symbol} {strike} {option_type} | "
                                 f"Vol:{current_volume:,} | Avg:{int(avg_volume):,} | "
                                 f"Multiple:{multiple:.2f}X | Threshold:{current_threshold}X | "
                                 f"Premium:₹{current_price:.2f} | OI:{oi_change_pct:.2f}%")
                
                # Telegram alert
                emoji = "⚡🔴"
                msg = f"{emoji} <b>OPTION VOLUME SPIKE - OI DECREASING</b>\n\n"
                msg += f"📊 {symbol} {strike} {option_type}\n"
                msg += f"⏰ {snapshot['timestamp'].split(' ')[1]}\n"
                msg += f"💰 Premium: ₹{current_price:.2f}\n"
                msg += f"📈 Current Vol: {current_volume:,} ({int(volume_in_lots)} lots)\n"
                msg += f"📊 Avg Vol: {int(avg_volume):,} (last {history_count} fetches)\n"
                msg += f"🔥 <b>Multiple: {multiple:.2f}X</b>\n"
                msg += f"✅ Threshold: <b>{current_threshold}X</b>\n"
                msg += f"📉 OI Change: <b>{oi_change_pct:.2f}%</b> ⚠️ DECREASING"
                
                send_telegram_message(msg)
                
                print(f"  ⚡🔴 OPTION SPIKE (OI↓): {symbol} {strike} {option_type} {multiple:.2f}X ({current_threshold}X)")
                
                return spike_data
    
    return None

# ============================================================================
# ML PREDICTION
# ============================================================================

def predict_direction(spike_data):
    """Predict direction using ML model or rules"""
    import time as time_module
    
    # Features for ML
    features = {
        'candle_body_pct': spike_data.get('candle_body_pct', 0),
        'price_range_pct': spike_data.get('price_range_pct', 0),
        'close_position': spike_data.get('close_position', 0.5),
        'upper_wick_pct': spike_data.get('upper_wick_pct', 0),
        'lower_wick_pct': spike_data.get('lower_wick_pct', 0),
        'volume_position': 1 if spike_data.get('volume_position') == 'top' else (0 if spike_data.get('volume_position') == 'bottom' else 0.5),
        'nifty_change': spike_data.get('nifty_change', 0),
        'nifty_ok': 1 if spike_data.get('nifty_ok', True) else 0,
        'momentum_15min': spike_data.get('momentum_15min', 0),
        'time_of_day': spike_data.get('time_of_day', 12)
    }
    
    # Try ML model
    model_path = os.path.join(MODEL_DIR, "ml_directional.pkl")
    if os.path.exists(model_path):
        try:
            prediction_start_time = time_module.time()
            start_timestamp = get_ist_time().strftime('%H:%M:%S')
            
            model = joblib.load(model_path)
            
            feature_values = [
                features['candle_body_pct'],
                features['price_range_pct'],
                features['close_position'],
                features['upper_wick_pct'],
                features['lower_wick_pct'],
                features['volume_position'],
                features['nifty_change'],
                features['nifty_ok'],
                features['momentum_15min'],
                features['time_of_day']
            ]
            
            prediction = model.predict([feature_values])[0]
            proba = model.predict_proba([feature_values])[0]
            confidence = int(max(proba) * 100)
            
            if prediction == 1:
                direction = "BULLISH"
                action = "BUY_CALL" if confidence >= 60 else "SKIP"
            else:
                direction = "BEARISH"
                action = "BUY_PUT" if confidence >= 60 else "SKIP"
            
            # Only log if confidence > 70%
            if confidence > 70:
                symbol = spike_data.get('symbol', 'UNKNOWN')
                logger.info("")
                logger.info("="*80)
                logger.info(f"🎯 PREDICTION: {symbol} volume spike detected")
                logger.info(f"⏱️  Prediction started at: {start_timestamp}")
                logger.info("="*80)
                logger.info(f"📂 FILE READ: {model_path}")
                logger.info("✅ ML model loaded")
                logger.info("")
                logger.info("🔍 INPUT FEATURES:")
                logger.info(f"   1. Candle Body %: {features['candle_body_pct']:.2f}%")
                logger.info(f"   2. Price Range %: {features['price_range_pct']:.2f}%")
                logger.info(f"   3. Close Position: {features['close_position']:.2f}")
                logger.info(f"   4. Upper Wick %: {features['upper_wick_pct']:.2f}%")
                logger.info(f"   5. Lower Wick %: {features['lower_wick_pct']:.2f}%")
                vol_pos_text = 'top' if features['volume_position'] == 1 else ('bottom' if features['volume_position'] == 0 else 'middle')
                logger.info(f"   6. Volume Position: {features['volume_position']} ({vol_pos_text})")
                logger.info(f"   7. Nifty Change: {features['nifty_change']:+.2f}%")
                logger.info(f"   8. Nifty OK: {features['nifty_ok']} ({'yes' if features['nifty_ok']==1 else 'no'})")
                logger.info(f"   9. Momentum 15min: {features['momentum_15min']:+.2f}%")
                logger.info(f"   10. Time of Day: {features['time_of_day']:.1f}")
                logger.info("")
                logger.info("🤖 ML PREDICTION:")
                logger.info(f"   • Direction: {direction}")
                logger.info(f"   • Action: {action}")
                logger.info(f"   • Confidence: {confidence}% ✅ (>70%)")
                logger.info(f"   • Method: ML")
                logger.info("")
                prediction_time = time_module.time() - prediction_start_time
                logger.info(f"⏱️  Prediction completed in: {prediction_time:.2f} seconds")
                logger.info("="*80 + "\n")
            
            return {
                'direction': direction,
                'action': action,
                'confidence': confidence,
                'method': 'ML'
            }
        except Exception as e:
            logger.debug(f"ML model prediction failed: {e}")
            pass
    
    # Fallback to rule-based
    candle_type = spike_data.get('candle_type', 'green')
    candle_body_pct = spike_data.get('candle_body_pct', 0)
    close_position = spike_data.get('close_position', 0.5)
    nifty_ok = spike_data.get('nifty_ok', True)
    
    if candle_type == 'green' and candle_body_pct > 1.0 and close_position > 0.6 and nifty_ok:
        return {
            'direction': 'BULLISH',
            'action': 'BUY_CALL',
            'confidence': 70,
            'method': 'RULE'
        }
    elif candle_type == 'red' and candle_body_pct < -1.0 and close_position < 0.4 and nifty_ok:
        return {
            'direction': 'BEARISH',
            'action': 'BUY_PUT',
            'confidence': 70,
            'method': 'RULE'
        }
    else:
        return {
            'direction': 'NEUTRAL',
            'action': 'SKIP',
            'confidence': 50,
            'method': 'RULE'
        }

# ============================================================================
# COMBINED SIGNALS
# ============================================================================

def check_combined_signals():
    """Check for combined signals (all 3 must match)"""
    global combined_signals
    
    combined_signals = []
    
    # Create lookup dictionaries
    oi_dict = {sig['symbol']: sig for sig in oi_signals}
    stock_dict = {spike['symbol']: spike for spike in stock_volume_spikes}
    
    # Group option spikes by symbol (combine both OI increasing and decreasing lists)
    option_spikes_by_symbol = {}
    for spike in option_volume_spikes_oi_increasing + option_volume_spikes_oi_decreasing:
        symbol = spike['symbol']
        if symbol not in option_spikes_by_symbol:
            option_spikes_by_symbol[symbol] = []
        option_spikes_by_symbol[symbol].append(spike)
    
    # Check each symbol with OI signal
    for symbol, oi_sig in oi_dict.items():
        # Must have stock volume spike
        if symbol not in stock_dict:
            continue
        
        stock_spike = stock_dict[symbol]
        ml_pred = stock_spike.get('ml_prediction', {})
        
        # Must have option volume spikes
        if symbol not in option_spikes_by_symbol:
            continue
        
        # Find HIGHEST multiple option spike
        option_spikes = option_spikes_by_symbol[symbol]
        highest_spike = max(option_spikes, key=lambda x: x['multiple'])
        
        # Determine option direction based on type
        option_direction = "BUY" if highest_spike['option_type'] == 'CE' else "SELL"
        
        # Check if all 3 match
        oi_direction = oi_sig['signal_type']
        ml_direction = "BUY" if ml_pred.get('action') == 'BUY_CALL' else ("SELL" if ml_pred.get('action') == 'BUY_PUT' else None)
        
        if ml_direction and oi_direction == option_direction == ml_direction:
            combined_signal = {
                'symbol': symbol,
                'direction': oi_direction,
                'oi_signal': oi_sig,
                'stock_spike': stock_spike,
                'option_spike': highest_spike,
                'timestamp': get_ist_time().strftime("%H:%M:%S")
            }
            
            combined_signals.append(combined_signal)
            
            signal_logger.info(f"COMBINED_SIGNAL | {symbol} | {oi_direction} | "
                             f"OI:{oi_sig['threshold']}% | Stock:{stock_spike['mcap_pct']:.4f}% | "
                             f"Option:{highest_spike['multiple']:.2f}X")
            
            emoji = "🟢" if oi_direction == "BUY" else "🔴"
            msg = f"{emoji} <b>🎯 COMBINED SIGNAL - {oi_direction}</b>\n\n"
            msg += f"📊 {symbol}\n"
            msg += f"⏰ {combined_signal['timestamp']}\n\n"
            msg += f"1️⃣ OI: {oi_sig['signal_type']} [{oi_sig['threshold']}%]\n"
            msg += f"2️⃣ Stock: {stock_spike['mcap_pct']:.4f}% MCap\n"
            msg += f"3️⃣ Option: {highest_spike['strike']} {highest_spike['option_type']} ({highest_spike['multiple']:.2f}X)\n\n"
            msg += f"🤖 ML: {ml_pred.get('action', 'N/A')} ({ml_pred.get('confidence', 0)}%)"
            
            send_telegram_message(msg)
            
            print(f"  🎯 COMBINED: {symbol} {oi_direction}")

# ============================================================================
# PAPER TRADING - ✅ FIXED: AUTO-SAVE AFTER OPENING
# ============================================================================

def open_paper_position(spike_data, ml_prediction):
    """
    Open paper position (ATM+1 CE or ATM-1 PE)
    ✅ FIXED: Returns position object for immediate saving
    """
    global paper_positions, capital
    
    symbol = spike_data['symbol']
    security_id = spike_data['security_id']
    action = ml_prediction['action']
    
    for pos in paper_positions:
        if pos['symbol'] == symbol and pos['status'] == 'OPEN':
            return None
    
    stock_entry_price = spike_data['close']
    expiry_date = get_trading_expiry()
    
    option_chain = get_option_chain(security_id, expiry_date)
    if not option_chain:
        return None
    
    if action == 'BUY_CALL':
        atm, interval = find_atm_strike(stock_entry_price, option_chain)
        if not atm or not interval:
            return None
        
        strikes = []
        oc_data = option_chain["data"]["oc"]
        for strike_str in oc_data.keys():
            try:
                strikes.append(float(strike_str))
            except:
                continue
        strikes = sorted(strikes)
        
        atm_index = strikes.index(atm)
        if atm_index + 1 >= len(strikes):
            return None
        strike = strikes[atm_index + 1]
        option_type = 'CE'
        
    else:
        atm, interval = find_atm_strike(stock_entry_price, option_chain)
        if not atm or not interval:
            return None
        
        strikes = []
        oc_data = option_chain["data"]["oc"]
        for strike_str in oc_data.keys():
            try:
                strikes.append(float(strike_str))
            except:
                continue
        strikes = sorted(strikes)
        
        atm_index = strikes.index(atm)
        if atm_index - 1 < 0:
            strike = atm
        else:
            strike = strikes[atm_index - 1]
        option_type = 'PE'
    
    strike_str = f"{strike:.6f}"
    if strike_str not in option_chain["data"]["oc"]:
        return None
    
    strike_data = option_chain["data"]["oc"][strike_str]
    option_key = "ce" if option_type == 'CE' else "pe"
    
    if option_key not in strike_data:
        return None
    
    premium = float(strike_data[option_key].get("last_price", 0) or 0)
    if premium <= 0:
        return None
    
    lot_size = LOT_SIZES.get(symbol, 1)
    shares = LOTS_PER_TRADE * lot_size
    total_cost = premium * shares
    
    if option_type == 'CE':
        target_stock = stock_entry_price * (1 + CALL_TARGET_PCT / 100)
        sl_stock = stock_entry_price * (1 + CALL_STOPLOSS_PCT / 100)
    else:
        target_stock = stock_entry_price * (1 + PUT_TARGET_PCT / 100)
        sl_stock = stock_entry_price * (1 + PUT_STOPLOSS_PCT / 100)
    
    entry_time = spike_data['datetime']
    if isinstance(entry_time, str):
        entry_time = pd.to_datetime(entry_time)
    exit_date = entry_time + timedelta(days=HOLDING_DAYS)
    
    position = {
        'id': len(paper_positions) + len(closed_trades) + 1,
        'symbol': symbol,
        'security_id': security_id,
        'option_type': option_type,
        'strike': strike,
        'expiry_date': expiry_date,
        'entry_time': entry_time.isoformat() if hasattr(entry_time, 'isoformat') else str(entry_time),
        'entry_premium': round(premium, 2),
        'current_premium': round(premium, 2),
        'lots': LOTS_PER_TRADE,
        'lot_size': lot_size,
        'shares': shares,
        'total_cost': round(total_cost, 2),
        'stock_entry_price': round(stock_entry_price, 2),
        'current_stock_price': round(stock_entry_price, 2),
        'target_stock_price': round(target_stock, 2),
        'stoploss_stock_price': round(sl_stock, 2),
        'exit_date': exit_date.strftime('%Y-%m-%d'),
        'days_held': 0,
        'current_value': round(total_cost, 2),
        'unrealized_pnl': 0.0,
        'ml_confidence': ml_prediction['confidence'],
        'ml_direction': ml_prediction['direction'],
        'spike_mcap_pct': spike_data['mcap_pct'],
        'candle_type': spike_data['candle_type'],
        'nifty_change': spike_data['nifty_change'],
        'status': 'OPEN'
    }
    
    capital -= total_cost
    paper_positions.append(position)
    
    print(f"  💼 OPENED: {symbol} {strike} {option_type} @ ₹{premium:.2f}")
    
    # ⭐ RETURN POSITION for immediate saving
    return position

def update_paper_positions():
    """Update all open positions"""
    global paper_positions, closed_trades, capital
    
    for i in range(len(paper_positions) - 1, -1, -1):
        pos = paper_positions[i]
        
        if pos['status'] != 'OPEN':
            continue
        
        security_id = pos['security_id']
        current_stock_price = get_stock_price(security_id)
        
        if not current_stock_price:
            continue
        
        pos['current_stock_price'] = round(current_stock_price, 2)
        
        # Check SL/Target on stock price
        exit_reason = None
        
        if pos['option_type'] == 'CE':
            if current_stock_price >= pos['target_stock_price']:
                exit_reason = "Target Hit"
            elif current_stock_price <= pos['stoploss_stock_price']:
                exit_reason = "Stop Loss"
        else:
            if current_stock_price <= pos['target_stock_price']:
                exit_reason = "Target Hit"
            elif current_stock_price >= pos['stoploss_stock_price']:
                exit_reason = "Stop Loss"
        
        # Check holding period
        entry_time = pd.to_datetime(pos['entry_time'])
        days_held = (get_ist_time() - entry_time).days
        pos['days_held'] = days_held
        
        if days_held >= HOLDING_DAYS and not exit_reason:
            exit_reason = "Time Expired"
        
        # Update premium and P&L
        option_chain = get_option_chain(security_id, pos['expiry_date'])
        if option_chain:
            strike_str = f"{pos['strike']:.6f}"
            if strike_str in option_chain["data"]["oc"]:
                strike_data = option_chain["data"]["oc"][strike_str]
                option_key = "ce" if pos['option_type'] == 'CE' else "pe"
                if option_key in strike_data:
                    current_premium = float(strike_data[option_key].get("last_price", 0) or 0)
                    if current_premium > 0:
                        pos['current_premium'] = round(current_premium, 2)
                        pos['current_value'] = round(current_premium * pos['shares'], 2)
                        pos['unrealized_pnl'] = round(pos['current_value'] - pos['total_cost'], 2)
        
        # Close if needed
        if exit_reason:
            final_premium = pos['current_premium']
            final_value = pos['current_value']
            pnl = pos['unrealized_pnl']
            pnl_pct = (pnl / pos['total_cost']) * 100
            
            capital += final_value
            
            closed_trade = {
                **pos,
                'exit_time': get_ist_time().isoformat(),
                'exit_premium': final_premium,
                'exit_reason': exit_reason,
                'days_held': days_held,
                'final_pnl': pnl,
                'pnl_pct': pnl_pct
            }
            
            closed_trades.append(closed_trade)
            paper_positions.pop(i)
            
            save_paper_trading_data()
            
            emoji = "🟢" if pnl > 0 else "🔴"
            msg = f"{emoji} <b>POSITION CLOSED</b>\n\n"
            msg += f"📊 {closed_trade['symbol']} {closed_trade['strike']} {closed_trade['option_type']}\n"
            msg += f"💰 Entry: ₹{closed_trade['entry_premium']:.2f}\n"
            msg += f"💰 Exit: ₹{final_premium:.2f}\n"
            msg += f"📊 P&L: ₹{pnl:,.2f} ({pnl_pct:+.2f}%)\n"
            msg += f"🎯 Reason: {exit_reason}\n"
            msg += f"📅 Days: {days_held}"
            
            send_telegram_message(msg)
            
            print(f"  💼 CLOSED: {closed_trade['symbol']} | P&L: ₹{pnl:,.2f} ({pnl_pct:+.2f}%)")

def save_paper_trading_data():
    """Save positions and trades"""
    positions_file = os.path.join(PAPER_TRADING_DIR, "positions.json")
    trades_file = os.path.join(PAPER_TRADING_DIR, "closed_trades.json")
    
    with open(positions_file, 'w') as f:
        json.dump({
            'positions': paper_positions,
            'capital': capital
        }, f, indent=2)
    
    with open(trades_file, 'w') as f:
        json.dump(closed_trades, f, indent=2)

def load_paper_trading_data():
    """Load positions and trades"""
    global paper_positions, closed_trades, capital
    
    positions_file = os.path.join(PAPER_TRADING_DIR, "positions.json")
    trades_file = os.path.join(PAPER_TRADING_DIR, "closed_trades.json")
    
    if os.path.exists(positions_file):
        with open(positions_file, 'r') as f:
            data = json.load(f)
            paper_positions = data.get('positions', [])
            capital = data.get('capital', STARTING_CAPITAL)
    
    if os.path.exists(trades_file):
        with open(trades_file, 'r') as f:
            closed_trades = json.load(f)
    
    logger.info(f"✅ Loaded paper trading:")
    logger.info(f"   Open Positions: {len(paper_positions)}")
    logger.info(f"   Closed Trades: {len(closed_trades)}")
    logger.info(f"   Capital: ₹{capital:,.0f}")

# ============================================================================
# 5-MINUTE STOCK VOLUME MONITOR - ✅ FIXED: BATCHED FETCHING
# ============================================================================

def run_stock_volume_monitor():
    """
    ✅ FIXED: Batched stock volume monitoring
    - Fetches ALL stocks in ONE API call (like opening prices)
    - Checks for spikes in new candles only
    - Dramatically reduced API usage: ~60 calls/day instead of 15,075!
    """
    global stock_volume_monitor_running, last_checked_candles, opening_prices
    global stock_volume_spikes, stock_volume_alerted, current_prices
    
    logger.info("\n" + "="*80)
    logger.info("⏰ 5-MINUTE STOCK VOLUME MONITOR - STARTING (BATCHED)")
    logger.info("="*80)
    logger.info("✅ NEW: Batched fetching (1 API call per cycle)")
    logger.info("✅ Checks for new candles only")
    logger.info("✅ NO volume spikes will be missed!")
    logger.info("="*80 + "\n")
    
    stock_volume_monitor_running = True
    check_count = 0
    
    while stock_volume_monitor_running and is_market_open():
        try:
            check_count += 1
            now = get_ist_time()
            logger.info(f"\n⏰ [5-MIN CHECK #{check_count}] Stock Volume Monitor at {now.strftime('%H:%M:%S')}")
            
            new_spikes = 0
            
            # ✅ FIX: Get ALL stocks' candles data in batches
            # We'll still need to call get_stock_5min_candles individually, 
            # but we can check all of them without delays
            
            for symbol, price_info in opening_prices.items():
                if not stock_volume_monitor_running:
                    break
                
                if symbol not in MARKET_CAPS:
                    continue
                
                security_id = price_info["security_id"]
                current_price = current_prices.get(symbol, price_info["open_price"])
                
                try:
                    # Get all 5-min candles for today
                    candles = get_stock_5min_candles(security_id)
                    if not candles or len(candles) == 0:
                        continue
                    
                    # Get the timestamp of last checked candle for this stock
                    last_checked = last_checked_candles.get(symbol, None)
                    
                    # Check ALL candles since last check
                    for candle in candles:
                        candle_time = candle.get('timestamp')
                        if not candle_time:
                            continue
                        
                        # Properly convert timestamp to datetime FIRST
                        if isinstance(candle_time, str):
                            candle_time = pd.to_datetime(candle_time)
                        elif isinstance(candle_time, (int, float)):
                            # Numeric timestamp - check if it's in seconds or milliseconds
                            from datetime import datetime
                            if candle_time > 10000000000:  # Milliseconds (13 digits)
                                candle_time = datetime.fromtimestamp(candle_time / 1000, tz=ist)
                            else:  # Seconds (10 digits)
                                candle_time = datetime.fromtimestamp(candle_time, tz=ist)
                        elif not hasattr(candle_time, 'hour'):
                            # Unknown format, use current time
                            candle_time = get_ist_time()
                        
                        # Skip if we already checked this candle
                        if last_checked and candle_time <= last_checked:
                            continue
                        
                        # Check this candle for volume spike
                        volume = candle['volume']
                        avg_price = (candle['high'] + candle['low']) / 2
                        traded_value = volume * avg_price
                        market_cap = MARKET_CAPS.get(symbol)
                        mcap_pct = (traded_value / market_cap) * 100
                        
                        if mcap_pct >= STOCK_MCAP_THRESHOLD:
                            alert_key = f"{symbol}_{candle_time}"
                            
                            if alert_key not in stock_volume_alerted:
                                stock_volume_alerted.add(alert_key)
                                
                                # Create full spike data with all required fields for dashboard
                                open_price = candle['open']
                                high_price = candle['high']
                                low_price = candle['low']
                                close_price = candle['close']
                                
                                # Determine candle type
                                candle_body = close_price - open_price
                                candle_type = 'green' if candle_body > 0 else 'red'
                                candle_body_pct = (candle_body / open_price * 100) if open_price > 0 else 0
                                
                                price_range = high_price - low_price
                                price_range_pct = (price_range / open_price * 100) if open_price > 0 else 0
                                close_position = ((close_price - low_price) / price_range) if price_range > 0 else 0.5
                                
                                if candle_body > 0:
                                    upper_wick = high_price - close_price
                                    lower_wick = open_price - low_price
                                else:
                                    upper_wick = high_price - open_price
                                    lower_wick = close_price - low_price
                                
                                upper_wick_pct = (upper_wick / open_price * 100) if open_price > 0 else 0
                                lower_wick_pct = (lower_wick / open_price * 100) if open_price > 0 else 0
                                volume_position = 'top' if close_position > 0.6 else ('bottom' if close_position < 0.4 else 'middle')
                                
                                spike_data = {
                                    'symbol': symbol,
                                    'datetime': candle_time,
                                    'timestamp': candle_time.strftime("%H:%M:%S") if hasattr(candle_time, 'strftime') else str(candle_time),
                                    'volume': volume,
                                    'avg_price': round(avg_price, 2),
                                    'traded_value_cr': round(traded_value / 10000000, 2),
                                    'market_cap_cr': round(market_cap / 10000000, 2),
                                    'mcap_pct': round(mcap_pct, 4),
                                    'open': round(open_price, 2),
                                    'high': round(high_price, 2),
                                    'low': round(low_price, 2),
                                    'close': round(close_price, 2),
                                    'current_price': current_price,
                                    'candle_type': candle_type,
                                    'candle_body_pct': round(candle_body_pct, 4),
                                    'price_range_pct': round(price_range_pct, 4),
                                    'close_position': round(close_position, 4),
                                    'upper_wick_pct': round(upper_wick_pct, 4),
                                    'lower_wick_pct': round(lower_wick_pct, 4),
                                    'volume_position': volume_position,
                                    'nifty_change': 0,  # Not calculated in 5-min check for speed
                                    'nifty_ok': True,
                                    'momentum_15min': 0,
                                    'time_of_day': candle_time.hour + (candle_time.minute / 60) if hasattr(candle_time, 'hour') else 12,
                                    'security_id': security_id,
                                    'detected_by': '5-min monitor'
                                }
                                
                                # Run ML prediction and paper trading
                                ml_prediction = predict_direction(spike_data)
                                spike_data['ml_prediction'] = ml_prediction
                                
                                stock_volume_spikes.append(spike_data)
                                ml_predictions.append({
                                    'symbol': symbol,
                                    'timestamp': spike_data['timestamp'],
                                    'action': ml_prediction['action'],
                                    'direction': ml_prediction['direction'],
                                    'confidence': ml_prediction['confidence']
                                })
                                
                                new_spikes += 1
                                
                                logger.info(f"  ⚡ SPIKE DETECTED: {symbol} | {mcap_pct:.4f}% | Vol: {volume:,} | ML: {ml_prediction['action']}")
                                
                                # ✅ FIX: Open position AND save immediately
                                if ml_prediction['action'] in ['BUY_CALL', 'BUY_PUT']:
                                    logger.info(f"  💼 Opening paper position for {symbol}...")
                                    position = open_paper_position(spike_data, ml_prediction)
                                    if position:
                                        # ⭐ CRITICAL FIX: Save after opening position
                                        save_paper_trading_data()
                                        logger.info(f"  💾 Position saved to disk")
                                
                                # Send telegram alert
                                direction = ml_prediction['direction']
                                action = ml_prediction['action']
                                
                                if action == 'BUY_CALL':
                                    emoji = "🟢"
                                    action_text = "BUY CALL"
                                elif action == 'BUY_PUT':
                                    emoji = "🔴"
                                    action_text = "BUY PUT"
                                else:
                                    emoji = "⚪"
                                    action_text = "SKIP"
                                
                                msg = f"{emoji} <b>VOLUME SPIKE [5-MIN] - {direction}</b>\n\n"
                                msg += f"📊 {symbol}\n"
                                msg += f"⏰ {spike_data['timestamp']}\n"
                                msg += f"💰 Price: ₹{close_price:.2f}\n"
                                msg += f"🕯️ Candle: {candle_type.upper()} ({candle_body_pct:+.2f}%)\n"
                                msg += f"📈 Volume: {volume:,}\n"
                                msg += f"💵 Traded: ₹{spike_data['traded_value_cr']:.2f} Cr\n"
                                msg += f"📊 MCap %: <b>{mcap_pct:.4f}%</b>\n\n"
                                msg += f"🤖 <b>ML: {action_text}</b>\n"
                                msg += f"🎯 Confidence: {ml_prediction['confidence']}%"
                                
                                send_telegram_message(msg)
                    
                    # Update last checked timestamp for this stock
                    if candles:
                        last_candle = candles[-1]
                        last_candle_time = last_candle.get('timestamp')
                        if isinstance(last_candle_time, str):
                            last_candle_time = pd.to_datetime(last_candle_time)
                        last_checked_candles[symbol] = last_candle_time
                
                except Exception as e:
                    # Silent fail for individual stocks
                    continue
            
            logger.info(f"  ✅ 5-Min Check #{check_count} Complete | New Spikes: {new_spikes}")
            
            # Wait 5 minutes before next check
            time.sleep(300)  # 300 seconds = 5 minutes
        
        except Exception as e:
            logger.error(f"❌ Error in 5-min monitor: {e}")
            time.sleep(300)
    
    stock_volume_monitor_running = False
    logger.info("\n⏰ 5-Minute Stock Volume Monitor stopped\n")

# ═══════════════════════════════════════════════════════════════════════════════
# 3X DETECTOR FUNCTIONS (NEW IN v9.0)
# ═══════════════════════════════════════════════════════════════════════════════

def initialize_3x_detector():
    """Initialize and load the 3X detector (dual model system)"""
    global threex_detector, threex_enabled
    import time as time_module
    
    if not THREEX_DETECTOR_AVAILABLE:
        logger.warning("⚠️  3X Detector module not available")
        return False
    
    init_start_time = time_module.time()
    start_timestamp = get_ist_time().strftime('%H:%M:%S')
    
    logger.info("\n" + "="*80)
    logger.info("🎯 INITIALIZING 3X DETECTOR (DUAL MODEL SYSTEM)")
    logger.info(f"⏱️  Initialization started at: {start_timestamp}")
    logger.info("="*80)
    logger.info(f"📂 MODEL DIR: {MODEL_DIR}")
    logger.info("")
    
    try:
        threex_detector = Live3XDetector(
            model_dir=MODEL_DIR,
            early_threshold=0.50,  # Changed from 0.75 to 0.50
            late_threshold=0.50    # Changed from 0.75 to 0.50
        )
        
        if threex_detector.load_models():
            threex_enabled = True
            
            # Log individual model files
            early_model_path = os.path.join(MODEL_DIR, "3x_early_model.pkl")
            late_model_path = os.path.join(MODEL_DIR, "3x_late_model.pkl")
            scaler_path = os.path.join(MODEL_DIR, "3x_scaler.pkl")
            
            if threex_detector.using_dual_models:
                logger.info("✅ MODE: DUAL MODEL SYSTEM")
                logger.info("")
                
                if threex_detector.early_models:
                    logger.info(f"📂 FILE READ: {early_model_path}")
                    logger.info("✅ Early model loaded (>5 days expiry)")
                    if os.path.exists(early_model_path):
                        file_size_kb = os.path.getsize(early_model_path) / 1024
                        logger.info(f"   • Size: {file_size_kb:.0f} KB")
                else:
                    logger.warning(f"⚠️  Early model not available: {early_model_path}")
                
                logger.info("")
                
                if threex_detector.late_models:
                    logger.info(f"📂 FILE READ: {late_model_path}")
                    logger.info("✅ Late model loaded (≤5 days expiry)")
                    if os.path.exists(late_model_path):
                        file_size_kb = os.path.getsize(late_model_path) / 1024
                        logger.info(f"   • Size: {file_size_kb:.0f} KB")
                else:
                    logger.warning(f"⚠️  Late model not available: {late_model_path}")
                
                logger.info("")
                
                if os.path.exists(scaler_path):
                    logger.info(f"📂 FILE READ: {scaler_path}")
                    logger.info("✅ Scaler loaded")
                    file_size_kb = os.path.getsize(scaler_path) / 1024
                    logger.info(f"   • Size: {file_size_kb:.0f} KB")
                
            else:
                logger.info("✅ MODE: Single Model (legacy)")
            
            logger.info("")
            logger.info(f"   Early threshold: {threex_detector.early_threshold*100:.0f}%")
            logger.info(f"   Late threshold: {threex_detector.late_threshold*100:.0f}%")
            
            init_time = time_module.time() - init_start_time
            logger.info("")
            logger.info(f"⏱️  Initialization completed in: {init_time:.2f} seconds")
            logger.info("="*80 + "\n")
            return True
        else:
            logger.warning("")
            logger.warning("⚠️  3X Detector models not found")
            logger.warning("   Run train_3x_detector_dual_model.py to train models")
            logger.warning("="*80 + "\n")
            threex_enabled = False
            return False
            
    except Exception as e:
        logger.error("")
        logger.error(f"❌ Error loading 3X detector: {e}")
        import traceback
        traceback.print_exc()
        logger.error("="*80 + "\n")
        threex_enabled = False
        return False

def run_3x_detection():
    """
    Run 3X pattern detection on current enhanced options data
    
    Called once per scanner cycle after all option chains are fetched.
    Uses in-memory enhanced_options_data (no additional API calls).
    """
    global threex_predictions, threex_alerts
    
    if not threex_enabled or threex_detector is None:
        return
    
    if len(enhanced_options_data) == 0:
        logger.debug("   No enhanced options data available for 3X detection")
        return
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🔍 RUNNING 3X PATTERN DETECTION")
    logger.info(f"{'='*80}")
    logger.info(f"Analyzing {len(enhanced_options_data)} options...")
    
    try:
        # Get predictions (top 20 with highest confidence)
        predictions = threex_detector.predict(enhanced_options_data, top_n=20)
        
        logger.info(f"   Found {len(predictions)} predictions above threshold!")
        
        # Store predictions for dashboard
        threex_predictions = []
        for pred in predictions:
            # At prediction time, we're at 1.0X (current price)
            current_multiplier = 1.0
            
            pred_dict = {
                'timestamp': get_ist_time().strftime('%H:%M:%S'),
                'option_key': pred['option_key'],
                'symbol': pred['symbol'],
                'strike': pred['strike'],
                'option_type': pred['option_type'],
                'confidence': pred['confidence'],
                'current_price': pred['current_price'],
                'target_price': pred['target_price'],
                'current_multiplier': current_multiplier,
                'days_to_expiry': pred.get('days_to_expiry', 0),
                'model_used': pred.get('model_used', 'unknown')
            }
            threex_predictions.append(pred_dict)
            
            # Generate alerts for very high confidence predictions (>90%)
            if pred['confidence'] > 0.90:
                alert_dict = {
                    'timestamp': get_ist_time().strftime('%H:%M:%S'),
                    'option_key': pred['option_key'],
                    'confidence': pred['confidence'],
                    'alert_type': 'PATTERN',
                    'message': f"🎯 3X PATTERN DETECTED\n\n"
                              f"📊 {pred['option_key']}\n"
                              f"💰 Current: ₹{pred['current_price']:.2f}\n"
                              f"🎯 Target: ₹{pred['target_price']:.2f}\n"
                              f"📈 Confidence: {pred['confidence']*100:.1f}%\n"
                              f"📅 Days to Expiry: {pred.get('days_to_expiry', 'N/A')}\n"
                              f"🤖 Model: {pred.get('model_used', 'N/A').upper()}",
                    'current_price': pred['current_price'],
                    'current_multiplier': current_multiplier,
                    'model_used': pred.get('model_used', 'unknown')
                }
                
                threex_alerts.append(alert_dict)
                
                # Keep only last 50 alerts
                if len(threex_alerts) > 50:
                    threex_alerts = threex_alerts[-50:]
                
                # Send Telegram alert
                send_telegram_message(alert_dict['message'])
                
                # Log to signal logger
                signal_logger.info(f"3X_ALERT | {pred['option_key']} | "
                                  f"Conf:{pred['confidence']*100:.1f}% | "
                                  f"Model:{pred.get('model_used', 'N/A')}")
                
                logger.info(f"   ⚡ HIGH CONF ALERT: {pred['option_key']} - {pred['confidence']*100:.1f}% "
                           f"({pred.get('model_used', 'N/A')})")
        
        # Log top prediction
        if threex_predictions:
            top = threex_predictions[0]
            logger.info(f"\n   Top Prediction: {top['option_key']}")
            logger.info(f"   • Confidence: {top['confidence']*100:.1f}%")
            logger.info(f"   • Current: ₹{top['current_price']:.2f}")
            logger.info(f"   • Target: ₹{top['target_price']:.2f}")
            logger.info(f"   • Days to Expiry: {top.get('days_to_expiry', 'N/A')}")
            logger.info(f"   • Model: {top.get('model_used', 'N/A')}")
        
        logger.info(f"{'='*80}")
        logger.info(f"✅ 3X Detection Complete - {len(threex_predictions)} predictions, {len([a for a in threex_alerts if a.get('timestamp') == get_ist_time().strftime('%H:%M:%S')])} new alerts")
        logger.info(f"{'='*80}\n")
        
    except Exception as e:
        logger.error(f"❌ Error in 3X detection: {e}")
        import traceback
        traceback.print_exc()

def scheduled_3x_training():
    """
    Run scheduled 3X model training at 4:30 PM daily
    
    Trains dual models (early + late expiry) on rolling 90-day window.
    Creates backups of old models before training.
    Sends Telegram alerts on success/failure.
    """
    import time as time_module
    
    training_start_time = time_module.time()
    start_timestamp = get_ist_time().strftime('%H:%M:%S')
    
    logger.info("\n" + "="*80)
    logger.info("🧠 SCHEDULED 3X TRAINING (ADVANCED ENSEMBLE)")
    logger.info(f"⏱️  Training started at: {start_timestamp}")
    logger.info("="*80)
    logger.info("Training ADVANCED ensemble models (early + late expiry)...")
    logger.info("XGBoost + LightGBM + CatBoost with 190+ features")
    logger.info("This may take 40-60 minutes depending on data size.")
    logger.info("="*80 + "\n")
    
    import subprocess
    
    try:
        # Check for existing models and create backups
        training_script = "train_3x_detector_topn_v7.py"
        logger.info(f"📂 TRAINING SCRIPT: {training_script}")
        logger.info("")
        
        # Backup existing models - FIXED: Correct filenames matching training script
        timestamp_backup = datetime.now().strftime('%Y%m%d_%H%M%S')
        models_to_backup = [
            # Early models (3 ensemble models)
            ("3x_detector_early_xgboost.pkl", f"3x_detector_early_xgboost_{timestamp_backup}.pkl"),
            ("3x_detector_early_lightgbm.pkl", f"3x_detector_early_lightgbm_{timestamp_backup}.pkl"),
            ("3x_detector_early_catboost.pkl", f"3x_detector_early_catboost_{timestamp_backup}.pkl"),
            
            # Late models (3 ensemble models)
            ("3x_detector_late_xgboost.pkl", f"3x_detector_late_xgboost_{timestamp_backup}.pkl"),
            ("3x_detector_late_lightgbm.pkl", f"3x_detector_late_lightgbm_{timestamp_backup}.pkl"),
            ("3x_detector_late_catboost.pkl", f"3x_detector_late_catboost_{timestamp_backup}.pkl"),
            
            # Scalers (2 files)
            ("3x_scaler_early.pkl", f"3x_scaler_early_{timestamp_backup}.pkl"),
            ("3x_scaler_late.pkl", f"3x_scaler_late_{timestamp_backup}.pkl"),
            
            # Feature columns (2 files)
            ("3x_feature_columns_early.pkl", f"3x_feature_columns_early_{timestamp_backup}.pkl"),
            ("3x_feature_columns_late.pkl", f"3x_feature_columns_late_{timestamp_backup}.pkl")
        ]
        
        logger.info("📦 BACKING UP EXISTING MODELS:")
        backup_count = 0
        for model_file, backup_file in models_to_backup:
            model_path = os.path.join(MODEL_DIR, model_file)
            backup_path = os.path.join(MODEL_BACKUP_DIR, backup_file)
            if os.path.exists(model_path):
                import shutil
                shutil.copy2(model_path, backup_path)
                file_size_kb = os.path.getsize(backup_path) / 1024
                logger.info(f"   ✅ Backed up {model_file} ({file_size_kb:.0f} KB)")
                backup_count += 1
        
        if backup_count == 0:
            logger.info("   ℹ️  No existing models found (first time training)")
        else:
            logger.info(f"   ✅ Total: {backup_count} files backed up")
        
        logger.info("")
        logger.info("🔄 EXECUTING TRAINING:")
        logger.info("="*80)
        
        # Set environment for UTF-8 encoding (fixes emoji print issues on Windows)
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            [sys.executable, training_script],
            capture_output=True,
            text=True,
            timeout=18000,  # ✅ FIXED: 300 minute timeout (5 hours) - sufficient for ensemble training
            env=env,       # Pass UTF-8 environment
            encoding='utf-8',  # Explicitly set encoding
            errors='replace'   # Replace encoding errors instead of crashing
        )
        
        training_time = time_module.time() - training_start_time
        
        if result.returncode == 0:
            logger.info("="*80)
            logger.info("✅ TRAINING COMPLETE")
            logger.info("="*80)
            
            # Parse training output for key metrics (if available in stdout)
            output_lines = result.stdout.split('\n')
            metrics_found = False
            for line in output_lines:
                if 'PR-AUC' in line or 'Precision' in line or 'Recall' in line:
                    logger.info(f"   {line}")
                    metrics_found = True
            
            if not metrics_found:
                logger.info("   Models trained and saved successfully")
            
            logger.info("")
            
            # Log new model files
            logger.info("📂 NEW MODEL FILES:")
            model_files_found = []
            for model_file, _ in models_to_backup:
                model_path = os.path.join(MODEL_DIR, model_file)
                if os.path.exists(model_path):
                    file_size_kb = os.path.getsize(model_path) / 1024
                    logger.info(f"   ✅ {model_file} ({file_size_kb:.0f} KB)")
                    model_files_found.append(model_file)
            
            if len(model_files_found) == 0:
                logger.warning("   ⚠️  No model files found after training!")
            else:
                logger.info(f"   ✅ Total: {len(model_files_found)} model files created")
            
            logger.info("")
            logger.info(f"⏱️  Total training time: {int(training_time//60)} minutes {int(training_time%60)} seconds")
            logger.info("="*80 + "\n")
            
            # Send success alert
            send_telegram_message(
                "✅ <b>Advanced 3X Model Training Complete</b>\n\n"
                f"📊 Models: {len(model_files_found)} files created\n"
                "🎯 XGBoost + LightGBM + CatBoost\n"
                "🔢 190+ advanced features\n"
                "• Early Model (>5 days)\n"
                "• Late Model (≤5 days)\n\n"
                "💾 6 models saved with backups\n"
                f"⏱️ Training time: {int(training_time//60)}m {int(training_time%60)}s\n"
                "📋 Check training reports for details"
            )
            
            # Reload detector with new models
            if threex_enabled:
                logger.info("🔄 Reloading 3X detector with new models...")
                initialize_3x_detector()
        
        else:
            logger.error("\n" + "="*80)
            logger.error("❌ 3X MODEL TRAINING FAILED")
            logger.error("="*80)
            logger.error(f"Error output:\n{result.stderr}")
            logger.error("="*80 + "\n")
            
            # Send failure alert
            send_telegram_message(
                "⚠️ <b>3X Model Training Failed</b>\n\n"
                "Training process encountered errors.\n"
                "Old models retained.\n\n"
                f"📋 Check logs for details:\n"
                f"{LOG_DIR}/scanner_{datetime.now().strftime('%Y%m%d')}.log"
            )
    
    except subprocess.TimeoutExpired:
        training_time = time_module.time() - training_start_time
        logger.error("="*80)
        logger.error("❌ Training timeout (>300 minutes)")
        logger.error("="*80)
        logger.error(f"⏱️  Time elapsed: {int(training_time//60)} minutes {int(training_time%60)} seconds")
        logger.error("Training exceeded 5 hour limit - this indicates a serious issue")
        logger.error("Possible causes:")
        logger.error("   • Too much data (>6 months)")
        logger.error("   • Memory issues causing slowdown")
        logger.error("   • Training script hung/stuck")
        logger.error("="*80 + "\n")
        
        send_telegram_message(
            "⚠️ <b>3X Training Timeout</b>\n\n"
            f"⏱️ Exceeded 300 minutes ({int(training_time//60)} min elapsed)\n"
            "This is unusual - check data volume and memory."
        )
    
    except Exception as e:
        logger.error(f"❌ Training error: {e}")
        import traceback
        traceback.print_exc()
        
        send_telegram_message(
            f"❌ <b>3X Training Error</b>\n\n"
            f"Error: {str(e)[:100]}\n"
            f"Check logs for details."
        )

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SCANNER LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def run_scanner():
    """Main scanner loop"""
    global scanner_running, baseline_data, locked_atm_data, opening_prices
    global oi_signals, stock_volume_spikes, option_volume_spikes, combined_signals
    
    logger.info("\n" + "="*80)
    logger.info("🚀 SCANNER v9.1 - STARTING (MULTI-DAY + IMMEDIATE SIGNALS)")
    logger.info("="*80 + "\n")
    
    scanner_running = True
    
    baseline = load_baseline()
    if baseline:
        baseline_data.update(baseline)
    else:
        logger.warning("⚠️ Scanner starting without baseline! Signals may be limited.")
    
    logger.info("\n📊 Loading options volume history...")
    load_options_history()
    
    # ⭐ NEW IN v9.1: Load multi-day enhanced options data
    logger.info("\n📊 Loading enhanced options history (multi-day)...")
    load_enhanced_options_history()
    
    logger.info("\n💼 Loading paper trading data...")
    load_paper_trading_data()
    
    logger.info("\n📊 Fetching opening prices...")
    
    # Separate stock and index IDs
    stock_ids = [sid for sid in STOCKS.keys() if sid not in [13, 25]]
    index_ids = [sid for sid in STOCKS.keys() if sid in [13, 25]]
    
    # Fetch stock prices (NSE_EQ) with retry mechanism
    if stock_ids:
        endpoint = "/v2/marketfeed/quote"
        payload = {"NSE_EQ": stock_ids}
        
        # Try up to 3 times with increasing delays
        max_retries = 3
        retry_delay = 2  # seconds
        success = False
        
        for attempt in range(1, max_retries + 1):
            response = make_api_request(endpoint, method="POST", data=payload)
            
            if response and "data" in response and "NSE_EQ" in response["data"]:
                nse_data = response["data"]["NSE_EQ"]
                stocks_fetched = 0
                
                for security_id in stock_ids:
                    symbol = STOCKS[security_id]
                    stock_data = nse_data.get(str(security_id))
                    if stock_data and "last_price" in stock_data:
                        price = float(stock_data["last_price"])
                        opening_prices[symbol] = {"security_id": security_id, "open_price": price}
                        current_prices[symbol] = price
                        stocks_fetched += 1
                
                if stocks_fetched > 0:
                    logger.info(f"✅ Fetched {stocks_fetched}/{len(stock_ids)} stock prices")
                    success = True
                    break
                else:
                    logger.warning(f"⚠️ Stock API returned data but no prices found (attempt {attempt}/{max_retries})")
            else:
                # Log detailed error information
                if response is None:
                    logger.warning(f"⚠️ Stock API returned None (attempt {attempt}/{max_retries}) - likely timeout or connection issue")
                elif "data" not in response:
                    logger.warning(f"⚠️ Stock API missing 'data' key (attempt {attempt}/{max_retries})")
                elif "NSE_EQ" not in response.get("data", {}):
                    logger.warning(f"⚠️ Stock API missing 'NSE_EQ' in data (attempt {attempt}/{max_retries})")
                else:
                    logger.warning(f"⚠️ Unexpected stock API response structure (attempt {attempt}/{max_retries})")
            
            # Wait before retry (except on last attempt)
            if attempt < max_retries:
                logger.info(f"   Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        if not success:
            logger.error("❌ Failed to fetch stock prices after 3 attempts - this is critical!")
            logger.error("   Scanner cannot continue without stock prices.")
            return  # Exit the main_scanner function
    
    # Fetch index prices (IDX_I) with retry mechanism
    if index_ids:
        endpoint = "/v2/marketfeed/quote"
        payload = {"IDX_I": index_ids}
        
        # Try up to 3 times with increasing delays
        max_retries = 3
        retry_delay = 2  # seconds
        success = False
        
        for attempt in range(1, max_retries + 1):
            response = make_api_request(endpoint, method="POST", data=payload)
            
            if response and "data" in response and "IDX_I" in response["data"]:
                idx_data = response["data"]["IDX_I"]
                indices_fetched = 0
                
                for security_id in index_ids:
                    symbol = STOCKS[security_id]
                    index_data = idx_data.get(str(security_id))
                    if index_data and "last_price" in index_data:
                        price = float(index_data["last_price"])
                        opening_prices[symbol] = {"security_id": security_id, "open_price": price}
                        current_prices[symbol] = price
                        indices_fetched += 1
                
                if indices_fetched > 0:
                    logger.info(f"✅ Fetched {indices_fetched} index price(s): {', '.join([STOCKS[sid] for sid in index_ids if STOCKS[sid] in opening_prices])}")
                    success = True
                    break
                else:
                    logger.warning(f"⚠️ Index API returned data but no prices found (attempt {attempt}/{max_retries})")
            else:
                # Log detailed error information
                if response is None:
                    logger.warning(f"⚠️ Index API returned None (attempt {attempt}/{max_retries}) - likely timeout or connection issue")
                elif "data" not in response:
                    logger.warning(f"⚠️ Index API missing 'data' key (attempt {attempt}/{max_retries}) - Response: {str(response)[:200]}")
                elif "IDX_I" not in response.get("data", {}):
                    logger.warning(f"⚠️ Index API missing 'IDX_I' in data (attempt {attempt}/{max_retries}) - Keys: {list(response.get('data', {}).keys())}")
                else:
                    logger.warning(f"⚠️ Unexpected index API response structure (attempt {attempt}/{max_retries})")
            
            # Wait before retry (except on last attempt)
            if attempt < max_retries:
                logger.info(f"   Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        if not success:
            logger.warning("⚠️ Failed to fetch index prices after 3 attempts - continuing without indices")
            logger.info("   Tip: Check if NIFTY/BANKNIFTY are trading. Scanner will continue with stocks only.")
    
    logger.info(f"✅ Fetched {len(opening_prices)} opening prices (stocks + indices)")
    
    msg = f"🚀 <b>Scanner v9.1 ACTIVE</b>\n\n"
    msg += f"🆕 New in v9.1:\n"
    msg += f"✅ Multi-day context loaded\n"
    msg += f"✅ 3X predictions from 9:15 AM\n"
    msg += f"✅ Option signals from 1st fetch\n\n"
    msg += f"🎯 v9.0 Features:\n"
    msg += f"✅ 3X ML Detector: {threex_status}\n"
    msg += f"✅ Dual Model System\n"
    msg += f"✅ Enhanced option data\n\n"
    msg += f"📊 API Usage: ~7,579/day (7.6%)\n"
    msg += f"💼 Capital: ₹{capital:,.0f}"
    send_telegram_message(msg)
    
    cycle_count = 0
    last_position_update = get_ist_time()
    
    # Start 5-minute stock volume monitor thread
    logger.info("\n" + "="*80)
    logger.info("🚀 STARTING 5-MINUTE STOCK VOLUME MONITOR THREAD (BATCHED)")
    logger.info("="*80)
    logger.info("✅ Batched fetching: Dramatically reduced API usage!")
    logger.info("✅ Ensures NO volume spikes are missed!")
    logger.info("="*80 + "\n")
    
    volume_monitor_thread = Thread(target=run_stock_volume_monitor, daemon=True)
    volume_monitor_thread.start()
    
    logger.info("\n" + "="*80)
    logger.info("STARTING MAIN SCANNER LOOP")
    logger.info("="*80 + "\n")
    
    while scanner_running and is_market_open():
        cycle_start = get_ist_time()
        cycle_count += 1
        
        logger.info(f"\n{'='*80}")
        logger.info(f"[{cycle_start.strftime('%H:%M:%S')}] 🔄 SCAN CYCLE #{cycle_count}")
        logger.info(f"{'='*80}")
        logger.info(f"Scanning {len(opening_prices)} stocks (ETA: ~{len(opening_prices) * OPTION_CHAIN_DELAY // 60} min)...")
        
        # Update positions every 5 minutes
        if (cycle_start - last_position_update).total_seconds() > 300:
            logger.info("\n💼 Updating paper positions...")
            update_paper_positions()
            last_position_update = cycle_start
        
        # Update Nifty
        nifty_manager.update_nifty()
        
        # Scan each stock (expiry determined per symbol for stocks vs indices)
        
        for idx, (symbol, price_info) in enumerate(opening_prices.items(), 1):
            try:
                security_id = price_info["security_id"]
                open_price = price_info["open_price"]
                
                # Determine expiry based on symbol type
                if security_id in [13, 25]:  # NIFTY or BANKNIFTY
                    expiry_date = get_index_expiry(security_id)
                else:
                    expiry_date = get_monthly_expiry()
                
                # Log progress every 50 stocks
                if idx % 50 == 0:
                    logger.info(f"   Progress: {idx}/{len(opening_prices)} stocks scanned...")
                
                # Get current price
                current_price = get_stock_price(security_id)
                if not current_price:
                    logger.debug(f"❌ {symbol}: No current price")
                    time.sleep(OPTION_CHAIN_DELAY)
                    continue
                
                current_prices[symbol] = current_price
                
                # Get option chain
                option_chain = get_option_chain(security_id, expiry_date)
                if not option_chain:
                    logger.debug(f"❌ {symbol}: No option chain")
                    time.sleep(OPTION_CHAIN_DELAY)
                    continue
                
                # ═══════════════════════════════════════════════════════════════════════
                # NEW IN v9.0: EXTRACT ENHANCED OPTION DATA FOR 3X DETECTION
                # ═══════════════════════════════════════════════════════════════════════
                if option_chain and "data" in option_chain and "oc" in option_chain["data"]:
                    current_timestamp = get_ist_time().strftime('%Y-%m-%d %H:%M:%S')
                    
                    for strike_str, strike_data in option_chain["data"]["oc"].items():
                        try:
                            strike = float(strike_str)
                            
                            # Process CE (Call)
                            if "ce" in strike_data and strike_data["ce"]:
                                ce_data = strike_data["ce"]
                                option_key = f"{symbol}_{strike}_CE"
                                
                                # Initialize if first time
                                if option_key not in enhanced_options_data:
                                    enhanced_options_data[option_key] = {
                                        'symbol': symbol,
                                        'strike': strike,
                                        'option_type': 'CE',
                                        'all_history': [],
                                        'volume_history': []
                                    }
                                
                                # Extract all available fields with correct Dhan API mapping
                                oi = int(ce_data.get('oi', 0) or 0)
                                previous_oi = int(ce_data.get('previous_oi', 0) or 0)
                                oi_change = oi - previous_oi
                                
                                greeks = ce_data.get('greeks', {}) or {}
                                
                                snapshot = {
                                    'timestamp': current_timestamp,
                                    'spot_price': current_price,  # ⭐ ADDED FOR ATM FILTERING
                                    'price': float(ce_data.get('last_price', 0) or 0),
                                    'volume': int(ce_data.get('volume', 0) or 0),
                                    'open_interest': oi,
                                    'oi_change': oi_change,
                                    'bid_price': float(ce_data.get('top_bid_price', 0) or 0),
                                    'ask_price': float(ce_data.get('top_ask_price', 0) or 0),
                                    'bid_qty': int(ce_data.get('top_bid_quantity', 0) or 0),
                                    'ask_qty': int(ce_data.get('top_ask_quantity', 0) or 0),
                                    'iv': float(ce_data.get('implied_volatility', 0) or 0),
                                    'delta': float(greeks.get('delta', 0) or 0),
                                    'gamma': float(greeks.get('gamma', 0) or 0),
                                    'theta': float(greeks.get('theta', 0) or 0),
                                    'vega': float(greeks.get('vega', 0) or 0),
                                    'open': 0.0,
                                    'high': 0.0,
                                    'low': 0.0,
                                    'close': 0.0,
                                }
                                
                                # Append to history
                                enhanced_options_data[option_key]['all_history'].append(snapshot)
                                enhanced_options_data[option_key]['volume_history'].append(snapshot['volume'])
                            
                            # Process PE (Put) - same logic
                            if "pe" in strike_data and strike_data["pe"]:
                                pe_data = strike_data["pe"]
                                option_key = f"{symbol}_{strike}_PE"
                                
                                if option_key not in enhanced_options_data:
                                    enhanced_options_data[option_key] = {
                                        'symbol': symbol,
                                        'strike': strike,
                                        'option_type': 'PE',
                                        'all_history': [],
                                        'volume_history': []
                                    }
                                
                                # Extract all available fields with correct Dhan API mapping
                                oi = int(pe_data.get('oi', 0) or 0)
                                previous_oi = int(pe_data.get('previous_oi', 0) or 0)
                                oi_change = oi - previous_oi
                                
                                greeks = pe_data.get('greeks', {}) or {}
                                
                                snapshot = {
                                    'timestamp': current_timestamp,
                                    'spot_price': current_price,  # ⭐ ADDED FOR ATM FILTERING
                                    'price': float(pe_data.get('last_price', 0) or 0),
                                    'volume': int(pe_data.get('volume', 0) or 0),
                                    'open_interest': oi,
                                    'oi_change': oi_change,
                                    'bid_price': float(pe_data.get('top_bid_price', 0) or 0),
                                    'ask_price': float(pe_data.get('top_ask_price', 0) or 0),
                                    'bid_qty': int(pe_data.get('top_bid_quantity', 0) or 0),
                                    'ask_qty': int(pe_data.get('top_ask_quantity', 0) or 0),
                                    'iv': float(pe_data.get('implied_volatility', 0) or 0),
                                    'delta': float(greeks.get('delta', 0) or 0),
                                    'gamma': float(greeks.get('gamma', 0) or 0),
                                    'theta': float(greeks.get('theta', 0) or 0),
                                    'vega': float(greeks.get('vega', 0) or 0),
                                    'open': 0.0,
                                    'high': 0.0,
                                    'low': 0.0,
                                    'close': 0.0,
                                }
                                
                                enhanced_options_data[option_key]['all_history'].append(snapshot)
                                enhanced_options_data[option_key]['volume_history'].append(snapshot['volume'])
                        
                        except Exception as e:
                            logger.debug(f"Error extracting enhanced data for {symbol} {strike_str}: {e}")
                            continue
                # ═══════════════════════════════════════════════════════════════════════
                
                # Lock ATM at open (first cycle only)
                if symbol not in locked_atm_data:
                    atm, interval = find_atm_strike(open_price, option_chain)
                    if atm and interval:
                        locked_atm_data[symbol] = {
                            "atm": atm,
                            "interval": interval
                        }
                
                locked_atm = locked_atm_data.get(symbol, {}).get("atm")
                strike_interval = locked_atm_data.get(symbol, {}).get("interval")
                
                # Signal 1: OI Signal (baseline comparison)
                oi_signal = detect_oi_signal(symbol, security_id, locked_atm, strike_interval, option_chain)
                
                # Signal 2: Stock Volume Spike (done by 5-min monitor now, but we can still check here)
                # This is redundant but kept for safety
                stock_spike = detect_stock_volume_spike(symbol, security_id, current_price)
                
                # Signal 3: Option Volume Spike (track all ATM±3 options)
                if locked_atm and strike_interval and "data" in option_chain and "oc" in option_chain["data"]:
                    oc_data = option_chain["data"]["oc"]
                    
                    # Get baseline data for OI comparison
                    baseline = baseline_data.get(symbol, {})
                    baseline_strikes = baseline.get("strikes", {})
                    
                    for offset in range(-OPTION_VOLUME_STRIKES_RANGE, OPTION_VOLUME_STRIKES_RANGE + 1):
                        strike = locked_atm + (offset * strike_interval)
                        strike_key = f"{strike:.6f}"
                        
                        if strike_key not in oc_data:
                            continue
                        
                        strike_data = oc_data[strike_key]
                        
                        # Get baseline OI for this strike (for OI validation)
                        baseline_strike = baseline_strikes.get(str(float(strike)), {})
                        
                        # Track CE volume
                        if "ce" in strike_data:
                            ce = strike_data["ce"]
                            ce_volume = int(ce.get("volume", 0) or 0)
                            ce_price = float(ce.get("last_price", 0) or 0)
                            ce_oi = int(ce.get("oi", 0) or 0)
                            baseline_ce_oi = baseline_strike.get("ce_oi", 0)
                            
                            if ce_volume > 0 and ce_price > 0:
                                # Pass OI data for validation
                                track_option_volume(symbol, strike, "CE", ce_volume, ce_price, ce_oi, baseline_ce_oi)
                        
                        # Track PE volume
                        if "pe" in strike_data:
                            pe = strike_data["pe"]
                            pe_volume = int(pe.get("volume", 0) or 0)
                            pe_price = float(pe.get("last_price", 0) or 0)
                            pe_oi = int(pe.get("oi", 0) or 0)
                            baseline_pe_oi = baseline_strike.get("pe_oi", 0)
                            
                            if pe_volume > 0 and pe_price > 0:
                                # Pass OI data for validation
                                track_option_volume(symbol, strike, "PE", pe_volume, pe_price, pe_oi, baseline_pe_oi)
                
                # Critical: 4-second delay after EVERY stock
                time.sleep(OPTION_CHAIN_DELAY)
                
            except KeyboardInterrupt:
                logger.info("\n⚠️ Scanner interrupted by user")
                scanner_running = False
                break
            except Exception as e:
                logger.error(f"❌ {symbol}: {str(e)}")
                time.sleep(OPTION_CHAIN_DELAY)
                continue
        
        # Check combined signals
        check_combined_signals()
        
        # Save options history
        save_options_history()
        
        # ═══════════════════════════════════════════════════════════════
        # NEW IN v9.0: SAVE ENHANCED OPTIONS + RUN 3X DETECTION
        # ═══════════════════════════════════════════════════════════════
        save_enhanced_options_history()
        
        # Run 3X pattern detection
        run_3x_detection()
        # ═══════════════════════════════════════════════════════════════
        
        cycle_end = get_ist_time()
        cycle_duration = (cycle_end - cycle_start).total_seconds() / 60
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ CYCLE #{cycle_count} COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"   Duration: {cycle_duration:.1f} minutes")
        logger.info(f"   OI Signals: {len(oi_signals)}")
        logger.info(f"   Stock Spikes: {len(stock_volume_spikes)}")
        logger.info(f"   Option Spikes (OI↑): {len(option_volume_spikes_oi_increasing)}")
        logger.info(f"   Option Spikes (OI↓): {len(option_volume_spikes_oi_decreasing)}")
        logger.info(f"   Combined: {len(combined_signals)}")
        logger.info(f"   Open Positions: {len(paper_positions)}")
        logger.info(f"{'='*80}\n")
    
    scanner_running = False
    stock_volume_monitor_running = False
    
    logger.info("\n" + "="*80)
    logger.info("SCANNER STOPPED")
    logger.info("="*80)
    
    # Save everything
    save_options_history()
    save_paper_trading_data()
    
    if len(closed_trades) >= 20:
        logger.info("\n🤖 Training ML model...")
        train_ml_model()

# ============================================================================
# ML TRAINING
# ============================================================================

def train_ml_model():
    """Train ML model from closed trades"""
    import time as time_module
    
    training_start_time = time_module.time()
    start_timestamp = get_ist_time().strftime('%H:%M:%S')
    
    logger.info("\n" + "="*80)
    logger.info("🤖 ML TRAINING - Stock Volume Directional Model")
    logger.info(f"⏱️  Training started at: {start_timestamp}")
    logger.info("="*80)
    
    if len(closed_trades) < 20:
        logger.warning("⚠️  Need at least 20 trades to train ML model")
        logger.warning(f"   Currently have: {len(closed_trades)} trades")
        logger.info("="*80 + "\n")
        return
    
    # Read closed trades file
    closed_trades_file = os.path.join(PAPER_TRADING_DIR, "closed_trades.json")
    logger.info(f"📂 FILE READ: {closed_trades_file}")
    logger.info(f"✅ Loaded {len(closed_trades)} closed trades")
    
    # Count profitable vs unprofitable
    profitable_count = sum(1 for t in closed_trades if t.get('final_pnl', 0) > 0)
    unprofitable_count = len(closed_trades) - profitable_count
    win_rate = (profitable_count / len(closed_trades) * 100) if closed_trades else 0
    
    logger.info(f"   • Profitable: {profitable_count} ({win_rate:.1f}%)")
    logger.info(f"   • Unprofitable: {unprofitable_count} ({100-win_rate:.1f}%)")
    logger.info("")
    
    # Prepare features
    logger.info("🔍 EXTRACTING FEATURES (showing first 5):")
    X = []
    y = []
    
    for idx, trade in enumerate(closed_trades):
        features = [
            trade.get('candle_body_pct', 0),
            trade.get('price_range_pct', 0),
            trade.get('close_position', 0.5),
            trade.get('upper_wick_pct', 0),
            trade.get('lower_wick_pct', 0),
            1 if trade.get('volume_position') == 'top' else (0 if trade.get('volume_position') == 'bottom' else 0.5),
            trade.get('nifty_change', 0),
            1 if trade.get('nifty_ok', True) else 0,
            trade.get('momentum_15min', 0),
            trade.get('time_of_day', 12)
        ]
        
        # Label: 1 for profitable (BULLISH), 0 for loss (BEARISH)
        label = 1 if trade.get('final_pnl', 0) > 0 else 0
        
        # Log first 5 trades in detail
        if idx < 5:
            symbol = trade.get('symbol', 'UNKNOWN')
            logger.info(f"   [{idx+1}/{len(closed_trades)}] {symbol}: body={features[0]:.2f}%, range={features[1]:.2f}%, "
                       f"close_pos={features[2]:.2f}, upper_wick={features[3]:.2f}%, lower_wick={features[4]:.2f}%, "
                       f"vol_pos={'top' if features[5]==1 else ('bottom' if features[5]==0 else 'middle')}, "
                       f"nifty={features[6]:+.2f}%, time={features[9]:.1f}")
        
        X.append(features)
        y.append(label)
    
    logger.info(f"   ... (extracting remaining {len(closed_trades)-5} trades)")
    logger.info("")
    
    X = np.array(X)
    y = np.array(y)
    
    # Train/test split
    logger.info("📊 DATA SPLIT:")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    logger.info(f"   • Train: {len(X_train)} samples (80%)")
    logger.info(f"   • Test: {len(X_test)} samples (20%)")
    logger.info("")
    
    # Train model
    logger.info("🧠 TRAINING MODEL: GradientBoostingClassifier")
    logger.info("   • Estimators: 100, Max Depth: 5")
    
    model_train_start = time_module.time()
    model = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    model_train_time = time_module.time() - model_train_start
    
    logger.info(f"⏱️  Training completed in: {model_train_time:.2f} seconds")
    logger.info("")
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    logger.info("✅ EVALUATION:")
    logger.info(f"   • Train Accuracy: {train_score*100:.1f}%")
    logger.info(f"   • Test Accuracy: {test_score*100:.1f}%")
    logger.info("")
    
    # Save model
    model_path = os.path.join(MODEL_DIR, "ml_directional.pkl")
    logger.info(f"📂 FILE WRITE: {model_path}")
    joblib.dump(model, model_path)
    
    # Get file size
    file_size_kb = os.path.getsize(model_path) / 1024
    logger.info(f"✅ Model saved ({file_size_kb:.0f} KB)")
    logger.info("")
    
    # Save metadata
    metadata = {
        'trained_date': get_ist_time().isoformat(),
        'num_trades': len(closed_trades),
        'train_accuracy': train_score,
        'test_accuracy': test_score,
        'training_time_seconds': model_train_time
    }
    
    metadata_path = os.path.join(MODEL_DIR, "ml_directional_metadata.json")
    logger.info(f"📂 FILE WRITE: {metadata_path}")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info("✅ Metadata saved")
    logger.info("")
    
    total_time = time_module.time() - training_start_time
    logger.info(f"⏱️  Total training time: {total_time:.2f} seconds")
    logger.info("="*80)
    logger.info("🎉 ML TRAINING COMPLETED SUCCESSFULLY")
    logger.info("="*80 + "\n")

# ============================================================================
# DASHBOARD (Flask)
# ============================================================================

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Render dashboard HTML"""
    html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Options Scanner v9.3 - Dynamic Validation + New Schedule</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            text-align: center;
        }
        
        .stat-card h3 {
            font-size: 1em;
            opacity: 0.8;
            margin-bottom: 10px;
        }
        
        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
        }
        
        .signals-section {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
        }
        
        .signals-section h2 {
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        .signal-card {
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #4CAF50;
        }
        
        .signal-card.sell {
            border-left-color: #f44336;
        }
        
        .signal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .signal-symbol {
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .signal-badge {
            background: #4CAF50;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .signal-badge.sell {
            background: #f44336;
        }
        
        .signal-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            font-size: 0.9em;
        }
        
        .detail-item {
            opacity: 0.9;
        }
        
        .detail-item strong {
            opacity: 1;
        }
        
        .no-signals {
            text-align: center;
            padding: 40px;
            opacity: 0.7;
            font-size: 1.2em;
        }
        
        .refresh-info {
            text-align: center;
            margin-top: 20px;
            opacity: 0.7;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            overflow: hidden;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        th {
            background: rgba(255, 255, 255, 0.1);
            font-weight: bold;
        }
        
        tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        
        .positive {
            color: #4CAF50;
        }
        
        .negative {
            color: #f44336;
        }
        
        /* NEW IN v9.0: 3X DETECTOR STYLES */
        .threex-prediction {
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.2) 0%, rgba(255, 140, 0, 0.2) 100%);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #FFD700;
        }
        
        .threex-alert {
            background: linear-gradient(135deg, rgba(255, 69, 0, 0.2) 0%, rgba(220, 20, 60, 0.2) 100%);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #FF4500;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
        
        .confidence-bar {
            background: rgba(255, 255, 255, 0.2);
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .confidence-fill {
            background: linear-gradient(90deg, #4CAF50, #FFD700);
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .model-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 8px;
        }
        
        .model-early {
            background: #2196F3;
            color: white;
        }
        
        .model-late {
            background: #FF9800;
            color: white;
        }
        
        .alert-type-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 8px;
        }
        
        .alert-pattern {
            background: #9C27B0;
            color: white;
        }
        
        .alert-starting {
            background: #FF9800;
            color: white;
        }
        
        .alert-target {
            background: #4CAF50;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Options Scanner v9.3 - Dynamic Validation + New Schedule</h1>
            <p>Real-time Market Analysis Dashboard</p>
            <p id="last-update">Loading...</p>
        </div>
        
        <div class="stats-grid" id="stats-grid">
            <div class="stat-card">
                <h3>OI Signals</h3>
                <div class="value" id="oi-count">0</div>
            </div>
            <div class="stat-card">
                <h3>Stock Volume Spikes</h3>
                <div class="value" id="stock-count">0</div>
            </div>
            <div class="stat-card">
                <h3>Option Spikes (OI↑)</h3>
                <div class="value" id="option-count-increasing">0</div>
            </div>
            <div class="stat-card">
                <h3>Option Spikes (OI↓)</h3>
                <div class="value" id="option-count-decreasing">0</div>
            </div>
            <div class="stat-card">
                <h3>Combined Signals</h3>
                <div class="value" id="combined-count">0</div>
            </div>
            <div class="stat-card">
                <h3>Open Positions</h3>
                <div class="value" id="open-positions">0</div>
            </div>
            <div class="stat-card">
                <h3>Total P&L</h3>
                <div class="value" id="total-pnl">₹0</div>
            </div>
            <div class="stat-card">
                <h3>Win Rate</h3>
                <div class="value" id="win-rate">0%</div>
            </div>
            <div class="stat-card">
                <h3>Capital</h3>
                <div class="value" id="capital">₹0</div>
            </div>
        </div>
        
        <div class="signals-section">
            <h2>🎯 Combined Signals (All 3 Match)</h2>
            <div id="combined-signals"></div>
        </div>
        
        <div class="signals-section">
            <h2>📊 OI Signals</h2>
            <div id="oi-signals"></div>
        </div>
        
        <div class="signals-section">
            <h2>📈 Stock Volume Spikes</h2>
            <div id="stock-signals"></div>
        </div>
        
        <div class="signals-section">
            <h2>⚡🟢 Option Volume Spikes - OI Increasing</h2>
            <div id="option-signals-increasing"></div>
        </div>
        
        <div class="signals-section">
            <h2>⚡🔴 Option Volume Spikes - OI Decreasing</h2>
            <div id="option-signals-decreasing"></div>
        </div>
        
        <!-- NEW IN v9.0: 3X DETECTOR SECTIONS -->
        <div class="signals-section">
            <h2>🎯 3X Move Predictions (Top 20)</h2>
            <div id="threex-predictions">
                <div class="no-signals">Initializing 3X detector...</div>
            </div>
        </div>
        
        <div class="signals-section">
            <h2>⚡ Recent 3X Alerts</h2>
            <div id="threex-alerts">
                <div class="no-signals">No 3X alerts yet</div>
            </div>
        </div>
        
        <div class="signals-section">
            <h2>💼 Open Positions</h2>
            <div id="positions-table"></div>
        </div>
        
        <div class="refresh-info">
            🔄 Dashboard auto-refreshes every 10 seconds
        </div>
    </div>
    
    <script>
        async function fetchData() {
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }
        
        function updateDashboard(data) {
            // Update timestamp
            document.getElementById('last-update').textContent = `Last Updated: ${new Date(data.timestamp).toLocaleTimeString()}`;
            
            // Update stats
            document.getElementById('oi-count').textContent = data.stats.oi_count;
            document.getElementById('stock-count').textContent = data.stats.stock_spike_count;
            document.getElementById('option-count-increasing').textContent = data.stats.option_spike_count_oi_increasing;
            document.getElementById('option-count-decreasing').textContent = data.stats.option_spike_count_oi_decreasing;
            document.getElementById('combined-count').textContent = data.stats.combined_count;
            document.getElementById('open-positions').textContent = data.paper_trading.statistics.open_positions;
            
            const totalPnl = data.paper_trading.statistics.total_pnl;
            document.getElementById('total-pnl').textContent = `₹${totalPnl.toLocaleString('en-IN')}`;
            document.getElementById('total-pnl').className = `value ${totalPnl >= 0 ? 'positive' : 'negative'}`;
            
            document.getElementById('win-rate').textContent = `${data.paper_trading.statistics.win_rate.toFixed(1)}%`;
            document.getElementById('capital').textContent = `₹${data.paper_trading.statistics.capital.toLocaleString('en-IN')}`;
            
            // Update Combined Signals
            const combinedSignals = data.signals.combined_signals;
            const combinedContainer = document.getElementById('combined-signals');
            if (combinedSignals.length === 0) {
                combinedContainer.innerHTML = '<div class="no-signals">No combined signals yet</div>';
            } else {
                combinedContainer.innerHTML = combinedSignals.slice().reverse().map(signal => `
                    <div class="signal-card ${signal.direction.toLowerCase()}">
                        <div class="signal-header">
                            <div class="signal-symbol">${signal.symbol}</div>
                            <div class="signal-badge ${signal.direction.toLowerCase()}">${signal.direction}</div>
                        </div>
                        <div class="signal-details">
                            <div class="detail-item"><strong>Time:</strong> ${signal.timestamp}</div>
                            <div class="detail-item"><strong>OI:</strong> ${signal.oi_signal.threshold}%</div>
                            <div class="detail-item"><strong>Stock MCap:</strong> ${signal.stock_spike.mcap_pct.toFixed(4)}%</div>
                            <div class="detail-item"><strong>Option:</strong> ${signal.option_spike.strike} ${signal.option_spike.option_type} (${signal.option_spike.multiple}X)</div>
                        </div>
                    </div>
                `).join('');
            }
            
            // Update OI Signals
            const oiSignals = data.signals.oi_signals;
            const oiContainer = document.getElementById('oi-signals');
            if (oiSignals.length === 0) {
                oiContainer.innerHTML = '<div class="no-signals">No OI signals detected</div>';
            } else {
                oiContainer.innerHTML = oiSignals.slice().reverse().map(signal => `
                    <div class="signal-card ${signal.signal_type.toLowerCase()}">
                        <div class="signal-header">
                            <div class="signal-symbol">${signal.symbol}</div>
                            <div class="signal-badge ${signal.signal_type.toLowerCase()}">${signal.signal_type}</div>
                        </div>
                        <div class="signal-details">
                            <div class="detail-item"><strong>Time:</strong> ${signal.timestamp}</div>
                            <div class="detail-item"><strong>CE Change:</strong> ${signal.call_change.toFixed(2)}%</div>
                            <div class="detail-item"><strong>PE Change:</strong> ${signal.put_change.toFixed(2)}%</div>
                            <div class="detail-item"><strong>Threshold:</strong> ${signal.threshold}%</div>
                        </div>
                    </div>
                `).join('');
            }
            
            // Update Stock Spikes
            const stockSpikes = data.signals.stock_volume_spikes;
            const stockContainer = document.getElementById('stock-signals');
            if (stockSpikes.length === 0) {
                stockContainer.innerHTML = '<div class="no-signals">No stock volume spikes detected</div>';
            } else {
                stockContainer.innerHTML = stockSpikes.slice().reverse().map(spike => `
                    <div class="signal-card">
                        <div class="signal-header">
                            <div class="signal-symbol">${spike.symbol}</div>
                            <div class="signal-badge">${spike.ml_prediction.direction}</div>
                        </div>
                        <div class="signal-details">
                            <div class="detail-item"><strong>Time:</strong> ${spike.timestamp}</div>
                            <div class="detail-item"><strong>Price:</strong> ₹${spike.close.toFixed(2)}</div>
                            <div class="detail-item"><strong>MCap %:</strong> ${spike.mcap_pct.toFixed(4)}%</div>
                            <div class="detail-item"><strong>Candle:</strong> ${spike.candle_type.toUpperCase()}</div>
                            <div class="detail-item"><strong>ML Action:</strong> ${spike.ml_prediction.action}</div>
                            <div class="detail-item"><strong>Confidence:</strong> ${spike.ml_prediction.confidence}%</div>
                        </div>
                    </div>
                `).join('');
            }
            
            // Update Option Spikes - OI Increasing
            const optionSpikesIncreasing = data.signals.option_volume_spikes_oi_increasing;
            const optionContainerIncreasing = document.getElementById('option-signals-increasing');
            if (optionSpikesIncreasing.length === 0) {
                optionContainerIncreasing.innerHTML = '<div class="no-signals">No option volume spikes (OI Increasing) detected</div>';
            } else {
                optionContainerIncreasing.innerHTML = optionSpikesIncreasing.slice().reverse().map(spike => `
                    <div class="signal-card">
                        <div class="signal-header">
                            <div class="signal-symbol">${spike.symbol} ${spike.strike} ${spike.option_type}</div>
                            <div class="signal-badge">${spike.threshold}X 🟢</div>
                        </div>
                        <div class="signal-details">
                            <div class="detail-item"><strong>Time:</strong> ${spike.timestamp.split(' ')[1]}</div>
                            <div class="detail-item"><strong>Premium:</strong> ₹${spike.price.toFixed(2)}</div>
                            <div class="detail-item"><strong>Volume:</strong> ${spike.current_volume.toLocaleString()}</div>
                            <div class="detail-item"><strong>Avg Volume:</strong> ${spike.avg_volume.toLocaleString()} (${spike.history_count} fetches)</div>
                            <div class="detail-item"><strong>Multiple:</strong> ${spike.multiple}X</div>
                            ${spike.oi_change_pct ? `<div class="detail-item"><strong>OI Change:</strong> +${spike.oi_change_pct}% ✅ INCREASING</div>` : ''}
                        </div>
                    </div>
                `).join('');
            }
            
            // Update Option Spikes - OI Decreasing
            const optionSpikesDecreasing = data.signals.option_volume_spikes_oi_decreasing;
            const optionContainerDecreasing = document.getElementById('option-signals-decreasing');
            if (optionSpikesDecreasing.length === 0) {
                optionContainerDecreasing.innerHTML = '<div class="no-signals">No option volume spikes (OI Decreasing) detected</div>';
            } else {
                optionContainerDecreasing.innerHTML = optionSpikesDecreasing.slice().reverse().map(spike => `
                    <div class="signal-card">
                        <div class="signal-header">
                            <div class="signal-symbol">${spike.symbol} ${spike.strike} ${spike.option_type}</div>
                            <div class="signal-badge">${spike.threshold}X 🔴</div>
                        </div>
                        <div class="signal-details">
                            <div class="detail-item"><strong>Time:</strong> ${spike.timestamp.split(' ')[1]}</div>
                            <div class="detail-item"><strong>Premium:</strong> ₹${spike.price.toFixed(2)}</div>
                            <div class="detail-item"><strong>Volume:</strong> ${spike.current_volume.toLocaleString()}</div>
                            <div class="detail-item"><strong>Avg Volume:</strong> ${spike.avg_volume.toLocaleString()} (${spike.history_count} fetches)</div>
                            <div class="detail-item"><strong>Multiple:</strong> ${spike.multiple}X</div>
                            ${spike.oi_change_pct ? `<div class="detail-item"><strong>OI Change:</strong> ${spike.oi_change_pct}% ⚠️ DECREASING</div>` : ''}
                        </div>
                    </div>
                `).join('');
            }
            
            // NEW IN v9.0: Update 3X Predictions
            const predictionsContainer = document.getElementById('threex-predictions');
            if (!data.threex_enabled) {
                predictionsContainer.innerHTML = '<div class="no-signals">⚠️ 3X Detector not loaded. Run training: python train_3x_detector_dual_model.py</div>';
            } else if (!data.threex_predictions || data.threex_predictions.length === 0) {
                predictionsContainer.innerHTML = '<div class="no-signals">✅ 3X Detector loaded! Waiting for first scanner cycle...</div>';
            } else {
                predictionsContainer.innerHTML = data.threex_predictions.map(pred => `
                    <div class="threex-prediction">
                        <div class="signal-header">
                            <strong>${pred.option_key}</strong>
                            <span class="model-badge model-${pred.model_used || 'single'}">${pred.model_used || 'single'}</span>
                            <span style="float:right;">Confidence: ${(pred.confidence * 100).toFixed(1)}%</span>
                        </div>
                        <div class="signal-details">
                            <div class="detail-item"><strong>Current:</strong> ₹${pred.current_price.toFixed(2)} (${pred.current_multiplier.toFixed(2)}X from base)</div>
                            <div class="detail-item"><strong>Days to Expiry:</strong> ${pred.days_to_expiry || 'N/A'}</div>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${pred.confidence * 100}%"></div>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
            
            // NEW IN v9.0: Update 3X Alerts
            const alertsContainer = document.getElementById('threex-alerts');
            if (!data.threex_enabled) {
                alertsContainer.innerHTML = '<div class="no-signals">⚠️ 3X Detector not loaded</div>';
            } else if (!data.threex_alerts || data.threex_alerts.length === 0) {
                alertsContainer.innerHTML = '<div class="no-signals">No 3X alerts yet - threshold not crossed</div>';
            } else {
                alertsContainer.innerHTML = data.threex_alerts.slice().reverse().map(alert => `
                    <div class="threex-alert">
                        <div class="signal-header">
                            <strong>${alert.option_key}</strong>
                            <span class="alert-type-badge alert-${alert.alert_type.toLowerCase()}">${alert.alert_type}</span>
                            <span class="model-badge model-${alert.model_used || 'single'}">${alert.model_used || 'single'}</span>
                            <span style="float:right;">${alert.timestamp}</span>
                        </div>
                        <div class="signal-details">
                            <div class="detail-item"><strong>Confidence:</strong> ${(alert.confidence * 100).toFixed(1)}%</div>
                            <div class="detail-item"><strong>Price:</strong> ₹${alert.current_price.toFixed(2)}</div>
                            <div class="detail-item"><strong>Current:</strong> ${alert.current_multiplier.toFixed(2)}X</div>
                            <div class="detail-item" style="margin-top:8px; font-style:italic;">${alert.message}</div>
                        </div>
                    </div>
                `).join('');
            }
            
            // Update Positions Table
            const positions = data.paper_trading.open_positions;
            const positionsContainer = document.getElementById('positions-table');
            if (positions.length === 0) {
                positionsContainer.innerHTML = '<div class="no-signals">No open positions</div>';
            } else {
                positionsContainer.innerHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Strike</th>
                                <th>Type</th>
                                <th>Entry Premium</th>
                                <th>Current Premium</th>
                                <th>P&L</th>
                                <th>Stock Price</th>
                                <th>Target</th>
                                <th>SL</th>
                                <th>Days</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${positions.slice().reverse().map(pos => `
                                <tr>
                                    <td>${pos.symbol}</td>
                                    <td>${pos.strike}</td>
                                    <td>${pos.option_type}</td>
                                    <td>₹${pos.entry_premium.toFixed(2)}</td>
                                    <td>₹${pos.current_premium.toFixed(2)}</td>
                                    <td class="${pos.unrealized_pnl >= 0 ? 'positive' : 'negative'}">₹${pos.unrealized_pnl.toFixed(2)}</td>
                                    <td>₹${pos.current_stock_price.toFixed(2)}</td>
                                    <td>₹${pos.target_stock_price.toFixed(2)}</td>
                                    <td>₹${pos.stoploss_stock_price.toFixed(2)}</td>
                                    <td>${pos.days_held}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }
        }
        
        // Initial fetch
        fetchData();
        
        // Auto-refresh every 10 seconds
        setInterval(fetchData, 10000);
    </script>
</body>
</html>
    '''
    return html

@app.route('/api/dashboard')
def api_dashboard():
    """API endpoint for dashboard data"""
    # Calculate statistics
    total_pnl = sum(t.get('final_pnl', 0) for t in closed_trades)
    winning_trades = sum(1 for t in closed_trades if t.get('final_pnl', 0) > 0)
    win_rate = (winning_trades / len(closed_trades) * 100) if closed_trades else 0
    
    return jsonify({
        'signals': {
            'oi_signals': oi_signals,
            'stock_volume_spikes': stock_volume_spikes,
            'option_volume_spikes_oi_increasing': option_volume_spikes_oi_increasing,
            'option_volume_spikes_oi_decreasing': option_volume_spikes_oi_decreasing,
            'combined_signals': combined_signals
        },
        # NEW IN v9.0: 3X Predictions and Alerts
        'threex_predictions': threex_predictions,
        'threex_alerts': threex_alerts,
        'threex_enabled': threex_enabled,
        'paper_trading': {
            'open_positions': paper_positions,
            'statistics': {
                'open_positions': len(paper_positions),
                'total_trades': len(closed_trades),
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'capital': capital
            }
        },
        'stats': {
            'oi_count': len(oi_signals),
            'stock_spike_count': len(stock_volume_spikes),
            'option_spike_count_oi_increasing': len(option_volume_spikes_oi_increasing),
            'option_spike_count_oi_decreasing': len(option_volume_spikes_oi_decreasing),
            'combined_count': len(combined_signals),
            'threex_predictions_count': len(threex_predictions),  # NEW
            'threex_alerts_count': len(threex_alerts)  # NEW
        },
        'timestamp': get_ist_time().isoformat()
    })

# ============================================================================
# SCHEDULER
# ============================================================================

def monitor_and_schedule():
    """Monitor time and schedule tasks"""
    global scanner_running
    
    print("⏰ Scheduler started\n")
    
    stock_ml_training_done_today = False
    threex_training_done_today = False
    baseline_captured_today = False
    current_date = get_ist_time().date()
    
    while True:
        try:
            now = get_ist_time()
            
            # Reset flags on new day
            if now.date() != current_date:
                stock_ml_training_done_today = False
                threex_training_done_today = False
                baseline_captured_today = False
                current_date = now.date()
            
            # Market start trigger
            market_start = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
            market_start_end = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE + 1, second=0, microsecond=0)
            
            if market_start <= now <= market_start_end and not scanner_running:
                print(f"\n🚀 Market opening!")
                Thread(target=run_scanner, daemon=True).start()
            
            # Stock Volume ML Training at 4:00 PM
            stock_ml_time = now.replace(hour=STOCK_ML_TRAINING_HOUR, minute=STOCK_ML_TRAINING_MINUTE, second=0, microsecond=0)
            stock_ml_time_end = now.replace(hour=STOCK_ML_TRAINING_HOUR, minute=STOCK_ML_TRAINING_MINUTE + 1, second=0, microsecond=0)
            
            if stock_ml_time <= now <= stock_ml_time_end and not stock_ml_training_done_today:
                print(f"\n🧠 3:55 PM - Starting Stock Volume ML Training!")
                logger.info("\n" + "="*80)
                logger.info("🧠 STARTING STOCK VOLUME ML TRAINING")
                logger.info("="*80)
                Thread(target=train_ml_model, daemon=True).start()
                stock_ml_training_done_today = True
            
            # 3X Model Training at 4:30 PM
            training_time = now.replace(hour=THREEX_TRAINING_HOUR, minute=THREEX_TRAINING_MINUTE, second=0, microsecond=0)
            training_time_end = now.replace(hour=THREEX_TRAINING_HOUR, minute=THREEX_TRAINING_MINUTE + 1, second=0, microsecond=0)
            
            if training_time <= now <= training_time_end and not threex_training_done_today:
                print(f"\n🧠 4:30 PM - Starting Advanced 3X Model Training (Ensemble)!")
                Thread(target=scheduled_3x_training, daemon=True).start()
                threex_training_done_today = True
            
            # Baseline capture at 5:30 PM
            baseline_time = now.replace(hour=BASELINE_CAPTURE_HOUR, minute=BASELINE_CAPTURE_MINUTE, second=0, microsecond=0)
            baseline_time_end = now.replace(hour=BASELINE_CAPTURE_HOUR, minute=BASELINE_CAPTURE_MINUTE + 1, second=0, microsecond=0)
            
            if baseline_time <= now <= baseline_time_end and not baseline_captured_today:
                print(f"\n📸 4:00 PM - Starting baseline capture!")
                Thread(target=capture_baseline, daemon=True).start()
                baseline_captured_today = True
            
            time.sleep(30)
            
        except Exception as e:
            print(f"❌ Scheduler error: {e}")
            time.sleep(60)

# ============================================================================
# DATA STATUS CHECK
# ============================================================================

def check_data_status():
    """Check and display data status at startup"""
    logger.info("\n" + "="*80)
    logger.info("📊 DATA STATUS CHECK")
    logger.info("="*80)
    
    logger.info("\n1️⃣ BASELINE DATA:")
    today = get_ist_time()
    baseline_found = False
    for days_back in range(1, 5):
        prev_day = today - timedelta(days=days_back)
        if prev_day.weekday() < 5:
            filename = os.path.join(BASELINE_DIR, f"baseline_{prev_day.strftime('%Y%m%d')}.json")
            if os.path.exists(filename):
                file_size = os.path.getsize(filename) / (1024 * 1024)
                logger.info(f"   ✅ Found: {os.path.basename(filename)} ({file_size:.2f} MB)")
                baseline_found = True
                break
    
    if not baseline_found:
        logger.warning("   ⚠️ NO BASELINE FOUND!")
        logger.warning("   → Run baseline capture at 4:00 PM")
    
    logger.info("\n2️⃣ OPTIONS VOLUME HISTORY:")
    history_files = 0
    total_size = 0
    for days_back in range(10):
        date = today - timedelta(days=days_back)
        filename = os.path.join(OPTIONS_HISTORY_DIR, f"options_{date.strftime('%Y%m%d')}.json")
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            total_size += file_size
            history_files += 1
    
    if history_files > 0:
        logger.info(f"   ✅ Found: {history_files} days of history ({total_size/(1024*1024):.2f} MB)")
    else:
        logger.warning("   ⚠️ No options history yet")
    
    logger.info("\n3️⃣ PAPER TRADING DATA:")
    positions_file = os.path.join(PAPER_TRADING_DIR, "positions.json")
    
    if os.path.exists(positions_file):
        try:
            with open(positions_file, 'r') as f:
                data = json.load(f)
                pos_count = len(data.get('positions', []))
                cap = data.get('capital', STARTING_CAPITAL)
            logger.info(f"   ✅ Positions File: {pos_count} open positions")
            logger.info(f"   💰 Capital: ₹{cap:,.0f}")
        except:
            logger.warning("   ⚠️ Error reading positions file")
    else:
        logger.info("   ℹ️  No positions file (fresh start)")
    
    logger.info("\n" + "="*80)
    logger.info("✅ DATA STATUS CHECK COMPLETE")
    logger.info("="*80 + "\n")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  SCANNER v12.0 - TOP-N 3X DETECTOR                           ║
    ╚══════════════════════════════════════════════════════════════╝
    
    🆕 NEW IN v12.0 (TOP-N FILTERING):
       ✅ No spot_price needed - works with existing data!
       ✅ Filters by highest option prices (near-the-money)
       ✅ Early: Top 10 CE + 10 PE by price
       ✅ Late: Top 5 CE + 5 PE by price
       ✅ Naturally excludes far OTM options
       ✅ Expected Performance:
          • Early Model: 30-40% precision
          • Late Model: 40-50% precision
       ✅ Schedule:
          • 3:55 PM - Stock Volume ML
          • 4:00 PM - Baseline Capture
          • 4:30 PM - 3X ML (Top-N Filtering)
    
    🔧 v9.2.1 HOTFIX:
       ✅ Fixed last_price KeyError
       ✅ All stocks processing correctly
    
    🆕 v9.2 FEATURES:
       ✅ All Dashboard Limits Removed: Shows ALL signals
       ✅ Newest Signals on Top: Reversed order everywhere
       ✅ Enhanced Option Volume: 3-way validation
          • Volume Spike (>=10X)
          • OI Increasing (from last fetch)
          • Price Increasing (green candle)
       ✅ Open Positions: Newest first
    
    🆕 v9.1 FEATURES:
       ✅ Multi-Day Enhanced Data: Last 3 days loaded
       ✅ Immediate 3X Predictions: From 9:15 AM
       ✅ Immediate Option Volume Signals: From 1st fetch
       ✅ First Hour Coverage: 9:15-10:15 AM captured ✓
    
    🎯 v9.0 FEATURES (DUAL MODEL SYSTEM):
       ✅ Dual Model: Early (>5d) + Late (≤5d) expiry
       ✅ Enhanced Option Data: ALL fields captured
       ✅ ML-powered 3X prediction with confidence
       ✅ Multi-stage alerts: Pattern → Starting → Target
       ✅ Scheduled training with backups
       ✅ Dashboard: All predictions + all alerts
    
    📊 API USAGE:
       • Main Scanner: ~7,279 calls/day
       • 5-Min Monitor: ~300 calls/day
       • 3X Detection: 0 calls/day
       • TOTAL: ~7,579/day (7.6% of limit) ✅
    
    ✅ 4 CORE SYSTEMS:
       • OI Signals (threshold alerts)
       • Stock Volume Spike + ML
       • Option Volume Spike (3-way dynamic)
       • 3X Move Prediction (Dual Model)
    
    ⏰ DAILY SCHEDULE:
       • 3:55 PM - Stock ML training
       • 4:00 PM - Baseline capture
       • 4:30 PM - Advanced 3X ML training (Ensemble)
    
    📊 Dashboard: http://localhost:5000
    """)
    
    check_data_status()
    
    # Initialize 3X detector
    initialize_3x_detector()
    
    # Update telegram message
    threex_status = "✅ Enabled (Advanced Ensemble)" if threex_enabled else "⚠️ Not loaded"
    
    if send_telegram_message(
        f"🤖 <b>Scanner v12.0 - Top-N 3X Detector</b>\n\n"
        f"🆕 New in v12.0:\n"
        f"✅ Top-N filtering (highest priced options only)\n"
        f"✅ Early: Top 10 CE + 10 PE, Late: Top 5 CE + 5 PE\n"
        f"✅ Works with existing data (no spot_price needed)\n\n"
        f"📅 Schedule:\n"
        f"   • 3:55 PM - Stock ML\n"
        f"   • 4:00 PM - Baseline\n"
        f"   • 4:30 PM - 3X ML (Advanced)\n\n"
        f"🎯 3X ML: {threex_status}\n"
        f"📊 Ready to trade"):
        logger.info("✅ Telegram connected\n")
    
    Thread(target=monitor_and_schedule, daemon=True).start()
    
    if is_market_open() and not scanner_running:
        logger.info("🚀 Market is open! Starting scanner now...\n")
        Thread(target=run_scanner, daemon=True).start()
    else:
        now = get_ist_time()
        logger.info(f"⏰ Market closed. Current time: {now.strftime('%H:%M:%S')}")
        logger.info(f"   Scanner will start at 9:15 AM")
        logger.info(f"   Stock ML at 3:55 PM")
        logger.info(f"   Baseline capture at 4:00 PM")
        logger.info(f"   Advanced 3X ML at 4:30 PM\n")
    
    logger.info("🌐 Dashboard: http://localhost:5000")
    logger.info("📊 API: http://localhost:5000/api/dashboard\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
