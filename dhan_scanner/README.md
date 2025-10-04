# Dhan Intraday Option-Chain Scanner (Enhanced)

This application is a production-ready intraday option-chain scanner for Windows, designed to monitor a universe of stocks and indices, identify trading signals based on Open Interest (OI) changes, and deliver real-time alerts via a desktop GUI and Telegram.

## Key Features

- **Live Scanning**: Continuously scans a user-defined universe of symbols from the Dhan API.
- **Advanced Tiered Signals**: Identifies multiple types of trading signals across different percentage thresholds (e.g., >10%, >20%, >30%).
- **Multiple Signal Types**:
    - **OI Unwinding (Long/Short)**: Detects classic unwinding patterns where one side's OI drops significantly while the other rises.
    - **OI Buildup (CE/PE)**: Detects significant OI addition on either the Call or Put side, indicating new interest.
- **ATM-Focused Analysis**: Analyzes the 5 most relevant strikes around the At-The-Money (ATM) price.
- **Multi-Tab GUI**: A clean, four-tab interface to clearly separate and display each signal type.
- **Telegram Alerts**: Delivers instant, detailed notifications for every new signal to a specified Telegram chat.
- **Robust & Secure**: Includes a pre-run API health check, handles errors with retries, and reads all secrets securely from environment variables.
- **Windows Automation**: Includes `.bat` and `.ps1` scripts for easy operation and a recipe for daily automation via Windows Task Scheduler.

---

## Signal Logic Explained

The scanner identifies four distinct types of signals, categorized by tiered percentage thresholds defined in `config.yaml`.

1.  **Long Unwinding**: A potential bullish signal.
    - **Condition**: Call option OI *decreases* by a set percentage AND Put option OI *increases*.
    - **Interpretation**: Suggests that Call writers are closing their positions (covering shorts) while new Put writers are entering, indicating a potential upward move.

2.  **Short Unwinding**: A potential bearish signal.
    - **Condition**: Put option OI *decreases* by a set percentage AND Call option OI *increases*.
    - **Interpretation**: Suggests that Put writers are closing their positions while new Call writers are entering, indicating a potential downward move.

3.  **CE Buildup (Call OI Buildup)**:
    - **Condition**: Call option OI *increases* significantly, irrespective of the Put side.
    - **Interpretation**: Indicates a strong buildup of interest in Call options, which could mean traders are either buying calls (bullish) or writing calls (bearish). This signal highlights unusual activity for further analysis.

4.  **PE Buildup (Put OI Buildup)**:
    - **Condition**: Put option OI *increases* significantly, irrespective of the Call side.
    - **Interpretation**: Indicates a strong buildup of interest in Put options.

---

## The User Interface

The GUI is organized into four tabs to provide a clear view of all detected signals:

1.  **Longs (CE Unwind)**: Displays all "Long Unwinding" signals.
2.  **Shorts (PE Unwind)**: Displays all "Short Unwinding" signals.
3.  **CE Buildup**: Displays all stocks with significant Call OI addition.
4.  **PE Buildup**: Displays all stocks with significant Put OI addition.

Each list includes a **Threshold** column (e.g., `> 30%`, `> 20%`) to show the strength of the signal at a glance.

---

## Folder Structure

```
C:\DHAN_SCANNER\
│
├── config\
│   ├── config.yaml             # Main configuration for scanner rules, thresholds, etc.
│   ├── universe_symbols.txt    # List of symbols to scan.
│   └── symbol_to_id.json       # Mapping of symbols to Dhan security IDs.
│
├── logs\
│   └── scanner.log             # Rotating log files are stored here.
│
├── src\
│   └── ... (source files)
│
├── venv\                       # Python virtual environment (created during setup).
│
├── .env                        # **CRITICAL**: Stores your secret API keys (you must create this).
├── requirements.txt            # List of Python packages to install.
├── README.md                   # This file.
│
├── start_scanner.bat           # Easy-to-use script to start the application.
├── stop_scanner.bat            # Easy-to-use script to stop the application.
└── daily_check.ps1             # PowerShell script for health checks.
```

---

## Setup Instructions (for Windows)

Follow these steps exactly to set up the scanner on a new machine.

### Prerequisites
- **Python 3.10+**: Ensure you have Python installed. You can download it from the [official Python website](https://www.python.org/downloads/). Make sure to check the box **"Add Python to PATH"** during installation.

### Step 1: Place the Code
- Unzip or place the entire `dhan_scanner` folder into a simple path, for example: `C:\dhan_scanner`.

### Step 2: Create and Activate Virtual Environment
- Open the Windows Command Prompt (search for `cmd`).
- Navigate to the project directory (`cd C:\dhan_scanner`).
- Create the environment: `python -m venv venv`
- Activate the environment: `venv\Scripts\activate.bat`
- Your prompt should now start with `(venv)`.

### Step 3: Install Dependencies
- With the virtual environment still active, run: `pip install -r requirements.txt`

### Step 4: Configure Your Secrets (.env file)
- In the `C:\dhan_scanner` directory, create a new text file and name it exactly **`.env`**.
- Open this `.env` file with Notepad and add your credentials in the following format, replacing the placeholder values.

  ```
  # .env file for Dhan Scanner
  DHAN_CLIENT_ID="your_dhan_client_id"
  DHAN_ACCESS_TOKEN="your_dhan_access_token"
  TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
  TELEGRAM_CHAT_ID="your_telegram_chat_id"
  ```
- **Important**: If you have trouble, ensure Windows is not hiding file extensions and your file is not accidentally named `.env.txt`.

### Step 5: Review Configuration (Optional)
- Open `config\config.yaml` to see the default settings. You can adjust the `unwinding_thresholds` and `buildup_thresholds` lists to your preference.

---

## How to Run the Scanner

- **To Start**: Simply double-click the **`start_scanner.bat`** file.
- **To Stop**: Double-click the **`stop_scanner.bat`** file, or close the GUI window.
- **Daily Health Check**: Before the market opens, run **`daily_check.ps1`** (right-click -> "Run with PowerShell") to verify your setup.

---

## Automation with Windows Task Scheduler

To run the scanner automatically every market day at 9:00 AM, follow the instructions in the original `README.md` or use the Task Scheduler wizard to run `C:\dhan_scanner\start_scanner.bat` daily.

---

## Operations and Maintenance

### Token Rotation
The `DHAN_ACCESS_TOKEN` will expire. When the scanner logs show an "invalid token" error on startup, you must generate a new token from the Dhan API portal and update it in your `.env` file.

### Viewing Logs
- All detailed activity, signals, and errors are recorded in `logs\scanner.log`. This is the first place to look if you encounter any issues.