"""Compare BTC bid/ask prices from Variational and GRVT exchanges.

This script:
1. Fetches BTC/USDC quotes from Variational using variational_python_sdk
2. Subscribes to GRVT BTC_USDT_Perp mini ticker using grvt-pysdk (referencing test_grvt_ws.py)
3. Logs both bid/ask prices to a CSV file with timestamps
"""
import asyncio
import csv
import os
import signal
import sys
from datetime import datetime
from decimal import Decimal

from pysdk.grvt_ccxt_env import GrvtEnv, GrvtWSEndpointType
from pysdk.grvt_ccxt_logging_selector import logger
from pysdk.grvt_ccxt_ws import GrvtCcxtWS
from variational_python_sdk.client import AsyncVariationalClient
from variational_python_sdk.models import Instrument
from variational_python_sdk.exceptions import VariationalAuthenticationError, VariationalAPIError
from dotenv import load_dotenv

load_dotenv()

# Global state
grvt_bid = None
grvt_ask = None
grvt_api = None
variational_client = None
latest_variational_quote = None  # Store latest Variational quote
running = True
csv_file = None
csv_writer = None
csv_file_handle = None


def normalize_price(price):
    """Normalize price to string format."""
    if price is None:
        return None
    if isinstance(price, (int, float)):
        return str(price)
    if isinstance(price, str):
        return price
    return str(price)


async def grvt_mini_ticker_callback(message: dict) -> None:
    """Callback for GRVT mini ticker updates to get best bid and ask prices.
    
    Logs to CSV when GRVT quote is received, using the latest Variational quote.
    """
    global grvt_bid, grvt_ask, latest_variational_quote
    try:
        if "feed" in message:
            feed_data = message.get("feed", {})
            bid_updated = False
            ask_updated = False
            
            if "best_bid_price" in feed_data:
                grvt_bid = normalize_price(feed_data["best_bid_price"])
                bid_updated = True
            if "best_ask_price" in feed_data:
                grvt_ask = normalize_price(feed_data["best_ask_price"])
                ask_updated = True
            
            # Log to CSV when GRVT quote is received
            if bid_updated or ask_updated:
                logger.info(f"GRVT update received - Bid: {grvt_bid}, Ask: {grvt_ask}")
                
                # Log to CSV with latest Variational quote (if available)
                log_to_csv(latest_variational_quote, grvt_bid, grvt_ask)
                
                # Also log to console
                if latest_variational_quote:
                    logger.info(
                        f"Logged: Variational - Bid: {latest_variational_quote.bid}, "
                        f"Ask: {latest_variational_quote.ask} | "
                        f"GRVT - Bid: {grvt_bid}, Ask: {grvt_ask}"
                    )
                else:
                    logger.info(
                        f"Logged: Variational - (no quote yet) | "
                        f"GRVT - Bid: {grvt_bid}, Ask: {grvt_ask}"
                    )
    except Exception as e:
        logger.error(f"Error in grvt_mini_ticker_callback: {e}")


async def grvt_ws_subscribe(api: GrvtCcxtWS, args_list: dict) -> None:
    """Subscribes to Websocket channels/feeds in args list.
    
    Based on grvt_ws_subscribe from test_grvt_ws.py
    """
    for stream, (callback, ws_endpoint_type, params) in args_list.items():
        logger.info(f"Subscribing to {stream} {params=}")
        await api.subscribe(
            stream=stream,
            callback=callback,
            ws_end_point_type=ws_endpoint_type,
            params=params,
        )
        await asyncio.sleep(0)


async def setup_grvt_websocket(loop) -> GrvtCcxtWS:
    """Set up GRVT WebSocket connection and subscribe to BTC mini ticker.
    
    Based on subscribe() function from test_grvt_ws.py
    """
    params = {
        "api_key": os.getenv("GRVT_API_KEY"),
        "trading_account_id": os.getenv("GRVT_TRADING_ACCOUNT_ID"),
        "api_ws_version": os.getenv("GRVT_WS_STREAM_VERSION", "v1"),
    }
    if os.getenv("GRVT_PRIVATE_KEY"):
        params["private_key"] = os.getenv("GRVT_PRIVATE_KEY")
    env = GrvtEnv(os.getenv("GRVT_ENV", "testnet"))

    api = GrvtCcxtWS(env, loop, logger, parameters=params)
    await api.initialize()
    
    pub_args_dict = {
        # Market Data - mini ticker for BTC best bid and ask
        "mini.s": (
            grvt_mini_ticker_callback,
            None,  # use default endpoint
            {"instrument": "BTC_USDT_Perp"},
        ),
    }
    
    try:
        await grvt_ws_subscribe(api, pub_args_dict)
        logger.info("GRVT WebSocket subscribed successfully")
    except Exception as e:
        logger.error(f"Error subscribing to GRVT WebSocket: {e}")
        return None
    
    return api


async def get_variational_quote(client: AsyncVariationalClient, qty: str = "0.01"):
    """Get an indicative quote for BTC/USDC from Variational.
    
    Based on get_btc_usdc_quote from get_btc_usdc_quotes.py
    """
    try:
        # Create instrument for BTC/USDC perpetual future
        instrument = Instrument(
            underlying="BTC",
            funding_interval_s=3600,
            settlement_asset="USDC",
            instrument_type="perpetual_future",
        )
        
        # Get indicative quote
        quote = await client.quotes.get_indicative_quote(instrument, qty=qty)
        return quote
        
    except VariationalAuthenticationError as e:
        logger.error(f"Variational authentication failed: {e}")
        return None
    except VariationalAPIError as e:
        logger.error(f"Variational API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting Variational quote: {e}")
        return None


