"""Configuration constants for arbitrage trading."""

# Spread thresholds
OPEN_THRESHOLD = 0.0025
CLOSE_THRESHOLD = -0.0014  # Place cover when spread < this

# Default order amounts
DEFAULT_ORDER_AMOUNT = 0.01

# Timeout values
QUOTE_FETCH_INTERVAL = 0.1  # Seconds between quote fetches
QUOTE_FETCH_BACKOFF_MAX = 5.0  # Maximum backoff seconds on error
ORDER_CHECK_INTERVAL = 0.1  # Seconds between order status checks
STATUS_CHECK_INTERVAL = 2.0  # Seconds between periodic status checks
ORDER_TIMEOUT = 60.0  # Seconds to wait for order fill before timeout

# Price change threshold for requoting
PRICE_CHANGE_THRESHOLD = 0.01  # Minimum price change to trigger requote

# Variational order settings
VARIATIONAL_MAX_SLIPPAGE = 0.005  # 0.5% max slippage
