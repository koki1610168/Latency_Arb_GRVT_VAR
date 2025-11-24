"""Instrument data model."""
from dataclasses import dataclass
from typing import Literal


@dataclass
class Instrument:
    """Represents a trading instrument configuration."""
    underlying: str
    funding_interval_s: int = 3600
    settlement_asset: str = "USDC"
    instrument_type: Literal["perpetual_future"] = "perpetual_future"

    def to_dict(self) -> dict:
        """Convert to API request format."""
        return {
            "underlying": self.underlying,
            "funding_interval_s": self.funding_interval_s,
            "settlement_asset": self.settlement_asset,
            "instrument_type": self.instrument_type,
        }