async def setup_variational_client():
    """Set up Variational client."""
    cookie = os.environ.get("VARIATIONAL_COOKIE")
    if not cookie:
        logger.error("VARIATIONAL_COOKIE environment variable not set")
        return None
    
    client = AsyncVariationalClient(cookie=cookie)
    # Initialize the session by entering the context manager
    await client.__aenter__()
    logger.info("Variational client initialized")
    return client


def setup_csv_logger(filename: str = "variational_grvt_comparison.csv"):
    """Set up CSV file for logging bid/ask prices."""
    global csv_file, csv_writer, csv_file_handle
    
    csv_file = filename
    csv_file_handle = open(csv_file, 'w', newline='')
    csv_writer = csv.writer(csv_file_handle)
    
    # Write header
    csv_writer.writerow([
        "timestamp",
        "variational_bid",
        "variational_ask",
        "variational_mid",
        "variational_spread",
        "grvt_bid",
        "grvt_ask",
        "grvt_spread",
        "bid_diff",
        "ask_diff",
    ])
    csv_file_handle.flush()
    logger.info(f"CSV logger initialized: {csv_file}")


def log_to_csv(variational_quote, grvt_bid_val, grvt_ask_val):
    """Log bid/ask prices to CSV file."""
    global csv_writer
    
    if csv_writer is None:
        return
    
    timestamp = datetime.now().isoformat()
    
    # Extract Variational data
    var_bid = None
    var_ask = None
    var_mid = None
    var_spread = None
    
    if variational_quote:
        var_bid = str(variational_quote.bid) if variational_quote.bid else None
        var_ask = str(variational_quote.ask) if variational_quote.ask else None
        var_mid = str(variational_quote.mid) if variational_quote.mid else None
        var_spread = str(variational_quote.spread) if variational_quote.spread else None
    
    # Calculate GRVT spread if both bid and ask are available
    grvt_spread = None
    if grvt_bid_val and grvt_ask_val:
        try:
            bid_float = float(grvt_bid_val)
            ask_float = float(grvt_ask_val)
            grvt_spread = str(ask_float - bid_float)
        except (ValueError, TypeError):
            pass
    
    # Calculate differences
    bid_diff = None
    ask_diff = None
    if var_bid and grvt_bid_val:
        try:
            bid_diff = str(float(var_bid) - float(grvt_bid_val))
        except (ValueError, TypeError):
            pass
    if var_ask and grvt_ask_val:
        try:
            ask_diff = str(float(var_ask) - float(grvt_ask_val))
        except (ValueError, TypeError):
            pass
    
    # Write to CSV
    csv_writer.writerow([
        timestamp,
        var_bid,
        var_ask,
        var_mid,
        var_spread,
        grvt_bid_val,
        grvt_ask_val,
        grvt_spread,
        bid_diff,
        ask_diff,
    ])
    csv_file_handle.flush()


async def variational_quote_loop():
    """Continuously fetch Variational quotes and update latest quote.
    
    Note: Logging to CSV happens in GRVT callback when GRVT quote is received.
    This loop just keeps the latest Variational quote updated.
    """
    global variational_client, latest_variational_quote, running
    
    logger.info("Starting Variational quote loop...")
    
    while running:
        try:
            # Get Variational quote
            quote = await get_variational_quote(variational_client, qty="0.01")
            
            if quote:
                # Update latest quote (used by GRVT callback for logging)
                latest_variational_quote = quote
                
                logger.info(
                    f"Variational quote updated - Bid: {quote.bid}, Ask: {quote.ask}, "
                    f"Mid: {quote.mid}"
                )
            else:
                logger.warning("Failed to get Variational quote")
            
            # Wait before next quote (fetch every 0.5 seconds)
            await asyncio.sleep(0.5)
            
        except asyncio.CancelledError:
            logger.info("Variational quote loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in Variational quote loop: {e}")
            await asyncio.sleep(0.5)


async def main():
    """Main entry point."""
    global grvt_api, variational_client, running, csv_file_handle, loop
    
    logger.info("Starting Variational vs GRVT price comparison...")
    
    # Set up CSV logger
    setup_csv_logger()
    
    try:
        loop = asyncio.get_event_loop()
        
        # Set up GRVT WebSocket
        logger.info("Setting up GRVT WebSocket...")
        grvt_api = await setup_grvt_websocket(loop)
        if not grvt_api:
            logger.error("Failed to set up GRVT WebSocket")
            return
        
        # Wait a bit for GRVT connection to establish
        await asyncio.sleep(2)
        
        # Set up Variational client
        logger.info("Setting up Variational client...")
        variational_client = await setup_variational_client()
        if not variational_client:
            logger.error("Failed to set up Variational client")
            return
        
        logger.info("Both connections established. Starting data collection...")
        logger.info("Press Ctrl+C to stop\n")
        
        # Run Variational quote loop
        await variational_quote_loop()
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        # Cleanup
        running = False
        
        if variational_client:
            try:
                # Properly exit the async context manager
                await variational_client.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing Variational client: {e}")
        
        if grvt_api:
            try:
                # Clean up GRVT WebSocket connection
                del grvt_api
            except Exception as e:
                logger.error(f"Error closing GRVT connection: {e}")
        
        if csv_file_handle:
            csv_file_handle.close()
            logger.info(f"CSV file saved: {csv_file}")
        
        logger.info("Shutdown complete")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global running
    logger.info("\nReceived shutdown signal. Stopping...")
    running = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

