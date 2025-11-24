"""Main async client for Variational API."""
from typing import Optional
import aiohttp

from .api import QuotesAPI, OrdersAPI
from .config import DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, RetryConfig
from .utils.retry import retry_with_backoff


class AsyncVariationalClient:
    """Async client for Variational Omni API."""
    
    def __init__(
        self,
        cookie: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        retry_config: Optional[RetryConfig] = None,
        proxy: Optional[str] = None,
    ):
        """
        Initialize async Variational client.
        
        Args:
            cookie: Authentication cookie (vr-token)
            base_url: Base URL for API (defaults to production)
            timeout: Request timeout in seconds
            retry_config: Retry configuration (uses defaults if None)
            proxy: Proxy URL (e.g. http://user:pass@host:port)
        """
        self.cookie = cookie
        self.base_url = base_url
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.proxy = proxy
        self._session: Optional[aiohttp.ClientSession] = None
        self._quotes: Optional[QuotesAPI] = None
        self._orders: Optional[OrdersAPI] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            cookies = {}
            if self.cookie:
                cookies["vr-token"] = self.cookie
            
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            self._session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": DEFAULT_USER_AGENT,
                },
                cookies=cookies,
                connector=connector,
            )
        return self._session
    
    async def _ensure_session(self):
        """Ensure session is initialized."""
        if self._session is None or self._session.closed:
            await self._get_session()
    
    @property
    def quotes(self) -> QuotesAPI:
        """Access quote-related API methods."""
        if self._quotes is None:
            if self._session is None or self._session.closed:
                raise RuntimeError(
                    "Session not initialized. Use client as async context manager: "
                    "async with AsyncVariationalClient(...) as client:"
                )
            self._quotes = QuotesAPI(self._session, self.timeout, self.proxy)
        return self._quotes
    
    @property
    def orders(self) -> OrdersAPI:
        """Access order-related API methods."""
        if self._orders is None:
            if self._session is None or self._session.closed:
                raise RuntimeError(
                    "Session not initialized. Use client as async context manager: "
                    "async with AsyncVariationalClient(...) as client:"
                )
            self._orders = OrdersAPI(self._session, self.timeout, self.proxy)
        return self._orders
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            self._quotes = None
            self._orders = None

