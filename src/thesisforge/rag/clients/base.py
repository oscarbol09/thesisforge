"""Base asynchronous academic HTTP client with SSRF protection, retries, and rate-limiting."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from thesisforge import __version__
from thesisforge.core.logging import get_logger
from thesisforge.core.security import assert_safe_academic_url_async
from thesisforge.exceptions import AcademicAPIError, SSRFBlockedError

logger = get_logger(__name__)

DEFAULT_ACADEMIC_USER_AGENT = (
    f"ThesisForge/{__version__} "
    "(https://github.com/oscarbol09/thesisforge; mailto:thesisforge@academic.org)"
)


def _is_retryable_http_error(exc: BaseException) -> bool:
    """Check if exception is a transient network or 5xx/429 server error."""
    if isinstance(exc, (httpx.TransportError, httpx.TimeoutException)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        # Retry Rate Limits (429) and Server Errors (500, 502, 503, 504)
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return False


class BaseAcademicClient(ABC):
    """Abstract base client for querying academic publication APIs."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 15.0,
        max_retries: int = 3,
        user_agent: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.user_agent = user_agent or DEFAULT_ACADEMIC_USER_AGENT
        self._client: httpx.AsyncClient | None = None

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Provide an active httpx.AsyncClient session."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={"User-Agent": self.user_agent, "Accept": "application/json"},
                follow_redirects=True,
            )
        try:
            yield self._client
        finally:
            pass

    async def close(self) -> None:
        """Close client connection pool."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def request_json(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Perform a secure, retried HTTP request and parse JSON response."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if endpoint else self.base_url
        await assert_safe_academic_url_async(url)

        req_headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        if headers:
            req_headers.update(headers)

        retrier = AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential_jitter(initial=1.0, max=10.0),
            retry=retry_if_exception(_is_retryable_http_error),
            reraise=True,
        )

        async with self.get_client() as client:
            try:
                async for attempt in retrier:
                    with attempt:
                        response = await client.request(
                            method=method,
                            url=url,
                            params=params,
                            headers=req_headers,
                        )
                        response.raise_for_status()
                        return response.json()  # type: ignore[no-any-return]
            except SSRFBlockedError:
                raise
            except httpx.HTTPStatusError as err:
                status = err.response.status_code
                logger.warning(
                    f"Academic API returned HTTP {status}",
                    extra={"url": url, "status": status},
                )
                raise AcademicAPIError(
                    f"Error de API académica ({self.__class__.__name__}): HTTP {status}",
                    details={
                        "url": url,
                        "status": str(status),
                        "response": err.response.text[:200],
                    },
                ) from err
            except Exception as err:
                logger.warning(
                    f"Academic API request failed: {err}",
                    extra={"url": url, "error": str(err)},
                )
                raise AcademicAPIError(
                    f"Fallo en comunicación con API académica ({self.__class__.__name__}): {err}",
                    details={"url": url, "error": str(err)},
                ) from err
        raise AcademicAPIError(f"No se pudo completar la petición a {url}")

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        **kwargs: Any,
    ) -> Any:
        """Search academic catalog for papers matching query."""
