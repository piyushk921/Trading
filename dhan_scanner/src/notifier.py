# src/notifier.py

import requests
from loguru import logger
from .config import SECRETS

class TelegramNotifier:
    """
    Handles sending notifications to a Telegram chat.
    """
    def __init__(self):
        self.bot_token = SECRETS.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = SECRETS.get("TELEGRAM_CHAT_ID")

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials (BOT_TOKEN, CHAT_ID) not found. Notifications will be disabled.")
            self.is_configured = False
        else:
            self.is_configured = True
            self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            logger.info("Telegram notifier initialized.")

    def send_notification(self, message: str):
        """
        Sends a message to the configured Telegram chat.

        Args:
            message (str): The message text to send.
        """
        if not self.is_configured:
            return

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown" # Or "HTML" if you prefer
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=5)
            response.raise_for_status()
            response_json = response.json()
            if not response_json.get("ok"):
                logger.error(f"Failed to send Telegram notification: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Could not send Telegram notification due to a network error: {e}")

if __name__ == "__main__":
    # A simple test for the notifier, uses print as logger isn't set up.
    print("--- Testing Telegram Notifier ---")

    try:
        notifier = TelegramNotifier()
        if notifier.is_configured:
            print("Notifier is configured. Sending a test message...")
            test_message = (
                "*Test Signal*\n"
                "--------------------\n"
                "Direction: *LONG*\n"
                "Symbol: *TESTING*\n"
                "LTP: *100.0*\n"
                "Strike: *100*\n"
                "CE ΔOI: *-35.50%*\n"
                "PE ΔOI: *15.20%*\n"
                "--------------------"
            )
            notifier.send_notification(test_message)
            print("Test message sent. Please check your Telegram chat.")
        else:
            print("Notifier is not configured. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")

    except Exception as e:
        print(f"An unexpected error occurred during the test: {e}")