"""GRVT WebSocket setup and subscription management."""
import asyncio
import os
import traceback

from pysdk.grvt_ccxt_env import GrvtEnv, GrvtWSEndpointType
from pysdk.grvt_ccxt_logging_selector import logger
from pysdk.grvt_ccxt_ws import GrvtCcxtWS
from . import callbacks


async def grvt_ws_subscribe(api: GrvtCcxtWS, args_list: dict) -> None:
    """Subscribe to GRVT websocket channels."""
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
    """Set up GRVT WebSocket connection."""
    from .. import state
    
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
    state.grvt_api = api
    
    pub_args_dict = {
        "mini.s": (
            callbacks.grvt_mini_ticker_callback,
            None,
            {"instrument": "BTC_USDT_Perp"},
        ),
    }
    
    prv_args_dict = {
        # "order": (
        #     callbacks.grvt_order_callback,
        #     GrvtWSEndpointType.TRADE_DATA_RPC_FULL,
        #     {"instrument": "BTC_USDT_Perp"},
        # ),
        # "fill": (
        #     callbacks.grvt_fill_callback,
        #     GrvtWSEndpointType.TRADE_DATA_RPC_FULL,
        #     {"instrument": "BTC_USDT_Perp"},
        # ),
        # "state": (
        #     callbacks.grvt_state_callback,
        #     GrvtWSEndpointType.TRADE_DATA_RPC_FULL,
        #     {"instrument": "BTC_USDT_Perp"},
        # ),
    }
    
    try:
        if "private_key" in params:
            await grvt_ws_subscribe(api, {**pub_args_dict, **prv_args_dict})
        else:
            await grvt_ws_subscribe(api, pub_args_dict)
    except Exception as e:
        logger.error(f"Error in grvt_ws_subscribe: {e} {traceback.format_exc()}")
    return api


