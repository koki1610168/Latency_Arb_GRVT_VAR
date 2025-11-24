"""Retry logic with exponential backoff."""
import asyncio
import random
from functools import wraps
from typing import Callable, TypeVar, Optional

from ..exceptions import (
    VariationalAPIError,
    VariationalAuthenticationError,
    VariationalRateLimitError,
)
from ..config import RetryConfig, DEFAULT_MAX_RETRIES_NETWORK, DEFAULT_MAX_RETRIES_5XX, DEFAULT_MAX_RETRIES_429

T = TypeVar("T")


def _add_jitter(value: float, jitter_factor: float = 0.1) -> float:
    """Add random jitter to backoff value."""
    jitter = value * jitter_factor * random.random()
    return value + jitter


async def retry_with_backoff(
    func: Callable[..., T],
    *args,
    retry_config: Optional[RetryConfig] = None,
    **kwargs,
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        *args: Positional arguments for func
        retry_config: Retry configuration (uses defaults if None)
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func
        
    Raises:
        VariationalAuthenticationError: For 401/403 (no retry)
        VariationalRateLimitError: For 429 (special retry logic)
        VariationalAPIError: For other API errors
    """
    if retry_config is None:
        retry_config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(max(retry_config.max_retries_network, retry_config.max_retries_5xx, retry_config.max_retries_429) + 1):
        try:
            return await func(*args, **kwargs)
        except VariationalAuthenticationError:
            # Never retry auth errors
            raise
        except VariationalRateLimitError as e:
            # Special handling for rate limits
            if attempt < retry_config.max_retries_429:
                backoff = min(
                    retry_config.backoff_base * (2 ** attempt),
                    retry_config.backoff_max
                )
                backoff = _add_jitter(backoff)
                await asyncio.sleep(backoff)
                last_exception = e
                continue
            raise
        except VariationalAPIError as e:
            # Handle 5xx errors
            if 500 <= e.status_code < 600:
                if attempt < retry_config.max_retries_5xx:
                    backoff = retry_config.backoff_base * (2 ** attempt)
                    backoff = _add_jitter(backoff)
                    await asyncio.sleep(backoff)
                    last_exception = e
                    continue
            raise
        except (asyncio.TimeoutError, ConnectionError, OSError) as e:
            # Network errors
            if attempt < retry_config.max_retries_network:
                backoff = retry_config.backoff_base * (2 ** attempt)
                backoff = _add_jitter(backoff)
                await asyncio.sleep(backoff)
                last_exception = e
                continue
            raise
        except Exception as e:
            # Unexpected errors - don't retry
            raise
    
    # If we exhausted retries, raise the last exception
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed unexpectedly")


def with_retry(retry_config: Optional[RetryConfig] = None):
    """
    Decorator to add retry logic to async functions.
    
    Usage:
        @with_retry()
        async def my_api_call():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(func, *args, retry_config=retry_config, **kwargs)
        return wrapper
    return decorator

