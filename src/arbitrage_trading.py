"""Main entry point for arbitrage trading between GRVT and Variational exchanges.

Strategy:
- Event-driven execution based on price updates (Callbacks).
- Monitors open_gap > OPEN_THRESHOLD -> Market Entry (Short GRVT, Buy Var)
- Monitors close_gap > CLOSE_THRESHOLD -> Market Exit (Buy GRVT, Sell Var)
"""
import asyncio
import signal
import sys
import logging
import logging.handlers
import queue
import os
import atexit
from datetime import datetime

from pysdk.grvt_ccxt_logging_selector import logger
from dotenv import load_dotenv

from src.arbitrage import state
from src.arbitrage.grvt import websocket as grvt_websocket
from src.arbitrage.variational import client as variational_client_module
from src.arbitrage.variational.client import variational_quote_loop
from src.arbitrage.grvt import orders as grvt_orders
from src.arbitrage.utils import SlackHandler

load_dotenv()


def setup_file_logging():
    """Configure asynchronous file logging for both app logs and price CSV."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # --- 1. Main Application Log Setup ---
    app_log_file = os.path.join(log_dir, f"trading_{timestamp}.log")
    
    # Actual handlers (File and Console)
    app_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    app_file_handler = logging.FileHandler(app_log_file)
    app_file_handler.setFormatter(app_formatter)
    app_file_handler.setLevel(logging.INFO)
    
    app_console_handler = logging.StreamHandler()
    app_console_handler.setFormatter(app_formatter)
    app_console_handler.setLevel(logging.INFO)

    # List of handlers to be managed by the listener
    handlers_list = [app_file_handler, app_console_handler]

    # --- Slack Handler Setup ---
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if slack_webhook:
        slack_handler = SlackHandler(slack_webhook)
        slack_handler.setFormatter(logging.Formatter('%(message)s'))
        slack_handler.setLevel(logging.INFO)
        
        # Filter to send only important notifications
        class NotificationFilter(logging.Filter):
            def filter(self, record):
                # Keywords to trigger notification
                keywords = ["Executing", "sent success", "failed", "Unbalanced"]
                return any(k in record.getMessage() for k in keywords) or record.levelno >= logging.WARNING

        slack_handler.addFilter(NotificationFilter())
        handlers_list.append(slack_handler)
        print("Slack notification enabled.")

    # Queue and Listener for App Log
    app_queue = queue.Queue(-1)
    app_listener = logging.handlers.QueueListener(app_queue, *handlers_list)
    app_listener.start()
    
    # QueueHandler for App Log
    app_queue_handler = logging.handlers.QueueHandler(app_queue)
    
    # Configure Root Logger
    root = logging.getLogger()
    if root.hasHandlers():
        root.handlers.clear()
    root.addHandler(app_queue_handler)
    root.setLevel(logging.INFO)
    
    # --- 2. Price CSV Log Setup ---
    csv_log_file = os.path.join(log_dir, f"prices_{timestamp}.csv")
    
    # CSV Handler (No formatting, just raw message)
    csv_file_handler = logging.FileHandler(csv_log_file)
    csv_file_handler.setFormatter(logging.Formatter('%(message)s'))
    csv_file_handler.setLevel(logging.INFO)
    
    # Queue and Listener for CSV
    csv_queue = queue.Queue(-1)
    csv_listener = logging.handlers.QueueListener(csv_queue, csv_file_handler)
    csv_listener.start()
    
    # Write CSV Header synchronously once
    with open(csv_log_file, 'w') as f:
        f.write("timestamp,grvt_bid,grvt_ask,var_bid,var_ask,open_gap,close_gap\n")
    
    # Configure Dedicated CSV Logger
    price_logger = logging.getLogger("price_csv")
    price_logger.handlers = [logging.handlers.QueueHandler(csv_queue)]
    price_logger.setLevel(logging.INFO)
    price_logger.propagate = False  # Don't send to root logger
    
    # Ensure listeners stop on exit
    atexit.register(app_listener.stop)
    atexit.register(csv_listener.stop)
    
    logger.info(f"Async logging initialized. App: {app_log_file}, CSV: {csv_log_file}")



async def trading_main():
    """Main trading function (keeps process alive)."""
    # Start Variational quote loop (This loop now also triggers execution logic)
    quote_task = asyncio.create_task(variational_quote_loop())
    
    logger.info("Trading system started. Waiting for price updates...")
    
    try:
        while state.running:
            # The actual trading logic is now triggered by callbacks in:
            # - src/arbitrage/grvt/callbacks.py (GRVT updates)
            # - src/arbitrage/variational/client.py (Variational updates)
            # We just keep the main loop alive.
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info("Trading loop cancelled")
    except Exception as e:
        logger.error(f"Error in trading loop: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Cancel quote task
        quote_task.cancel()
        try:
            await quote_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Trading cycle complete!")


async def shutdown(loop):
    """Clean up resources."""
    logger.info("Shutting down gracefully...")
    
    state.running = False
    
    grvt_api_ref = state.grvt_api
    variational_client_ref = state.variational_client
    
    # Close Variational client
    if variational_client_ref is not None:
        try:
            await variational_client_ref.__aexit__(None, None, None)
        except Exception as e:
            logger.debug(f"Error closing Variational client: {e}")
    
    # Clean up GRVT API reference
    if grvt_api_ref is not None:
        state.grvt_api = None
    if variational_client_ref is not None:
        state.variational_client = None
    
    logger.info("Shutdown complete.")


if __name__ == "__main__":
    # Setup logging before anything else
    setup_file_logging()
    
    loop = asyncio.get_event_loop()
    state.running = True
    
    # Set up connections
    grvt_api = loop.run_until_complete(grvt_websocket.setup_grvt_websocket(loop))
    if not grvt_api:
        logger.error("Failed to set up GRVT WebSocket")
        sys.exit(1)
    
    variational_client = loop.run_until_complete(variational_client_module.setup_variational_client())
    if not variational_client:
        logger.error("Failed to set up Variational client")
        sys.exit(1)
    
    def signal_handler():
        """Handle shutdown signals."""
        asyncio.create_task(shutdown(loop))
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    # Wait for subscriptions to initialize
    loop.run_until_complete(asyncio.sleep(5))
    
    # Start trading
    try:
        loop.run_until_complete(trading_main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        loop.run_until_complete(shutdown(loop))
    
    loop.close()
