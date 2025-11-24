"""GRVT order management functions."""
import traceback

from pysdk.grvt_ccxt_logging_selector import logger
from pysdk.grvt_ccxt_utils import rand_uint32
from pysdk.grvt_ccxt_ws import GrvtCcxtWS, GrvtOrderSide
from .. import state
from .. import config

async def grvt_create_mkt_order(
    api: GrvtCcxtWS, side: GrvtOrderSide, qty: float, client_order_id: str = "", reduce_only: bool = False
) -> str:
    FN = "rpc_create_mkt_order"
    if not api or not api._private_key:
        logger.error("API not initialized or no private key")
        return ""
    # Send order
    if not client_order_id:
        client_order_id = str(rand_uint32())
    payload = await api.rpc_create_order(
        symbol="BTC_USDT_Perp",
        order_type="market",
        side=side,
        amount=qty,
        params={
            "client_order_id": client_order_id,
            "time_in_force": "IMMEDIATE_OR_CANCEL",
            "reduce_only": reduce_only,
        },
    )
    logger.info(f"{FN}: {payload=}")
    return client_order_id

# async def grvt_cancel_order(api: GrvtCcxtWS, client_order_id: str) -> None:
#     """Cancel an order at GRVT."""
#     if not api or not api._private_key:
#         return
    
#     logger.info(f"Cancelling GRVT order with client_order_id={client_order_id}")
    
#     try:
#         payload = await api.rpc_cancel_order(params={"client_order_id": client_order_id})
#         logger.info(f"grvt_cancel_order: {payload=}")
#     except Exception as e:
#         logger.error(f"Error cancelling order: {e} {traceback.format_exc()}")
    

# async def grvt_create_short_order(api: GrvtCcxtWS, price: str) -> str:
#     """Create a short (sell) order at GRVT."""
#     if not api or not api._private_key:
#         logger.error("API not initialized or no private key")
#         return ""
    
#     client_order_id = str(rand_uint32())
#     state.current_short_order_id = client_order_id
#     state.short_order_price = price
    
#     logger.info(f"Creating short (sell) order at GRVT price {price} with client_order_id={client_order_id}")
    
#     try:
#         payload = await api.rpc_create_order(
#             symbol="BTC_USDT_Perp",
#             order_type="limit",
#             side="sell",
#             amount=config.DEFAULT_ORDER_AMOUNT,
#             price=price,
#             params={
#                 "client_order_id": client_order_id,
#                 "time_in_force": "GOOD_TILL_TIME",
#             },
#         )
#         logger.info(f"grvt_create_short_order: {payload=}")
#         return client_order_id
#     except Exception as e:
#         logger.error(f"Error creating short order: {e} {traceback.format_exc()}")
#         state.current_short_order_id = None
#         state.short_order_price = None
#         return ""


# async def grvt_create_cover_order(api: GrvtCcxtWS, price: str) -> str:
#     """Create a cover (buy) order at GRVT."""
#     if not api or not api._private_key:
#         logger.error("API not initialized or no private key")
#         return ""
    
#     # Use the short filled quantity to cover
#     amount = abs(state.short_filled_quantity) if state.short_filled_quantity > 0 else config.DEFAULT_ORDER_AMOUNT
    
#     client_order_id = str(rand_uint32())
#     state.current_cover_order_id = client_order_id
#     state.cover_order_price = price
    
#     logger.info(f"Creating cover (buy) order at GRVT price {price} for amount {amount} with client_order_id={client_order_id}")
    
#     try:
#         payload = await api.rpc_create_order(
#             symbol="BTC_USDT_Perp",
#             order_type="limit",
#             side="buy",
#             amount=amount,
#             price=price,
#             params={
#                 "client_order_id": client_order_id,
#                 "time_in_force": "GOOD_TILL_TIME",
#             },
#         )
#         logger.info(f"grvt_create_cover_order: {payload=}")
#         return client_order_id
#     except Exception as e:
#         logger.error(f"Error creating cover order: {e} {traceback.format_exc()}")
#         state.current_cover_order_id = None
#         state.cover_order_price = None
#         return ""





