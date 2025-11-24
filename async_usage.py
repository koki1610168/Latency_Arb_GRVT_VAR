"""Example usage of Variational Python SDK (async)."""
import asyncio
import os
import sys
from pathlib import Path

from variational_python_sdk.client import AsyncVariationalClient
from variational_python_sdk.models import Instrument, MarketOrderRequest
from variational_python_sdk.exceptions import VariationalAuthenticationError, VariationalAPIError
from dotenv import load_dotenv

load_dotenv()

async def example_get_quote():
    """Example: Get an indicative quote."""
    cookie = os.environ.get("VARIATIONAL_COOKIE")
    proxy = None
    if not cookie:
        print("Please set VARIATIONAL_COOKIE environment variable")
        return
    
    async with AsyncVariationalClient(cookie=cookie, proxy=proxy) as client:
        # Create instrument
        instrument = Instrument(
            underlying="BTC",
            funding_interval_s=3600,
            settlement_asset="USDC",
            instrument_type="perpetual_future",
        )
        
        try:
            # Get indicative quote
            quote = await client.quotes.get_indicative_quote(instrument, qty="1.0")
            print(f"Quote ID: {quote.quote_id}")
            print(f"Bid: {quote.bid}, Ask: {quote.ask}")
            print(f"Mid: {quote.mid}, Spread: {quote.spread}")
            if quote.mark_price:
                print(f"Mark Price: {quote.mark_price}")
            if quote.index_price:
                print(f"Index Price: {quote.index_price}")
            
            return quote
        except VariationalAuthenticationError as e:
            print(f"Authentication failed: {e}")
        except VariationalAPIError as e:
            print(f"API error: {e}")


async def example_place_order():
    """Example: Get quote and place market order."""
    cookie = os.environ.get("VARIATIONAL_COOKIE")
    if not cookie:
        print("Please set VARIATIONAL_COOKIE environment variable")
        return
    
    async with AsyncVariationalClient(cookie=cookie) as client:
        instrument = Instrument(underlying="SOL")
        
        try:
            # Get quote first
            quote = await client.quotes.get_indicative_quote(instrument, qty="1.0")
            print(f"Got quote: bid={quote.bid}, ask={quote.ask}")
            
            # Place market order (commented out to avoid accidental trades)
            # Uncomment to actually place an order
            order_request = MarketOrderRequest(
                quote_id=quote.quote_id,
                side="buy",
                is_reduce_only=False,
                max_slippage=0.005,
            )
            order_response = await client.orders.place_market_order(order_request)
            print(f"Order placed: {order_response.data}")
            
        except VariationalAuthenticationError as e:
            print(f"Authentication failed: {e}")
        except VariationalAPIError as e:
            print(f"API error: {e}")


async def example_using_dict():
    """Example: Using dict instead of model classes."""
    cookie = os.environ.get("VARIATIONAL_COOKIE")
    if not cookie:
        print("Please set VARIATIONAL_COOKIE environment variable")
        return
    
    async with AsyncVariationalClient(cookie=cookie) as client:
        try:
            # Use dict for instrument
            quote = await client.quotes.get_indicative_quote(
                instrument={
                    "underlying": "SOL",
                    "funding_interval_s": 3600,
                    "settlement_asset": "USDC",
                    "instrument_type": "perpetual_future",
                },
                qty="1.0",
            )
            print(f"Quote using dict: {quote}")
            
        except Exception as e:
            print(f"Error: {e}")

async def example_get_positions():
    """Example: Fetch all open positions."""
    cookie = os.environ.get("VARIATIONAL_COOKIE")
    if not cookie:
        print("Please set VARIATIONAL_COOKIE environment variable")
        return
    
    async with AsyncVariationalClient(cookie=cookie) as client:
        try:
            print("Fetching positions...")
            positions = await client.positions.get_all_positions()
            
            # Assuming the API returns a list or a dict containing a list
            if isinstance(positions, list):
                print(f"Found {len(positions)} positions.")
                for pos in positions:
                    print(pos)
            elif isinstance(positions, dict):
                print(f"Positions response: {positions}")
            else:
                print(f"Unexpected response type: {type(positions)}")
                print(positions)
                
        except VariationalAuthenticationError as e:
            print(f"Authentication failed: {e}")
        except VariationalAPIError as e:
            print(f"API error: {e}")
        except Exception as e:
            print(f"Error fetching positions: {e}")


async def main():
    """Run all examples."""
    # print("=== Example 1: Get Quote ===")
    # await example_get_quote()
    
    #print("\n=== Example 2: Place Order ===")
    #await example_place_order()
    
    #print("\n=== Example 3: Using Dict ===")
    #await example_using_dict()

    print("\n=== Example 4: Get Positions ===")
    await example_get_positions()


if __name__ == "__main__":
    asyncio.run(main())

