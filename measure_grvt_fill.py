import asyncio
import os
import sys
import traceback
import time
import datetime
import json
from pysdk.grvt_ccxt_env import GrvtEnv, GrvtWSEndpointType
from pysdk.grvt_ccxt_logging_selector import logger
from pysdk.grvt_ccxt_utils import rand_uint32
from pysdk.grvt_ccxt_ws import GrvtCcxtWS

# Global state to track order times
order_times = {}
# Event to signal fill received
fill_received_event = asyncio.Event()

def find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for k, v in obj.items():
            res = find_key(v, key)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_key(item, key)
            if res:
                return res
    return None

async def fill_callback(message: dict) -> None:
    """Callback for fill messages."""
    recv_perf_counter = time.perf_counter()
    recv_timestamp = datetime.datetime.now()
    
    # logger.info(f"Received fill message: {message}")
    
    client_order_id = find_key(message, "client_order_id")
    
    if client_order_id:
        client_order_id = str(client_order_id)
        if client_order_id in order_times:
            send_info = order_times.pop(client_order_id)
            send_perf_counter = send_info['perf_counter']
            send_timestamp = send_info['timestamp']
            
            latency = (recv_perf_counter - send_perf_counter) * 1000 # ms
            
            log_msg = (
                f"Fill received for order {client_order_id}.\n"
                f"Order Submitted: {send_timestamp}\n"
                f"Fill Received:   {recv_timestamp}\n"
                f"Latency:         {latency:.4f} ms"
            )
            logger.info(log_msg)
            print(log_msg)
            fill_received_event.set()
        else:
            # logger.debug(f"Received fill for unknown order: {client_order_id}")
            pass
    else:
        # Sometimes fill messages might not have client_order_id at top level or depending on structure
        # But for this test we rely on it being there as per previous exploration
        pass

async def main():
    # Setup API
    params = {
        "api_key": os.getenv("GRVT_API_KEY"),
        "trading_account_id": os.getenv("GRVT_TRADING_ACCOUNT_ID"),
        "api_ws_version": os.getenv("GRVT_WS_STREAM_VERSION", "v1"),
    }
    if os.getenv("GRVT_PRIVATE_KEY"):
        params["private_key"] = os.getenv("GRVT_PRIVATE_KEY")
    
    env_str = os.getenv("GRVT_ENV", "testnet")
    try:
        env = GrvtEnv(env_str)
    except ValueError:
        env = GrvtEnv.TESTNET
    
    loop = asyncio.get_running_loop()
    api = GrvtCcxtWS(env, loop, logger, parameters=params)
    await api.initialize()
    
    instrument = "BTC_USDT_Perp"
    
    print(f"Subscribing to fills for {instrument}...")
    await api.subscribe(
        stream="fill",
        callback=fill_callback,
        ws_end_point_type=GrvtWSEndpointType.TRADE_DATA_RPC_FULL,
        params={"instrument": instrument}
    )
    
    print("Waiting 5 seconds for connection stability...")
    await asyncio.sleep(5)
    
    # Send Market Order
    try:
        client_order_id = str(rand_uint32())
        
        print(f"Sending Market Buy Order {client_order_id}...")
        
        # Capture time right before sending
        send_perf_counter = time.perf_counter()
        send_timestamp = datetime.datetime.now()
        
        order_times[client_order_id] = {
            'perf_counter': send_perf_counter,
            'timestamp': send_timestamp
        }
        
        print(f"Order Submitted at: {send_timestamp}")
        
        # Send order (Market Buy)
        await api.rpc_create_order(
            symbol=instrument,
            order_type="limit",
            side="buy",
            amount=0.001, # Minimum amount
            price=87560,
            params={
                "client_order_id": client_order_id,
                "time_in_force": "GOOD_TILL_TIME",
                "post_only": True,
            },
        )
        
        print("Order sent. Waiting for fill...")
        
        # Wait for fill with timeout
        try:
            await asyncio.wait_for(fill_received_event.wait(), timeout=20.0)
        except asyncio.TimeoutError:
            print(f"Timeout waiting for fill for order {client_order_id}")
            
    except Exception as e:
        logger.error(f"Error sending order: {e}")
        traceback.print_exc()
        
    finally:
        print("Closing connection...")
        try:
            await api._close_connection(GrvtWSEndpointType.TRADE_DATA_RPC_FULL)
        except:
            pass
        # Give some time for async cleanup
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
