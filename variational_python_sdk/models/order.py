"""Order data models."""
from dataclasses import dataclass
from typing import Literal, Optional, Any, Dict


@dataclass
class MarketOrderRequest:
    """Represents a market order request."""
    quote_id: str
    side: Literal["buy", "sell"]
    is_reduce_only: bool = False
    max_slippage: float = 0.005

    def to_dict(self) -> dict:
        """Convert to API request format."""
        return {
            "quote_id": self.quote_id,
            "side": self.side,
            "is_reduce_only": self.is_reduce_only,
            "max_slippage": self.max_slippage,
        }


@dataclass
class OrderResponse:
    """Represents an order execution response."""
    # Structure TBD based on actual API response
    # For now, store as dict to be flexible
    data: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict) -> "OrderResponse":
        """Create from API response."""
        return cls(data=data)

