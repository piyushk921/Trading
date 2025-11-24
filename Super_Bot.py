import time
import requests
import json
import os
import csv
import sys
import pytz
import pandas as pd
from datetime import datetime, timedelta
from threading import Thread
from collections import deque
from flask import Flask, jsonify

# ==============================================================================
# 🟢 1. USER CONFIGURATION
# ==============================================================================
DHAN_CLIENT_ID = "1000681801"      
DHAN_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY0MDQxMDAyLCJpYXQiOjE3NjM5NTQ2MDIsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMDAwNjgxODAxIn0.5XnYkuRIMySiDGtuuz--_49D33FKsxuT9u0rU0d07iXyoxoI8oAztFbf4os8Mpma11Yjnf3s4iNJn_RVaeaQYA"
DHAN_API_BASE = "https://api.dhan.co"

TELEGRAM_BOT_TOKEN = "7589611837:AAGe5ysmoq-DrsioVd4T6AzE9dnUUNxdSYU"
TELEGRAM_CHAT_ID = "865318193"

# ==============================================================================
# ⚙️ 2. RESEARCH-BACKED STRATEGY PARAMETERS
# ==============================================================================
SCAN_DELAY = 4               # 4 Seconds per stock (Dhan Rule)
HISTORY_SIZE = 6             # Keep ~75 mins of history in RAM (0=Current, -3=30m, -5=60m)

# Filters (The "Trap" Avoidance)
MIN_PREMIUM = 10.0           
MAX_PREMIUM = 450.0          
FILTER_DELTA_MIN = 0.15      # Deep OTM but movable
FILTER_DELTA_MAX = 0.35      # Avoid expensive ATM
FILTER_IV_MAX = 55.0         # Avoid IV Crush risks

# Triggers (The "Ignition")
REQ_VOL_30M = 100.0          # Volume doubled in 30 mins
REQ_VOL_60M = 120.0          # Volume trend sustained 60 mins
REQ_OI_60M = 1.5             # Smart money accumualtion
REQ_PRICE_STABILITY = -5.0   # Price allowed to dip, but not crash

