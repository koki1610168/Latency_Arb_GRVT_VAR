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
            f"Close Gap: {gap:.6f} (Thresh: {config.CLOSE_THRESHOLD}) | "
            f"GRVT Bid: {state.grvt_bid} | Var Ask: {state.variational_ask} | "
            f"GRVT Ask: {state.grvt_ask} | Var Bid: {state.variational_bid}"
        )

    if _execution_lock.locked():
        return

    async with _execution_lock:
        # Re-check state inside lock
        if state.existing_position:
            return
            
        gap = utils.calculate_open_gap()
        grvt_best_ask = state.grvt_ask

        if gap is None:
            return

        # --- アクティブな指値注文がある場合の管理ロジック ---
        if state.active_limit_order_id:
            # 注文があるときに、gapが閾値を下回ったらキャンセル
            if gap <= config.OPEN_THRESHOLD:
                logger.info(f"Gap {gap:.5f} <= Threshold. Cancelling active order {state.active_limit_order_id}")
                await grvt_orders.grvt_cancel_order(api, state.active_limit_order_id)
                state.active_limit_order_id = None
                state.active_limit_order_price = None
                return

            if state.active_limit_order_price != grvt_best_ask:
                logger.info(f"Price moved ({state.active_limit_order_price} -> {grvt_best_ask}). Replacing order.")
                
                # キャンセル
                await grvt_orders.grvt_cancel_order(api, state.active_limit_order_id)
                
                # 新しいBest Askで再発注
                amount = config.DEFAULT_ORDER_AMOUNT
                new_order_id = await grvt_orders.grvt_create_limit_order(
                    api,
                    side="sell",
                    price=grvt_best_ask,
                    qty=amount,
                    post_only=True,
                    reduce_only=False
                )
                
                if new_order_id:
                    state.active_limit_order_id = new_order_id
                    state.active_limit_order_price = grvt_best_ask
                    logger.info(f"Replaced order: {new_order_id} at {grvt_best_ask}")
                else:
                    state.active_limit_order_id = None
                    state.active_limit_order_price = None
                return

        else:
            # Gapが閾値を超えたらBest Askに指値注文
            if gap > config.OPEN_THRESHOLD:
                logger.info(f"Open gap {gap:.5f} > {config.OPEN_THRESHOLD}. Placing Maker Limit Order at {grvt_best_ask}")
                
                amount = config.DEFAULT_ORDER_AMOUNT
                order_id = await grvt_orders.grvt_create_limit_order(
                    api,
                    side="sell",
                    price=grvt_best_ask,
                    qty=amount,
                    post_only=True,
                    reduce_only=False
                )
                
                if order_id:
                    state.active_limit_order_id = order_id
                    state.active_limit_order_price = grvt_best_ask
                    logger.info(f"Entry order placed: {order_id}")
                else:
                    logger.error("Failed to place entry limit order")
        


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
    gap = utils.calculate_open_gap()
    if gap is not None:
        logger.info(
            f"[Exit Check] Close Gap: {gap:.6f} (Thresh: {config.CLOSE_THRESHOLD}) | "
            f"Open Gap: {gap:.6f} (Thresh: {config.OPEN_THRESHOLD}) | "
            f"GRVT Bid: {state.grvt_bid} | Var Ask: {state.variational_ask} | "
            f"GRVT Ask: {state.grvt_ask} | Var Bid: {state.variational_bid}"
        )

    if _execution_lock.locked():
        return

    async with _execution_lock:
        # Re-check inside lock
        if not state.existing_position:
            return
            
        gap = utils.calculate_close_gap()
        grvt_best_bid = state.grvt_bid

        if gap is None:
            return


        # --- アクティブな指値注文がある場合の管理ロジック ---
        if state.active_limit_order_id:
            # 注文があるときに、gapが閾値を下回ったらキャンセル
            if gap <= config.CLOSE_THRESHOLD:
                logger.info(f"Gap {gap:.5f} <= Threshold. Cancelling active order {state.active_limit_order_id}")
                await grvt_orders.grvt_cancel_order(api, state.active_limit_order_id)
                state.active_limit_order_id = None
                state.active_limit_order_price = None
                return

            if state.active_limit_order_price != grvt_best_bid:
                logger.info(f"Price moved ({state.active_limit_order_price} -> {grvt_best_bid}). Replacing order.")
                
                # キャンセル
                await grvt_orders.grvt_cancel_order(api, state.active_limit_order_id)
                
                # 新しいBest Askで再発注
                amount = config.DEFAULT_ORDER_AMOUNT
                new_order_id = await grvt_orders.grvt_create_limit_order(
                    api,
                    side="buy",
                    price=grvt_best_bid,
                    qty=amount,
                    post_only=True,
                    reduce_only=True
                )
                
                if new_order_id:
                    state.active_limit_order_id = new_order_id
                    state.active_limit_order_price = grvt_best_bid
                    logger.info(f"Replaced order: {new_order_id} at {grvt_best_bid}")
                else:
                    state.active_limit_order_id = None
                    state.active_limit_order_price = None
                return

        else:
            # Gapが閾値を超えたらBest Askに指値注文
            if gap > config.CLOSE_THRESHOLD:
                logger.info(f"Close gap {gap:.5f} > {config.CLOSE_THRESHOLD}. Placing Maker Limit Order at {grvt_best_bid}")
                
                amount = config.DEFAULT_ORDER_AMOUNT
                order_id = await grvt_orders.grvt_create_limit_order(
                    api,
                    side="buy",
                    price=grvt_best_bid,
                    qty=amount,
                    post_only=True,
                    reduce_only=True
                )
                
                if order_id:
                    state.active_limit_order_id = order_id
                    state.active_limit_order_price = grvt_best_bid
                    logger.info(f"Exit order placed: {order_id}")
                else:
                    logger.error("Failed to place exit limit order")
