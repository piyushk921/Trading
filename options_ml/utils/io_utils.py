"""
I/O utilities for saving and loading data.

Provides convenience functions for common serialization formats.
"""

import json
import pickle
from pathlib import Path
from typing import Any


def save_json(data: Any, filepath: str, indent: int = 2) -> None:
    """
    Save data to JSON file.

    Args:
        data: Data to save (must be JSON-serializable)
        filepath: Output file path
        indent: JSON indentation (default: 2)
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=indent, default=str)


def load_json(filepath: str) -> Any:
    """
    Load data from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        Loaded data
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def save_pickle(data: Any, filepath: str) -> None:
    """
    Save data to pickle file.

    Args:
        data: Data to save
        filepath: Output file path
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_pickle(filepath: str) -> Any:
    """
    Load data from pickle file.

    Args:
        filepath: Path to pickle file

    Returns:
        Loaded data
    """
    with open(filepath, 'rb') as f:
        return pickle.load(f)


def ensure_directory(filepath: str) -> None:
    """
    Ensure the parent directory of a file exists.

    Args:
        filepath: File path to check
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)


def file_exists(filepath: str) -> bool:
    """
    Check if a file exists.

    Args:
        filepath: Path to check

    Returns:
        True if file exists, False otherwise
    """
    return Path(filepath).exists()