# ==============================================================================
# 📋 3. STOCK LIST
# ==============================================================================
STOCKS = {
    "13": "NIFTY", "25": "BANKNIFTY",
    "2885": "RELIANCE", "1333": "HDFCBANK", "10604": "BHARTIARTL", "11536": "TCS",
    "4963": "ICICIBANK", "3045": "SBIN", "317": "BAJFINANCE", "1394": "HINDUNILVR",
    "1594": "INFY", "9480": "LICI", "11483": "LT", "10999": "MARUTI",
    "1660": "ITC", "2031": "M&M", "1922": "KOTAKBANK", "3991": "HCLTECH",
    "3351": "SUNPHARMA", "5900": "AXISBANK", "11532": "ULTRACEMCO", "16675": "BAJAJFINSV",
    "11630": "NTPC", "2303": "HAL", "5097": "ETERNAL", "3506": "TITAN",
    "15083": "ADANIPORTS", "2475": "ONGC", "383": "BEL", "25": "ADANIENT",
    "11723": "JSWSTEEL", "19913": "DMART", "14977": "POWERGRID", "16669": "BAJAJ-AUTO",
    "3787": "WIPRO", "17963": "NESTLEIND", "236": "ASIANPAINT", "20374": "COALINDIA",
    "11195": "INDIGO", "3499": "TATASTEEL", "1624": "IOC", "1424": "HINDZINC",
    "18143": "JIOFIN", "1232": "GRASIM", "910": "EICHERMOT", "14732": "DLF",
    "3063": "VEDL", "21808": "SBILIFE", "10940": "DIVISLAB", "1363": "HINDALCO",
    "8479": "TVSMOTOR", "1964": "TRENT", "3563": "ADANIGREEN", "17818": "LTIM",
    "2029": "IRFC", "467": "HDFCLIFE", "18921": "VBL", "2664": "PIDILITIND",
    "547": "BRITANNIA", "977": "TATAMOTORS", "526": "BPCL", "13538": "TECHM",
    "685": "CHOLAFIN", "1270": "AMBUJACEM", "4668": "BANKBARODA", "23650": "MUTHOOTFIN",
    "10666": "PNB", "14299": "PFC", "13332": "SOLARINDS", "4306": "SHRIRAMFIN",
    "3426": "TATAPOWER", "694": "CIPLA", "4244": "HDFCAMC", "3518": "TORNTPHARM",
    "760": "CGPOWER", "3220": "LODHA", "10099": "GODREJCP", "22377": "MAXHEALTH",
    "4717": "GAIL", "509": "MAZDOCK", "11287": "TATACONSUM", "157": "APOLLOHOSP",
    "10794": "CANBK", "9590": "POLYCAB", "10217": "ADANIENSOL",
    "4204": "MOTHERSON", "1348": "HEROMOTOCO", "3150": "SIEMENS", "1901": "CUMMINSIND",
    "13": "ABB", "3103": "SHREECEM", "10753": "UNIONBANK", 
    "6733": "JINDALSTEL", "14309": "INDIANB", "881": "DRREDDY", "19585": "BSE",
    "15380": "MANKIND", "21690": "DIXON", "21770": "ICICIGI", "7929": "ZYDUSLIFE",
    "15355": "RECLTD", "17875": "GODREJPROP", "15414": "TITAGARH", "10440": "LUPIN",
    "20261": "IREDA", "1023": "FEDERALBNK", "1997": "LICHSGFIN", "18652": "ICICIPRULI",
    "5258": "INDUSINDBK", "17971": "SBICARD", "3718": "VOLTAS", "15332": "NMDC",
    "6545": "NYKAA", "11351": "PETRONET", "2263": "BANDHANBNK", "7406": "GLENMARK",
    "14418": "ASTRAL", "18721": "NUVAMA", "9552": "RVNL", "6705": "PAYTM",
    "20242": "OBEROIRLTY", "18365": "PERSISTENT", "18096": "JUBLFOOD", "20293": "TATATECH",
    "20302": "PRESTIGE", "275": "AUROPHARMA", "11543": "COFORGE", "12018": "SUZLON",
    "2144": "BDL", "11262": "IGL", "676": "EXIDEIND", "1406": "HINDPETRO",
    "17869": "JSWENERGY", "10447": "UNITDSPR", "24184": "PIIND", "21614": "ABCAPITAL",
    "14154": "UNOMINDA", "422": "BHARATFORG", "11287": "UPL", "11703": "ALKEM",
    "10243": "SYNGENE", "19234": "LAURUSLABS", "9683": "KPITTECH", "20825": "HUDCO",
    "29135": "INDUSTOWER", "4503": "MPHASIS", "21238": "AUBANK", "21174": "CDSL",
    "10738": "OFSS", "31415": "NBCC", "17438": "OIL", "4749": "CONCOR",
    "438": "BHEL", "14592": "FORTIS", "14413": "PAGEIND", "14552": "PHOENIXLTD",
    "13786": "TORNTPOWER", "13310": "KEI", "14366": "IDEA", "8075": "DALBHARAT",
    "6364": "NATIONALUM", "13528": "GMRAIRPORT", "11184": "IDFCFIRSTB", "2963": "SAIL",
    "2142": "MFSL", "212": "ASHOKLEY", "13751": "NAUKRI", "24948": "LTF",
    "2955": "KALYANKJIL", "4684": "SONACOMS", "17400": "NHPC", "19061": "MANAPPURAM",
    "18908": "PNBHOUSING", "324": "ANGELONE", "4745": "BANKINDIA", "13061": "360ONE",
    "9599": "DELHIVERY", "17094": "CROMPTON", "18391": "RBLBANK", "4067": "MARICO",
    "772": "DABUR", "13359": "KFINTECH", "6656": "POLICYBZR", "11915": "YESBANK",
    "8311": "BLUESTARCO", "342": "CAMS", "9819": "HAVELLS", "13611": "IRCTC",
    "15141": "COLPAL", "12092": "KAYNES", "18457": "POWERINDIA", "25780": "APLAPOLLO",
    "25358": "PGEL", "3273": "SRF", "11571": "PPLPHARMA", "3363": "SUPREMEIND",
    "17029": "PATANJALI", "31181": "MCX", "7852": "INOXWIND", "1185": "AMBER",
    "11809": "IIFL", "5748": "CYIENT", "2319": "NCC", "30125": "SAMMAANCAP",
    "220": "IEX", "21951": "HFCL"
}

# ==============================================================================
# 🔧 SETUP & HELPERS
# ==============================================================================
ist = pytz.timezone('Asia/Kolkata')
DATA_DIR = "Live_Data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

# Global Memory for Analysis
memory = {} # Structure: { "SYMBOL_STRIKE": deque([snapshot1, snapshot2...]) }
signals = [] # Store for dashboard

def get_ist_time():
    return datetime.now(ist)

def make_api_request(endpoint, method="GET", data=None):
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
    except: pass
    return None

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=3)
    except: pass

