# Arbitrage Trading System - Refactored Structure

This directory contains the refactored arbitrage trading system, organized into logical modules for better maintainability.

## Directory Structure

```
src/
├── arbitrage/
│   ├── __init__.py
│   ├── config.py              # Configuration constants
│   ├── state.py               # Global state management
│   ├── utils.py               # Utility functions
│   ├── grvt/                  # GRVT exchange integration
│   │   ├── __init__.py
│   │   ├── callbacks.py      # WebSocket callbacks
│   │   ├── websocket.py      # WebSocket setup
│   │   └── orders.py         # Order management
│   ├── variational/           # Variational exchange integration
│   │   ├── __init__.py
│   │   ├── client.py         # Client setup and quotes
│   │   └── orders.py         # Order management
│   └── trading/               # Trading logic
│       ├── __init__.py
│       ├── loops.py          # Trading loops
│       └── handlers.py       # Fill handlers
└── arbitrage_trading.py      # Main entry point
```

## Module Descriptions

### `arbitrage/config.py`
Configuration constants including:
- Spread thresholds (SHORT, COVER)
- Default order amounts
- Timeout values
- Price change thresholds

### `arbitrage/state.py`
Centralized global state:
- Price tracking (GRVT and Variational)
- Order tracking (IDs, fill status, quantities)
- Position tracking
- Events (bid/ask/spread changes)
- API instances

### `arbitrage/utils.py`
Utility functions:
- `normalize_price()` - Convert prices to float
- `calculate_spread()` - Calculate bid spread between exchanges

### `arbitrage/grvt/`
GRVT exchange integration:
- **callbacks.py**: WebSocket callbacks for market data and order updates
- **websocket.py**: WebSocket connection setup and subscription management
- **orders.py**: Order creation and cancellation functions

### `arbitrage/variational/`
Variational exchange integration:
- **client.py**: Client setup, quote fetching, and quote loop
- **orders.py**: Market order placement (buy/sell)

### `arbitrage/trading/`
Trading strategy logic:
- **loops.py**: Main trading loops (short_order_loop, cover_order_loop)
- **handlers.py**: Event handlers for order fills

### `arbitrage_trading.py`
Main entry point that:
- Initializes connections
- Sets up signal handlers
- Orchestrates the trading flow
- Handles shutdown

## Usage

Run the main script:
```bash
python src/arbitrage_trading.py
```

## Benefits

1. **Modularity**: Each module has a single, clear responsibility
2. **Maintainability**: Easy to locate and modify specific functionality
3. **Testability**: Modules can be tested independently
4. **Scalability**: Easy to add new exchanges or features
5. **Readability**: Smaller, focused files are easier to understand








