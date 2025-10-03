# Dhan Intraday Option-Chain Scanner

This application is a production-ready intraday option-chain scanner for Windows, designed to monitor a universe of stocks and indices, identify trading signals based on Open Interest (OI) changes, and deliver real-time alerts via a desktop GUI and Telegram.

## Features

- **Live Scanning**: Continuously scans a user-defined universe of symbols from the Dhan API.
- **Configurable Rules**: Identifies long/short candidates based on configurable OI change percentages (e.g., CE OI drops >30% while PE OI rises).
- **ATM-Focused Analysis**: Analyzes the 5 most relevant strikes around the At-The-Money (ATM) price.
- **Liquidity Filters**: Automatically ignores illiquid options based on volume, OI, and bid-ask spread.
- **Minimal GUI**: A simple, clean desktop interface built with Tkinter to display signals without extra dependencies.
- **Telegram Alerts**: Delivers instant notifications for every new signal to a specified Telegram chat.
- **Robust & Secure**: Handles API errors with retries and reads all sensitive credentials securely from environment variables.
- **Windows Automation**: Includes `.bat` and `.ps1` scripts for easy operation and a recipe for daily automation via Windows Task Scheduler.
- **Detailed Logging**: Keeps rotating log files for diagnostics and history.

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
│   ├── __init__.py
│   ├── main.py                 # Main application entry point (launches the GUI).
│   ├── scanner.py              # Core scanning and signal processing logic.
│   ├── gui.py                  # Tkinter-based GUI.
│   ├── dhan_api.py             # Handles all communication with the Dhan API.
│   ├── notifier.py             # Handles Telegram notifications.
│   ├── utils.py                # Helper functions for strike calculations.
│   └── logger_config.py        # Logging setup.
│
├── venv\                       # Python virtual environment (created during setup).
│
├── .env                        # **CRITICAL**: Stores your secret API keys (you must create this).
├── requirements.txt            # List of Python packages to install.
├── README.md                   # This file.
│
├── start_scanner.bat           # Easy-to-use script to start the application.
├── stop_scanner.bat            # Easy-to-use script to stop the application.
├── run_scanner.ps1             # PowerShell version of the start script.
└── daily_check.ps1             # PowerShell script for health checks.
```

---

## Setup Instructions (for Windows)

Follow these steps exactly to set up the scanner on a new machine.

### Prerequisites
- **Python 3.10+**: Ensure you have Python installed. You can download it from the [official Python website](https://www.python.org/downloads/). Make sure to check the box **"Add Python to PATH"** during installation.

### Step 1: Place the Code
- Unzip or place the entire `dhan_scanner` folder into a simple path, for example: `C:\dhan_scanner`.

### Step 2: Create the Python Virtual Environment
- Open the Windows Command Prompt (search for `cmd` in the Start Menu).
- Navigate to the project directory:
  ```cmd
  cd C:\dhan_scanner
  ```
- Create a virtual environment named `venv`:
  ```cmd
  python -m venv venv
  ```
  This creates a `venv` folder inside your project directory, which will keep the scanner's Python packages separate from the rest of your system.

### Step 3: Activate the Virtual Environment
- In the same Command Prompt window, run the following command to activate the environment:
  ```cmd
  venv\Scripts\activate.bat
  ```
- You will know it's active because your command prompt will now start with `(venv)`, like this: `(venv) C:\dhan_scanner>`.
- **Important**: You must activate the environment every time you want to run the scanner or install packages manually. The `start_scanner.bat` script does this for you automatically.

### Step 4: Install Dependencies
- With the virtual environment still active, install all the required Python packages by running:
  ```cmd
  pip install -r requirements.txt
  ```

### Step 5: Configure Your Secrets (.env file)
- This is the most important step for security.
- In the `C:\dhan_scanner` directory, create a new text file and name it exactly **`.env`**.
- Open this `.env` file with Notepad and add your credentials in the following format. **Copy and paste the template below and replace the placeholder values.**

  ```
  # .env file for Dhan Scanner
  # Replace the "your_..." values with your actual credentials.

  DHAN_CLIENT_ID="your_dhan_client_id"
  DHAN_ACCESS_TOKEN="your_dhan_access_token"

  TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
  TELEGRAM_CHAT_ID="your_telegram_chat_id"
  ```
- **How to get these values:**
  - `DHAN_CLIENT_ID` & `DHAN_ACCESS_TOKEN`: Generate these from the [DhanHQ API portal](https://dhanhq.co/account/api).
  - `TELEGRAM_BOT_TOKEN`: Create a new bot by talking to the `@BotFather` on Telegram. It will give you a token.
  - `TELEGRAM_CHAT_ID`: Get your chat ID by talking to the `@userinfobot` on Telegram.

### Step 6: Review Configuration (Optional)
- Open `config\config.yaml` to see the default settings for scan interval, OI thresholds, and liquidity filters. For most users, the defaults are fine to start with.

---

## How to Run the Scanner

### Manually
- **To Start**: Simply double-click the **`start_scanner.bat`** file. A new window will appear with the scanner GUI.
- **To Stop**: Double-click the **`stop_scanner.bat`** file. This will find and close the scanner process. You can also just close the GUI window or use the "Stop Scanner" button.

### Daily Health Check
- Before starting the market day, you can run **`daily_check.ps1`** (right-click -> "Run with PowerShell") to verify that your environment variables are set, the venv is healthy, and the scanner ran correctly on the previous day.

---

## Automation with Windows Task Scheduler

To run the scanner automatically every market day at 9:00 AM:

1.  **Open Task Scheduler**: Search for "Task Scheduler" in the Start Menu.
2.  **Create Basic Task**: In the "Actions" pane on the right, click "Create Basic Task...".
3.  **Name and Description**:
    -   Name: `Dhan Scanner Startup`
    -   Description: `Starts the Dhan Option Scanner every morning.`
    -   Click **Next**.
4.  **Trigger**:
    -   Select **Daily**. Click **Next**.
    -   Set the start time to **9:00:00 AM**.
    -   Ensure "Recur every: 1 days" is set. Click **Next**.
5.  **Action**:
    -   Select **Start a program**. Click **Next**.
    -   Program/script: Click **Browse...** and navigate to `C:\dhan_scanner\start_scanner.bat`.
    -   Click **Next**.
6.  **Finish**:
    -   Check the box **"Open the Properties dialog for this task when I click Finish"**.
    -   Click **Finish**.
7.  **Advanced Properties (IMPORTANT)**:
    -   In the Properties window, go to the **Conditions** tab.
    -   Under the "Power" section, **uncheck** "Start the task only if the computer is on AC power".
    -   Go to the **Settings** tab.
    -   Ensure **"Run task as soon as possible after a scheduled start is missed"** is checked.
    -   Ensure **"Run only when user is logged on"** is selected. This is critical for the GUI to be visible.
    -   Click **OK**.

The scanner will now launch automatically every day at 9:00 AM.

---

## Operations and Maintenance

### Token Rotation
The `DHAN_ACCESS_TOKEN` may expire after some time (e.g., a day or a week). If the scanner logs show authentication errors, you need to generate a new token.

1.  Log in to your Dhan account.
2.  Go to the DhanHQ API section and generate a new access token.
3.  Open the `.env` file (`C:\dhan_scanner\.env`).
4.  Replace the old `DHAN_ACCESS_TOKEN` value with the new one.
5.  Save the file and restart the scanner.

### Viewing Logs
- If you encounter issues, the first place to look is the log file located at `logs\scanner.log`. It contains detailed information about every scan cycle, signal, and error.