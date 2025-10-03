# main.py

import tkinter as tk
import sys
from pathlib import Path

# Add the project root to the Python path to allow for absolute imports from src
# This makes the application runnable from the root directory via `python main.py`
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.gui import ScannerGUI
from src.config import SECRETS  # Import to check for secrets early
from src.logger_config import setup_logging
from loguru import logger

def main():
    """
    The main entry point for the Dhan Option Scanner application.
    """
    # --- Setup Logging ---
    # This must be the first thing to run to ensure all subsequent
    # messages are captured.
    setup_logging()

    # --- Pre-run Checks ---
    # Check if essential secrets are loaded.
    if not SECRETS:
        logger.critical("Environment variables or .env file could not be loaded.")
        logger.critical("The application will open, but the scanner will FAIL to start.")
        logger.critical(f"Please ensure your .env file is correctly set up in the '{project_root.name}' directory.")

    # --- GUI Initialization ---
    root = tk.Tk()
    app = ScannerGUI(root)

    # Ensure the scanner is stopped gracefully when the window is closed
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # --- Start the Application ---
    root.mainloop()

if __name__ == "__main__":
    main()