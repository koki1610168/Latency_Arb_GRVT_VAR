"""Trading execution logic triggered by price updates."""
import asyncio
import logging
from datetime import datetime

from pysdk.grvt_ccxt_logging_selector import logger
from pysdk.grvt_ccxt_ws import GrvtCcxtWS
from .. import state
from .. import utils
from .. import config
from ..grvt import orders as grvt_orders
from ..variational import orders as variational_orders

# Lock to prevent double execution if both GRVT and Variational update triggering simultaneously
_execution_lock = asyncio.Lock()

# Get dedicated price logger (configured in main)
price_logger = logging.getLogger("price_csv")


def log_price_update():
    """Log current prices to CSV asynchronously."""
    # Check if all prices are available
    if None in (state.grvt_bid, state.grvt_ask, state.variational_bid, state.variational_ask):
        return

    ts = datetime.now().isoformat()
    open_gap = utils.calculate_open_gap()
    close_gap = utils.calculate_close_gap()
    
    # Handle None values for gaps
    open_gap_str = f"{open_gap}" if open_gap is not None else ""
    close_gap_str = f"{close_gap}" if close_gap is not None else ""
    
    # Format: timestamp,grvt_bid,grvt_ask,var_bid,var_ask,open_gap,close_gap
    log_msg = f"{ts},{state.grvt_bid},{state.grvt_ask},{state.variational_bid},{state.variational_ask},{open_gap_str},{close_gap_str}"
    
    # Send to queue (non-blocking)
    price_logger.info(log_msg)


async def try_entry(api: GrvtCcxtWS) -> None:
    """
    Check entry conditions and execute orders if met.
    Intended to be called from price update callbacks.
    """
    # Log prices on every update check
    log_price_update()

    if state.existing_position:
        return

    # Quick check before acquiring lock
    gap = utils.calculate_open_gap()
    if gap is not None:
        logger.info(
            f"[Entry Check] Open Gap: {gap:.6f} (Thresh: {config.OPEN_THRESHOLD}) | "
            f"Close Gap: {utils.calculate_close_gap():.6f} (Thresh: {config.CLOSE_THRESHOLD}) | "
            f"GRVT Bid: {state.grvt_bid} | Var Ask: {state.variational_ask} | "
            f"GRVT Ask: {state.grvt_ask} | Var Bid: {state.variational_bid}"
        )
    if gap is None or gap <= config.OPEN_THRESHOLD:
        return

    if _execution_lock.locked():
        return

    async with _execution_lock:
        # Re-check state inside lock
        if state.existing_position:
            return
            
        gap = utils.calculate_open_gap()
        if gap is None or gap <= config.OPEN_THRESHOLD:
            return

        logger.info(f"Open gap {gap:.5f} > {config.OPEN_THRESHOLD}. Executing ENTRY market orders!")
        
        amount = config.DEFAULT_ORDER_AMOUNT
        
        # Execute both orders in parallel
        grvt_task = grvt_orders.grvt_create_mkt_order(
            api, 
            side="sell", 
            qty=amount
        )
        var_task = variational_orders.variational_buy(
            state.variational_client, 
            qty=str(amount)
        )
        
        results = await asyncio.gather(grvt_task, var_task, return_exceptions=True)
        grvt_order_id = results[0]
        var_success = results[1]
        
        # Logging results
        if isinstance(grvt_order_id, Exception):
            logger.error(f"GRVT entry failed: {grvt_order_id}")
            grvt_order_id = ""
        elif grvt_order_id:
            logger.info(f"GRVT entry sent: {grvt_order_id}")
            
        if isinstance(var_success, Exception):
            logger.error(f"Variational entry failed: {var_success}")
            var_success = False
        elif var_success:
            logger.info("Variational entry sent success")

        # Update state
        if grvt_order_id and var_success:
            state.grvt_order_id = grvt_order_id
            state.existing_position = True
        elif grvt_order_id:
            logger.warning("Only GRVT entry succeeded. Unbalanced.")
        elif var_success:
            logger.warning("Only Variational entry succeeded. Unbalanced.")


async def try_exit(api: GrvtCcxtWS) -> None:
    """
    Check exit conditions and execute orders if met.
    Intended to be called from price update callbacks.
    """
    if not state.existing_position:
        return
    
    # Log prices on every update check
    log_price_update()

    # Quick check
    gap = utils.calculate_close_gap()
    if gap is not None:
        logger.info(
            f"[Exit Check] Gap: {gap:.6f} (Thresh: {config.CLOSE_THRESHOLD}) | "
            f"GRVT Ask: {state.grvt_ask} | Var Bid: {state.variational_bid}"
        )
    if gap is None or gap <= config.CLOSE_THRESHOLD:
        return

    if _execution_lock.locked():
        return

    async with _execution_lock:
        # Re-check inside lock
        if not state.existing_position:
            return
            
        gap = utils.calculate_close_gap()
        if gap is None or gap <= config.CLOSE_THRESHOLD:
            return

        logger.info(f"Close gap {gap:.5f} > {config.CLOSE_THRESHOLD}. Executing EXIT market orders!")
        
        amount = config.DEFAULT_ORDER_AMOUNT
        
        grvt_task = grvt_orders.grvt_create_mkt_order(
            api, 
            side="buy", 
            qty=amount,
            client_order_id="",
            reduce_only=True,
        )
        var_task = variational_orders.variational_sell(
            state.variational_client, 
            qty=str(amount)
        )
        
        results = await asyncio.gather(grvt_task, var_task, return_exceptions=True)
        grvt_order_id = results[0]
        var_success = results[1]
        
        if isinstance(grvt_order_id, Exception):
            logger.error(f"GRVT exit failed: {grvt_order_id}")
            grvt_order_id = ""
        elif grvt_order_id:
            logger.info(f"GRVT exit sent: {grvt_order_id}")
            
        if isinstance(var_success, Exception):
            logger.error(f"Variational exit failed: {var_success}")
            var_success = False
        elif var_success:
            logger.info("Variational exit sent success")
            
        if grvt_order_id and var_success:
            state.existing_position = False
            state.grvt_order_id = None
        elif grvt_order_id or var_success:
            logger.warning("One side failed to close. Unbalanced.")
