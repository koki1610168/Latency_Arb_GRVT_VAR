"""Utility functions for arbitrage trading."""
import logging
import json
import os
from urllib import request, error

class SlackHandler(logging.Handler):
    """Logging handler that sends messages to Slack asynchronously (via QueueListener)."""
    
    def __init__(self, webhook_url, level=logging.NOTSET):
        super().__init__(level)
        self.webhook_url = webhook_url

    def emit(self, record):
        try:
            msg = self.format(record)
            # Simple coloring based on level
            color = "#36a64f" # Green (INFO)
            if record.levelno >= logging.ERROR:
                color = "#ff0000" # Red
            elif record.levelno >= logging.WARNING:
                color = "#ffcc00" # Yellow

            payload = {
                "attachments": [
                    {
                        "color": color,
                        "text": f"*{record.levelname}*: {msg}",
                        "mrkdwn_in": ["text"]
                    }
                ]
            }
            
            req = request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            request.urlopen(req)
            
        except Exception:
            self.handleError(record)

def normalize_price(price):
    """Normalize price to float."""
    if price is None:
        return None
    if isinstance(price, (int, float)):
        return float(price)
    if isinstance(price, str):
        try:
            return float(price)
        except ValueError:
            return None
    return None

def calculate_open_gap():
    from . import state

    if state.variational_bid is None or state.grvt_bid is None:
        return None
    try:
        var_ask = float(state.variational_ask) if not isinstance(state.variational_ask, float) else state.variational_ask
        grvt_bid = float(state.grvt_bid) if not isinstance(state.grvt_bid, float) else state.grvt_bid
        
        return (grvt_bid - var_ask) / ((grvt_bid + var_ask) / 2)
    except (ValueError, TypeError):
        return None


def calculate_close_gap():
    from . import state

    if state.variational_bid is None or state.grvt_bid is None:
        return None
    try:
        var_bid = float(state.variational_bid) if not isinstance(state.variational_bid, float) else state.variational_bid
        grvt_ask = float(state.grvt_ask) if not isinstance(state.grvt_ask, float) else state.grvt_ask
        
        return (var_bid - grvt_ask) / ((var_bid + grvt_ask) / 2)
    except (ValueError, TypeError):
        return None


# def calculate_spread():
#     """Calculate bid spread: Variational bid - GRVT bid."""
#     from . import state
    
#     if state.variational_bid is None or state.grvt_bid is None:
#         return None
#     try:
#         var_bid = float(state.variational_bid) if not isinstance(state.variational_bid, float) else state.variational_bid
#         grvt_bid_val = float(state.grvt_bid) if not isinstance(state.grvt_bid, float) else state.grvt_bid
#         return grvt_bid_val - var_bid
#     except (ValueError, TypeError):
#         return None


