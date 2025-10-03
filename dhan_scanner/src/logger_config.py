# src/logger_config.py

import sys
from loguru import logger
from .config import get_logging_config

def setup_logging():
    """
    Configures the application's logger using Loguru.

    This sets up a logger that writes to both the console and a rotating file,
    as specified in the application's configuration.
    """
    log_config = get_logging_config()

    # Default configuration if not specified
    log_file = log_config.get("log_file", "dhan_scanner/logs/scanner.log")
    max_size_mb = log_config.get("max_file_size_mb", 10)
    backup_count = log_config.get("backup_count", 7)
    log_level = log_config.get("level", "INFO").upper()

    # Remove the default handler to prevent duplicate console outputs
    logger.remove()

    # Add a handler for console output
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # Add a handler for file output with rotation
    logger.add(
        log_file,
        level=log_level,
        rotation=f"{max_size_mb} MB",
        retention=backup_count,
        enqueue=True,  # Make it thread-safe
        backtrace=True, # Show full stack trace on exceptions
        diagnose=True, # Add exception details
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    logger.info("Logging has been set up.")

if __name__ == "__main__":
    # Example of using the configured logger
    setup_logging()

    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("Caught a ZeroDivisionError!")

    print(f"\nLog file should be created at '{get_logging_config().get('log_file')}'.")