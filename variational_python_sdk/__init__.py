"""Variational Python SDK - Official Python client for Variational Omni API."""

from .client import AsyncVariationalClient
from .models import Instrument, IndicativeQuote, MarketOrderRequest, OrderResponse
from .exceptions import (
    VariationalError,
    VariationalAPIError,
    VariationalAuthenticationError,
    VariationalRateLimitError,
    VariationalValidationError,
)
from .config import RetryConfig

__version__ = "1.0.0"

__all__ = [
    "AsyncVariationalClient",
    "Instrument",
    "IndicativeQuote",
    "MarketOrderRequest",
    "OrderResponse",
    "VariationalError",
    "VariationalAPIError",
    "VariationalAuthenticationError",
    "VariationalRateLimitError",
    "VariationalValidationError",
    "RetryConfig",
]

