"""Quote data models."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class IndicativeQuote:
    """Represents an indicative quote response from Variational."""
    bid: float
    ask: float
    quote_id: str
    mark_price: Optional[float] = None
    index_price: Optional[float] = None

    @classmethod
    def from_dict(cls, data: dict) -> "IndicativeQuote":
        """Create from API response."""
        return cls(
            bid=float(data["bid"]),
            ask=float(data["ask"]),
            quote_id=data["quote_id"],
            mark_price=float(data["mark_price"]) if data.get("mark_price") else None,
            index_price=float(data["index_price"]) if data.get("index_price") else None,
        )

    @property
    def mid(self) -> float:
        """Calculate mid price."""
        return (self.bid + self.ask) / 2.0

    @property
    def spread(self) -> float:
        """Calculate spread (ask - bid)."""
        return self.ask - self.bid

