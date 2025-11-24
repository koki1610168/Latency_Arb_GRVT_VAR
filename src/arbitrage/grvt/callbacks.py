"""GRVT WebSocket callbacks for market data and order updates."""
import asyncio
import traceback

from pysdk.grvt_ccxt_logging_selector import logger
from .. import state
from .. import utils
from .. import config
from ..trading import loops as trading_loops
from ..trading import handlers as trading_handlers


async def grvt_mini_ticker_callback(message: dict) -> None:
    """Callback for GRVT mini ticker updates."""
    try:
        if "feed" in message:
            feed_data = message.get("feed", {})
            
            price_changed = False
            
            # Update best bid price
            if "best_bid_price" in feed_data:
                new_bid = utils.normalize_price(feed_data["best_bid_price"])
                if new_bid is not None and new_bid != state.grvt_bid:
                    state.grvt_bid = new_bid
                    price_changed = True
            
            # Update best ask price
            if "best_ask_price" in feed_data:
                new_ask = utils.normalize_price(feed_data["best_ask_price"])
                if new_ask is not None and new_ask != state.grvt_ask:
                    state.grvt_ask = new_ask
                    price_changed = True
            
            # If prices updated, check execution logic immediately
            if price_changed and state.grvt_api:
                # Create tasks to run execution logic concurrently without blocking WebSocket
                if not state.existing_position:
                    asyncio.create_task(trading_loops.try_entry(state.grvt_api))
                else:
                    asyncio.create_task(trading_loops.try_exit(state.grvt_api))

    except Exception as e:
        logger.error(f"Error in grvt_mini_ticker_callback: {e} {traceback.format_exc()}")


async def grvt_fill_callback(message: dict) -> None:
    """Callback for GRVT fill updates."""
    try:
        logger.info(f"Filled size: {message['feed']['size']} | Filled price: {message['feed']['price']}")
        # Fill handling logic is mostly superseded by market order approach
        # but keeping logs is useful for debugging.
        fill_qty = float(message['feed']['size'])
        if fill_qty > 0 and not message['feed']['is_buyer']:
            asyncio.create_task(trading_handlers.handle_entry_fill(fill_qty))

        if fill_qty > 0 and message['feed']['is_buyer']:
            asyncio.create_task(trading_handlers.handle_exit_fill(fill_qty))

    except Exception as e:
        logger.error(f"Error in grvt_fill_callback: {e} {traceback.format_exc()}")


# async def grvt_order_callback(message: dict) -> None:
#     """Callback for GRVT order updates."""
#     try:
#         logger.info(f"grvt_order_callback: {message=}")
#     except Exception as e:
#         logger.error(f"Error in grvt_order_callback: {e} {traceback.format_exc()}")


# async def grvt_state_callback(message: dict) -> None:
#     """Callback for GRVT state updates."""
#     try:
#         logger.info(f"grvt_state_callback: {message=}")
#     except Exception as e:
#         logger.error(f"Error in grvt_state_callback: {e} {traceback.format_exc()}")