# ==============================================================================
# 🗓️ EXPIRY LOGIC (FROM YOUR CODE)
# ==============================================================================
NSE_HOLIDAYS_2025 = ["2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10", "2025-04-14", "2025-04-18", "2025-05-01", "2025-08-15", "2025-08-27", "2025-10-02", "2025-10-21", "2025-10-22", "2025-11-05", "2025-12-25"]

def is_trading_day(date):
    if date.weekday() >= 5: return False
    if date.strftime("%Y-%m-%d") in NSE_HOLIDAYS_2025: return False
    return True

def adjust_expiry_for_holiday(expiry_date):
    current = expiry_date
    while not is_trading_day(current):
        current = current - timedelta(days=1)
    return current

def get_next_tuesday(from_date):
    days_ahead = (1 - from_date.weekday()) % 7
    if days_ahead == 0: days_ahead = 7
    return from_date + timedelta(days=days_ahead)

def get_smart_expiry(security_id):
    """
    - NIFTY (13): Weekly Expiry
    - BANKNIFTY (25) & STOCKS: Monthly Expiry
    """
    today = get_ist_time()
    
    if security_id == 13: # NIFTY WEEKLY
        next_tuesday = get_next_tuesday(today)
        if today.weekday() == 1 and today.hour < 15:
            expiry_tuesday = today
        else:
            expiry_tuesday = next_tuesday
        return adjust_expiry_for_holiday(expiry_tuesday).strftime("%Y-%m-%d")
        
    else: # MONTHLY (Stocks + BN)
        if today.month == 12:
            last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        days_to_subtract = (last_day.weekday() - 1) % 7
        last_tuesday = last_day - timedelta(days=days_to_subtract)
        current_month_expiry = adjust_expiry_for_holiday(last_tuesday)
        
        if today.date() > current_month_expiry.date() or (today.date() == current_month_expiry.date() and today.hour >= 15):
            # Move to next month
            if today.month == 12:
                next_month_last = today.replace(year=today.year + 1, month=2, day=1) - timedelta(days=1)
            elif today.month == 11:
                next_month_last = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                next_month_last = today.replace(month=today.month + 2, day=1) - timedelta(days=1)
            
            days_sub = (next_month_last.weekday() - 1) % 7
            next_expiry = next_month_last - timedelta(days=days_sub)
            return adjust_expiry_for_holiday(next_expiry).strftime("%Y-%m-%d")
        else:
            return current_month_expiry.strftime("%Y-%m-%d")

# ==============================================================================
# 💾 DATA STORAGE (CSV)
# ==============================================================================
def save_to_csv(symbol, data):
    folder = os.path.join(DATA_DIR, datetime.now().strftime('%Y-%m-%d'))
    if not os.path.exists(folder): os.makedirs(folder)
    
    file_path = os.path.join(folder, f"{symbol}.csv")
    exists = os.path.isfile(file_path)
    
    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(['Time', 'Symbol', 'Strike', 'Type', 'Price', 'Vol', 'OI', 'Delta', 'IV', 'Gamma'])
        
        ts = datetime.now().strftime('%H:%M:%S')
        for k, d in data.items():
            writer.writerow([ts, symbol, d.get('strike_price'), d.get('option_type'), 
                             d.get('last_price'), d.get('volume'), d.get('open_interest'), 
                             d.get('delta'), d.get('iv'), d.get('gamma')])

