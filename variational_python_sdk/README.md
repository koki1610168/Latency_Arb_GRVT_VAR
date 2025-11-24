# Variational Python SDK

Official async Python client for interacting with the Variational Omni API.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install directly
pip install aiohttp
```

## Quick Start

```python
import asyncio
from variational_python_sdk import AsyncVariationalClient, Instrument

async def main():
    async with AsyncVariationalClient(cookie="your-vr-token-here") as client:
        # Create an instrument
        instrument = Instrument(
            underlying="SOL",
            funding_interval_s=3600,
            settlement_asset="USDC",
            instrument_type="perpetual_future",
        )
        
        # Get an indicative quote
        quote = await client.quotes.get_indicative_quote(instrument, qty="1.0")
        print(f"Bid: {quote.bid}, Ask: {quote.ask}")
        print(f"Mid: {quote.mid}, Spread: {quote.spread}")

asyncio.run(main())
```

## Features

- **Async-Only**: Built on `aiohttp` for high-performance async operations
- **Type Safety**: Full type hints and dataclass models
- **Error Handling**: Custom exceptions for different error types
- **Retry Logic**: Automatic retry with exponential backoff for network errors
- **Context Managers**: Use `async with` for automatic resource cleanup
- **Extensible**: Easy to add new API endpoints

## API Reference

### AsyncVariationalClient

Main async client for API interactions.

```python
client = AsyncVariationalClient(
    cookie="your-vr-token",  # Optional, can also use env var
    base_url="https://omni.variational.io",  # Optional
    timeout=5.0,  # Optional, request timeout
    retry_config=RetryConfig(...),  # Optional, retry configuration
)
```

#### Methods

- `quotes.get_indicative_quote(instrument, qty)` - Get indicative quote
- `orders.place_market_order(order)` - Place a market order
- `close()` - Close the HTTP session

### Models

#### Instrument

Represents a trading instrument configuration.

```python
instrument = Instrument(
    underlying="SOL",
    funding_interval_s=3600,
    settlement_asset="USDC",
    instrument_type="perpetual_future",
)
```

#### IndicativeQuote

Represents a quote response with bid, ask, and metadata.

```python
quote = await client.quotes.get_indicative_quote(instrument, qty="1.0")
print(quote.bid)      # Best bid price
print(quote.ask)      # Best ask price
print(quote.mid)       # Mid price (property)
print(quote.spread)    # Spread (property)
print(quote.quote_id)  # Quote ID for placing orders
```

#### MarketOrderRequest

Represents a market order request.

```python
order = MarketOrderRequest(
    quote_id=quote.quote_id,
    side="buy",  # or "sell"
    is_reduce_only=False,
    max_slippage=0.005,
)
result = await client.orders.place_market_order(order)
```

### Exceptions

- `VariationalError` - Base exception
- `VariationalAPIError` - General API errors
- `VariationalAuthenticationError` - Authentication failures (401, 403)
- `VariationalRateLimitError` - Rate limit exceeded (429)
- `VariationalValidationError` - Request validation errors

### Retry Configuration

The SDK includes automatic retry logic with exponential backoff:

- **Network errors** (connection/timeout): 3 retries with exponential backoff (1s, 2s, 4s) + jitter
- **5xx server errors**: 2 retries with exponential backoff
- **429 rate limit**: Up to 5 retries with exponential backoff (max 60s)
- **401/403 auth errors**: No retry, raise immediately

You can customize retry behavior:

```python
from variational_python_sdk import AsyncVariationalClient, RetryConfig

retry_config = RetryConfig(
    max_retries_network=5,
    max_retries_5xx=3,
    max_retries_429=10,
    backoff_base=2.0,
    backoff_max=120.0,
)

client = AsyncVariationalClient(
    cookie="token",
    retry_config=retry_config,
)
```

## Examples

See `examples/async_usage.py` for complete usage examples including:
- Getting quotes
- Placing market orders
- Using dict instead of model classes
- Error handling

## Environment Variables

- `VARIATIONAL_COOKIE` - Authentication cookie (vr-token)

## License

MIT

