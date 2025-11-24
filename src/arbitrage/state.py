"""Global state management for arbitrage trading."""
import asyncio

# Price tracking
grvt_bid = None
grvt_ask = None
variational_bid = None
variational_ask = None
variational_quote = None  # Latest Variational quote with quote_id

# Order tracking
########################################################
current_short_order_id = None  # GRVT short (sell) order
current_cover_order_id = None  # GRVT cover (buy) order
active_limit_order_id = None     # 現在アクティブな指値注文ID
active_limit_order_price = None  # 現在アクティブな指値注文の価格
short_order_filled = False
########################################################

# Position tracking
grvt_position = 0.0  # Positive = long, Negative = short
variational_position = 0.0  # Positive = long, Negative = short

# Events
ask_changed_event = asyncio.Event()
bid_changed_event = asyncio.Event()
spread_changed_event = asyncio.Event()
short_fill_event = asyncio.Event()
cover_fill_event = asyncio.Event()

# API instances
grvt_api = None
variational_client = None

running = True


grvt_order_id = None
existing_position = False