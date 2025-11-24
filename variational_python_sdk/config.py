"""Configuration constants for Variational API."""
from dataclasses import dataclass
from typing import Optional


# API Endpoints
BASE_URL = "https://omni.variational.io"
QUOTES_ENDPOINT = f"{BASE_URL}/api/quotes/indicative"
ORDERS_ENDPOINT = f"{BASE_URL}/api/orders/new/market"

# Default settings
DEFAULT_TIMEOUT = 5.0
DEFAULT_USER_AGENT = "variational-python-sdk/1.0"

# Retry settings
DEFAULT_MAX_RETRIES_NETWORK = 3
DEFAULT_MAX_RETRIES_5XX = 2
DEFAULT_MAX_RETRIES_429 = 5
DEFAULT_BACKOFF_BASE = 1.0
DEFAULT_BACKOFF_MAX = 60.0


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries_network: int = DEFAULT_MAX_RETRIES_NETWORK
    max_retries_5xx: int = DEFAULT_MAX_RETRIES_5XX
    max_retries_429: int = DEFAULT_MAX_RETRIES_429
    backoff_base: float = DEFAULT_BACKOFF_BASE
    backoff_max: float = DEFAULT_BACKOFF_MAX

