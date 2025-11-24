"""Variational order management functions."""
import traceback

from pysdk.grvt_ccxt_logging_selector import logger
from variational_python_sdk.client import AsyncVariationalClient
from variational_python_sdk.models import MarketOrderRequest
from .. import state
from . import client
from .. import config


async def variational_buy(variational_client: AsyncVariationalClient, qty: str) -> bool:
    """Buy at Variational using market order."""
    try:
        # Get fresh quote
        # quote = await client.get_variational_quote(variational_client, qty=qty)
        # if not quote:
        #     logger.error("Failed to get Variational quote for buy")
        #     return False
        
        # Place market buy order
        order = MarketOrderRequest(
            quote_id=state.variational_quote.quote_id,
            side="buy",
            is_reduce_only=False,
            max_slippage=config.VARIATIONAL_MAX_SLIPPAGE,
        )
        
        result = await variational_client.orders.place_market_order(order)
        logger.info(f"Variational buy order placed: {result.data}")
        
        # Update position (simplified - in reality, check actual filled quantity)
        try:
            qty_float = float(qty)
            state.variational_position += qty_float
            logger.info(f"Variational position updated: {state.variational_position}")
        except ValueError:
            pass
        
        return True
    except Exception as e:
        logger.error(f"Error placing Variational buy order: {e} {traceback.format_exc()}")
        return False


async def variational_sell(variational_client: AsyncVariationalClient, qty: str) -> bool:
    """Sell at Variational using market order."""
    try:
        # # Get fresh quote
        # quote = await client.get_variational_quote(variational_client, qty=qty)
        # if not quote:
        #     logger.error("Failed to get Variational quote for sell")
        #     return False
        
        # Place market sell order
        order = MarketOrderRequest(
            quote_id=state.variational_quote.quote_id,
            side="sell",
            is_reduce_only=False,
            max_slippage=config.VARIATIONAL_MAX_SLIPPAGE,
        )
        
        result = await variational_client.orders.place_market_order(order)
        logger.info(f"Variational sell order placed: {result.data}")
        
        # Update position (simplified - in reality, check actual filled quantity)
        try:
            qty_float = float(qty)
            state.variational_position -= qty_float
            logger.info(f"Variational position updated: {state.variational_position}")
        except ValueError:
            pass
        
        return True
    except Exception as e:
        logger.error(f"Error placing Variational sell order: {e} {traceback.format_exc()}")
        return False


