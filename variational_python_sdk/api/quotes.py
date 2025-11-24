"""Quote-related API methods."""
from typing import Union
import aiohttp

from ..models import Instrument, IndicativeQuote
from ..config import QUOTES_ENDPOINT, DEFAULT_TIMEOUT
from ..exceptions import (
    VariationalAPIError,
    VariationalAuthenticationError,
    VariationalRateLimitError,
)


class QuotesAPI:
    """API methods for fetching quotes."""
    
    def __init__(self, session: aiohttp.ClientSession, timeout: float = DEFAULT_TIMEOUT, proxy: str = None):
        """
        Initialize QuotesAPI.
        
        Args:
            session: aiohttp ClientSession to use for requests
            timeout: Request timeout in seconds
            proxy: Proxy URL
        """
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.proxy = proxy
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict:
        """Handle API response and raise appropriate exceptions."""
        if response.status == 401 or response.status == 403:
            text = await response.text()
            raise VariationalAuthenticationError(
                response.status,
                response.reason or "Authentication failed",
                text,
            )
        elif response.status == 429:
            text = await response.text()
            raise VariationalRateLimitError(
                response.status,
                response.reason or "Rate limit exceeded",
                text,
            )
        elif not response.ok:
            text = await response.text()
            raise VariationalAPIError(
                response.status,
                response.reason or "API error",
                text,
            )
        return await response.json()
    
    async def get_indicative_quote(
        self,
        instrument: Union[Instrument, dict],
        qty: Union[str, float],
    ) -> IndicativeQuote:
        """
        Get an indicative quote for an instrument.
        
        Args:
            instrument: Instrument configuration (Instrument instance or dict)
            qty: Quantity to quote
            
        Returns:
            IndicativeQuote object with bid, ask, and metadata
            
        Raises:
            VariationalAPIError: If the API request fails
            VariationalAuthenticationError: If authentication fails
            VariationalRateLimitError: If rate limit is exceeded
        """
        if isinstance(instrument, dict):
            payload = {"instrument": instrument, "qty": str(qty)}
        else:
            payload = {"instrument": instrument.to_dict(), "qty": str(qty)}
        
        if self.session is None or self.session.closed:
            raise RuntimeError("Session is closed. Use client as async context manager.")
        
        async with self.session.post(
            QUOTES_ENDPOINT,
            json=payload,
            timeout=self.timeout,
            proxy=self.proxy,
        ) as response:
            data = await self._handle_response(response)
            return IndicativeQuote.from_dict(data)