# ==============================================================================
# 🧠 ANALYSIS ENGINE
# ==============================================================================
def analyze(symbol, strike, otype, p, v, oi, delta, iv):
    uid = f"{symbol}_{strike}_{otype}"
    
    if uid not in memory: memory[uid] = deque(maxlen=HISTORY_SIZE)
    history = memory[uid]
    history.append({'p': p, 'v': v, 'oi': oi})
    
    # Need 60 min history (5 cycles @ 14min gaps)
    if len(history) < 3: return 

    now = history[-1]
    t_30 = history[-3] # ~30 mins ago
    t_60 = history[0] if len(history) >= 5 else history[-3] # ~60 mins ago
    
    if t_60['v'] == 0: return

    # --- METRICS ---
    v_chg_60 = ((now['v'] - t_60['v']) / t_60['v']) * 100
    v_chg_30 = ((now['v'] - t_30['v']) / t_30['v']) * 100 if t_30['v'] > 0 else 0
    p_chg_30 = ((now['p'] - t_30['p']) / t_30['p']) * 100 if t_30['p'] > 0 else 0
    
    oi_chg_60 = 0
    if t_60['oi'] > 0: oi_chg_60 = ((now['oi'] - t_60['oi']) / t_60['oi']) * 100

    # --- FILTERS (Trap Avoidance) ---
    if not (FILTER_DELTA_MIN <= delta <= FILTER_DELTA_MAX): return
    if iv > FILTER_IV_MAX: return
    if p_chg_30 < REQ_PRICE_STABILITY: return

    # --- TRIGGER (Research Based) ---
    if v_chg_30 >= REQ_VOL_30M and v_chg_60 >= REQ_VOL_60M and oi_chg_60 >= REQ_OI_60M:
        
        signal_data = {
            'Time': datetime.now().strftime('%H:%M'),
            'Symbol': symbol,
            'Strike': f"{strike} {otype}",
            'Price': p,
            'Vol_30m': round(v_chg_30),
            'Vol_60m': round(v_chg_60),
            'OI_Chg': round(oi_chg_60, 2),
            'Delta': delta
        }
        signals.append(signal_data)
        
        # Telegram Alert
        msg = (
            f"💎 **HERO-ZERO SETUP**\n"
            f"Symbol: #{symbol}\n"
            f"Strike: **{strike} {otype}**\n"
            f"----------------------\n"
            f"📊 30m Vol: +{round(v_chg_30)}%\n"
            f"📊 60m Vol: +{round(v_chg_60)}%\n"
            f"📈 60m OI:  +{round(oi_chg_60, 2)}%\n"
            f"💰 Price: {t_30['p']} ➝ **{p}**\n"
            f"----------------------\n"
            f"Delta: {delta} (Golden Zone)"
        )
        print(f"\n🚨 SIGNAL: {symbol} {strike} {otype}")
        send_telegram(msg)

def run_scanner():
    print(f"\n🔄 Cycle Start: {datetime.now().strftime('%H:%M:%S')}")
    i = 0
    for sec_id, sym in STOCKS.items():
        i+=1
        print(f"   [{i}/{len(STOCKS)}] {sym}...", end="\r")
        
        try:
            expiry = get_smart_expiry(sec_id)
            exch_seg = "IDX_I" if sec_id in [13, 25] else "NSE_EQ"
            
            # API Request
            endpoint = "/v2/optionchain"
            payload = {
                "UnderlyingScrip": sec_id,
                "UnderlyingSeg": exch_seg,
                "Expiry": expiry
            }
            resp = make_api_request(endpoint, method="POST", data=payload)
            
            if resp and resp.get('status') == 'success':
                data = resp.get('data', {})
                if data:
                    # Record Data
                    save_to_csv(sym, data)
                    
                    # Analyze Data
                    for k, d in data.items():
                        p = float(d.get('last_price', 0))
                        v = float(d.get('volume', 0))
                        oi = float(d.get('open_interest', 0))
                        delta = abs(float(d.get('delta', 0)))
                        iv = float(d.get('iv', 0))
                        
                        if p < MIN_PREMIUM or p > MAX_PREMIUM: continue
                        if v < 500: continue
                        if d.get('option_type') != "CALL": continue 

                        analyze(sym, d.get('strike_price'), d.get('option_type'), p, v, oi, delta, iv)
        except: pass
        time.sleep(SCAN_DELAY)
    
    print("\n✅ Cycle Complete.")

# ==============================================================================
# 🌐 FLASK DASHBOARD
# ==============================================================================
app = Flask(__name__)

@app.route('/')
def dashboard():
    html = """
    <style>
        body { background: #111; color: #eee; font-family: sans-serif; padding: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; border-bottom: 1px solid #333; text-align: left; }
        th { color: #00ffcc; }
        .positive { color: #0f0; }
    </style>
    <h1>🚀 Super-Bot Live Dashboard</h1>
    <p>Monitoring Real-time Volume & OI Accumulation</p>
    <table>
        <thead><tr><th>Time</th><th>Symbol</th><th>Strike</th><th>Price</th><th>Vol 30m</th><th>Vol 60m</th><th>OI Chg</th><th>Delta</th></tr></thead>
        <tbody>
    """
    for s in reversed(signals):
        html += f"""
        <tr>
            <td>{s['Time']}</td><td>{s['Symbol']}</td><td>{s['Strike']}</td><td>{s['Price']}</td>
            <td class="positive">+{s['Vol_30m']}%</td><td class="positive">+{s['Vol_60m']}%</td>
            <td class="positive">+{s['OI_Chg']}%</td><td>{s['Delta']}</td>
        </tr>"""
    
    html += "</tbody></table>"
    return html

def start_server():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    print("🤖 Super-Bot Online.")
    print("📊 Strategy: Multi-Timeframe Volume + Delta Filter")
    send_telegram("🤖 Super-Bot Started.")
    
    # Start Dashboard in Background
    Thread(target=start_server, daemon=True).start()
    
    # Start Scanner
    while True:
        run_scanner()