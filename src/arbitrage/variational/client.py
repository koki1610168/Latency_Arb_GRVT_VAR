"""Variational client setup and quote management."""
import asyncio
import os

from pysdk.grvt_ccxt_logging_selector import logger
from variational_python_sdk.client import AsyncVariationalClient
from variational_python_sdk.models import Instrument
from .. import state
from .. import utils
from .. import config
from ..trading import loops as trading_loops


async def setup_variational_client():
    """Set up Variational client."""
    cookie = os.environ.get("VARIATIONAL_COOKIE")
    #proxy = os.environ.get("VARIATIONAL_PROXY")
    if not cookie:
        logger.error("VARIATIONAL_COOKIE environment variable not set")
        return None
    client = AsyncVariationalClient(cookie=cookie, proxy=None)
    await client.__aenter__()
    logger.info("Variational client initialized")
    state.variational_client = client
    return client


async def get_variational_quote(client: AsyncVariationalClient, qty: str = str(config.DEFAULT_ORDER_AMOUNT)):
    """Get indicative quote from Variational."""
    try:
        instrument = Instrument(
            underlying="BTC",
            funding_interval_s=3600,
            settlement_asset="USDC",
            instrument_type="perpetual_future",
        )
        quote = await client.quotes.get_indicative_quote(instrument, qty=qty)
        return quote
    except Exception as e:
        logger.error(f"Error getting Variational quote: {e}")
        return None


async def variational_quote_loop():
    """Continuously fetch Variational quotes."""
    logger.info("Starting Variational quote loop...")
    
    while state.running:
        try:
            quote = await get_variational_quote(state.variational_client, qty=str(config.DEFAULT_ORDER_AMOUNT))
            
            if quote:
                state.variational_quote = quote
                state.variational_bid = quote.bid
                state.variational_ask = quote.ask
                
                logger.info(
                    f"Variational quote - Bid: {state.variational_bid}, Ask: {state.variational_ask}"
                )
                
                # Trigger execution logic immediately after update
                if state.grvt_api:
                    if not state.existing_position:
                        asyncio.create_task(trading_loops.try_entry(state.grvt_api))
                    else:
                        asyncio.create_task(trading_loops.try_exit(state.grvt_api))
                
            else:
                logger.warning("Failed to get Variational quote")
            
            await asyncio.sleep(config.QUOTE_FETCH_INTERVAL)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in Variational quote loop: {e}")
            await asyncio.sleep(config.QUOTE_FETCH_INTERVAL)
