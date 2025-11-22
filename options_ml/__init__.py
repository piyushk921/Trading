"""
Options ML Trading System

A production-grade intraday options ML system for Indian markets.
"""

__version__ = "1.0.0"
__author__ = "Options ML Team"

from .config import Config, get_config, load_config

__all__ = ["Config", "get_config", "load_config", "__version__"]
