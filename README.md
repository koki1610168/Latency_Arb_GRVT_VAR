# Variational SDK & Arbitrage Trading System

This repository contains a high-performance, asynchronous Python SDK for Variational built from scratch, along with an arbitrage trading system integrating both Variational and GRVT exchanges.

## 🚀 Variational Python SDK (Built From Scratch)

The core of this project is the **Variational Python SDK**, a custom-built library designed for robust and efficient interaction with the Variational Omni API.

### Key Features
*   **Built from Scratch**: Designed specifically for this use case, offering full control over the architecture and optimization.
*   **Fully Asynchronous**: Built on `aiohttp` to handle high-concurrency trading operations without blocking.
*   **Type Safety**: Comprehensive type hinting and Pydantic-style dataclass models for all API resources (Instruments, Orders, Quotes).
*   **Robust Error Handling**: Custom exception hierarchy (`VariationalAuthenticationError`, `VariationalRateLimitError`, etc.) for precise control flow.
*   **Smart Retry Logic**: Automatic retries with exponential backoff for network issues and rate limits.
*   **Context Management**: Pythonic `async with` support for clean resource management.

For detailed documentation and usage examples, see the [SDK README](variational_python_sdk/README.md).

```python
# Quick Example
from variational_python_sdk import AsyncVariationalClient

async with AsyncVariationalClient(cookie="your-token") as client:
    quote = await client.quotes.get_indicative_quote(instrument, qty="1.0")
    print(f"Spread: {quote.spread}")
```

## ⚡ Arbitrage Trading System

The repository also includes a modular arbitrage bot (`src/arbitrage`) that executes strategies between GRVT and Variational.

### Modules
*   **`src/arbitrage/variational/`**: Integration using the custom Variational SDK.
*   **`src/arbitrage/grvt/`**: Integration with GRVT exchange via WebSocket streams.
*   **`src/arbitrage/trading/`**: core trading loops and logic for detecting spreads and executing cover orders.

### Tools & Scripts
*   **`compare_variational_grvt.py`**: A real-time data collection tool that subscribes to both exchanges and logs bid/ask spreads to CSV for analysis.
*   **`measure_grvt_fill.py`**: Analysis script for measuring order fill latency and execution quality on GRVT.

## 📦 Installation

1.  **Clone the repository**
    ```bash
    git clone <repo-url>
    cd grvt_var
    ```

2.  **Install dependencies**
    ```bash
    # Install Variational SDK dependencies
    pip install -r variational_python_sdk/requirements.txt
    
    # Install GRVT SDK dependencies
    pip install -e grvt-pysdk
    
    # Install utility dependencies
    pip install python-dotenv
    ```

3.  **Environment Setup**
    Create a `.env` file with your credentials:
    ```env
    VARIATIONAL_COOKIE=your_variational_cookie
    GRVT_API_KEY=your_grvt_api_key
    GRVT_PRIVATE_KEY=your_grvt_private_key
    GRVT_TRADING_ACCOUNT_ID=your_account_id
    ```

## 🛠 Usage

**Run the Comparison Tool:**
```bash
python compare_variational_grvt.py
```

**Run the Arbitrage Bot:**
```bash
python src/arbitrage_trading.py
```

## License

MIT

