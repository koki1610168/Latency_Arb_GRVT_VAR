"""Position-related API methods."""
from typing import Dict, Any, List, Union
import aiohttp

from ..config import POSITIONS_ENDPOINT, DEFAULT_TIMEOUT
from ..exceptions import (
    VariationalAPIError,
    VariationalAuthenticationError,
    VariationalRateLimitError,
)


class PositionsAPI:
    """API methods for fetching positions."""
    
    def __init__(self, session: aiohttp.ClientSession, timeout: float = DEFAULT_TIMEOUT, proxy: str = None):
        """
        Initialize PositionsAPI.
        
        Args:
            session: aiohttp ClientSession to use for requests
            timeout: Request timeout in seconds
            proxy: Proxy URL
        """
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.proxy = proxy
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Union[dict, list]:
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
    
    async def get_all_positions(self) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Fetch all open positions.
        
        Returns:
            List of position dictionaries or a dictionary containing them.
            
        Raises:
            VariationalAPIError: If the API request fails
            VariationalAuthenticationError: If authentication fails
            VariationalRateLimitError: If rate limit is exceeded
        """
        if self.session is None or self.session.closed:
            raise RuntimeError("Session is closed. Use client as async context manager.")
        
        async with self.session.get(
            POSITIONS_ENDPOINT,
            timeout=self.timeout,
            proxy=self.proxy,
        ) as response:
            return await self._handle_response(response)