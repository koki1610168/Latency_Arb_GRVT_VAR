"""Event handlers for order fills."""
from pysdk.grvt_ccxt_logging_selector import logger
from .. import state
from ..variational import orders as variational_orders


async def handle_short_fill():
    """Handle short order fill: buy at Variational."""
    logger.info(f"Handling short fill: buying {state.short_filled_quantity} at Variational")
    
    if state.short_filled_quantity > 0:
        qty_str = str(state.short_filled_quantity)
        success = await variational_orders.variational_buy(state.variational_client, qty_str)
        if success:
            logger.info("Successfully bought at Variational after short fill")
        else:
            logger.error("Failed to buy at Variational after short fill")


async def handle_cover_fill():
    """Handle cover order fill: sell at Variational."""
    logger.info(f"Handling cover fill: selling {state.cover_filled_quantity} at Variational")
    
    if state.cover_filled_quantity > 0:
        qty_str = str(state.cover_filled_quantity)
        success = await variational_orders.variational_sell(state.variational_client, qty_str)
        if success:
            logger.info("Successfully sold at Variational after cover fill")
        else:
            logger.error("Failed to sell at Variational after cover fill")


