"""Event handlers for order fills."""
from pysdk.grvt_ccxt_logging_selector import logger
from .. import state
from ..variational import orders as variational_orders
import asyncio

async def _fetch_position_with_delay(client, delay: float = 2.0):
    """Helper to fetch position after a delay."""
    await asyncio.sleep(delay)
    try:
        positions = await client.positions.get_all_positions()
        # Be careful here: if positions is empty or structure changes, this might raise index error
        if positions and len(positions) > 0:
            avg_entry_price = float(positions[0]['position_info']['avg_entry_price'])
            state.variational_entry_price = avg_entry_price
            logger.info(f"Variational average entry price (delayed fetch): {avg_entry_price}")
        else:
            logger.warning("Variational positions empty after delay.")
    except Exception as e:
        logger.error(f"Error fetching delayed position info: {e}")

async def handle_entry_fill(fill_qty: float):
    """
    Handle entry fill on GRVT (Maker side).
    Execute taker order on Variational immediately.
    """
    logger.info(f"Handling entry fill: Buying {fill_qty} at Variational")
    
    # Variationalで成行買い
    success = await variational_orders.variational_buy(state.variational_client, qty=str(fill_qty))
    
    if success:
        logger.info("Successfully bought at Variational after GRVT fill")
        # ポジション状態を更新（部分約定などを考慮する場合はロジック調整が必要）
        positions = await state.variational_client.positions.get_all_positions()

        asyncio.create_task(_fetch_position_with_delay(state.variational_client, delay=3.0))

        state.existing_position = True
        # アクティブな注文IDをクリア
        state.active_limit_order_id = None
        state.active_limit_order_price = None
    else:
        logger.error("Failed to buy at Variational after GRVT fill! Unbalanced position.")
        # エラー処理: ここでリトライや緊急決済のロジックが必要かもしれません

async def handle_exit_fill(fill_qty: float):
    """
    Handle entry fill on GRVT (Maker side).
    Execute taker order on Variational immediately.
    """
    logger.info(f"Handling entry fill: Buying {fill_qty} at Variational")
    
    # Variationalで成行買い
    success = await variational_orders.variational_sell(state.variational_client, qty=str(fill_qty))
    
    if success:
        logger.info("Successfully bought at Variational after GRVT fill")
        # ポジション状態を更新（部分約定などを考慮する場合はロジック調整が必要）
        state.existing_position = True
        # アクティブな注文IDをクリア
        state.active_limit_order_id = None
        state.active_limit_order_price = None
    else:
        logger.error("Failed to buy at Variational after GRVT fill! Unbalanced position.")
        # エラー処理: ここでリトライや緊急決済のロジックが必要かもしれません

# async def handle_short_fill():
#     """Handle short order fill: buy at Variational."""
#     logger.info(f"Handling short fill: buying {state.short_filled_quantity} at Variational")
    
#     if state.short_filled_quantity > 0:
#         qty_str = str(state.short_filled_quantity)
#         success = await variational_orders.variational_buy(state.variational_client, qty_str)
#         if success:
#             logger.info("Successfully bought at Variational after short fill")
#         else:
#             logger.error("Failed to buy at Variational after short fill")


# async def handle_cover_fill():
#     """Handle cover order fill: sell at Variational."""
#     logger.info(f"Handling cover fill: selling {state.cover_filled_quantity} at Variational")
    
#     if state.cover_filled_quantity > 0:
#         qty_str = str(state.cover_filled_quantity)
#         success = await variational_orders.variational_sell(state.variational_client, qty_str)
#         if success:
#             logger.info("Successfully sold at Variational after cover fill")
#         else:
#             logger.error("Failed to sell at Variational after cover fill")


