"""Headless Steel Tide rules. Authoritative for Neon Rift until a UE module exists."""

__version__ = "0.1.0"

from .config import load_config
from .match import SteelTideMatch

__all__ = ["SteelTideMatch", "__version__", "load_config"]
