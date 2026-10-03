"""
SerpApi Client Service: Manages requests to SerpApi endpoints securely on the backend.
Normalizes response structures and handles errors robustly.
"""

import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.models.schemas import NormalizedSearchResponse
from app.serpapi.engines import (
    SearchEngineType,
    build_engine_params,
    normalize_serpapi_response
)

class SerpApiError(Exception):
    """Base exception class for SerpApi operations."""
    def __init__(self, message: str, status_code: Optional[int] = None, raw_response: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.raw_response = raw_response

class SerpApiMissingKeyError(SerpApiError):
    """Raised when SERPAPI_API_KEY is not configured in backend environment."""
    def __init__(self):
        super().__init__(
            message="SERPAPI_API_KEY is not configured in backend environment. Please set SERPAPI_API_KEY in .env file."
        )

class SerpApiAuthError(SerpApiError):
    """Raised when API key is invalid or unauthorized (HTTP 401/403 or error response)."""
    pass

class SerpApiRateLimitError(SerpApiError):
    """Raised when API rate limits are hit (HTTP 429)."""
    pass

class SerpApiNetworkError(SerpApiError):
    """Raised when network, connection, or timeout errors occur."""
    pass

class SerpApiClient:
    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0, http_client: Optional[httpx.AsyncClient] = None):
        if api_key is not None:
            raw_key = api_key
        else:
            raw_key = settings.SERPAPI_API_KEY

        if not raw_key or not isinstance(raw_key, str) or not raw_key.strip() or raw_key.strip() == "your_serpapi_key_here":
            raise SerpApiMissingKeyError()

        self.api_key = raw_key.strip()
        self.base_url = "https://serpapi.com/search"
        self.timeout = timeout
        self._shared_client = http_client

    @property
    def is_configured(self) -> bool:
        """Checks if a non-placeholder API key is set."""
        return bool(self.api_key and self.api_key.strip() and self.api_key != "your_serpapi_key_here")

    def _verify_configuration(self):
        if not self.is_configured:
            raise SerpApiMissingKeyError()

    async def execute_raw_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes raw HTTP request to SerpApi endpoint and handles HTTP/JSON errors.
        """
        self._verify_configuration()

        request_params = {
            **params,
            "api_key": self.api_key,
            "output": "json"
        }

        try:
            if self._shared_client and not self._shared_client.is_closed:
                response = await self._shared_client.get(self.base_url, params=request_params)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(self.base_url, params=request_params)

                # Check for HTTP errors
                if response.status_code == 401 or response.status_code == 403:
                    raise SerpApiAuthError(
                        message=f"SerpApi Authentication Failed (HTTP {response.status_code}). Check SERPAPI_API_KEY.",
                        status_code=response.status_code
                    )
                elif response.status_code == 429:
                    raise SerpApiRateLimitError(
                        message="SerpApi rate limit exceeded or search quota exhausted.",
                        status_code=429
                    )
                elif response.status_code >= 400:
                    raise SerpApiError(
                        message=f"SerpApi API error HTTP {response.status_code}: {response.text}",
                        status_code=response.status_code
                    )

                try:
                    data = response.json()
                except Exception as json_err:
                    raise SerpApiError(
                        message=f"Malformed response from SerpApi: Failed to decode JSON: {str(json_err)}"
                    )

                # Inspect payload for SerpApi inline error messages
                if isinstance(data, dict) and "error" in data:
                    err_msg = str(data["error"])
                    if "Invalid API key" in err_msg or "account" in err_msg.lower():
                        raise SerpApiAuthError(message=f"SerpApi Error: {err_msg}", raw_response=data)
                    raise SerpApiError(message=f"SerpApi Error: {err_msg}", raw_response=data)

                return data

        except httpx.TimeoutException as exc:
            raise SerpApiNetworkError(message=f"SerpApi request timed out after {self.timeout}s: {str(exc)}")
        except httpx.NetworkError as exc:
            raise SerpApiNetworkError(message=f"Network error connecting to SerpApi: {str(exc)}")
        except httpx.HTTPError as exc:
            raise SerpApiNetworkError(message=f"HTTP request error: {str(exc)}")
        except SerpApiError:
            raise
        except Exception as exc:
            raise SerpApiError(message=f"Unexpected error during SerpApi search: {str(exc)}")

    async def search(
        self,
        engine: str = SearchEngineType.GOOGLE.value,
        query: str = "",
        location: Optional[str] = "India",
        **kwargs
    ) -> NormalizedSearchResponse:
        """
        Executes search for any specified engine and returns normalized models.
        """
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty.")

        params = build_engine_params(
            engine=engine,
            query=query,
            location=location,
            **kwargs
        )

        raw_data = await self.execute_raw_request(params)
        return normalize_serpapi_response(engine=engine, query=query, raw_data=raw_data)

    async def search_web(
        self,
        query: str,
        location: Optional[str] = "India",
        num: int = 10,
        **kwargs
    ) -> NormalizedSearchResponse:
        """Reusable convenience method for Organic Web Search."""
        return await self.search(
            engine=SearchEngineType.GOOGLE.value,
            query=query,
            location=location,
            num=num,
            **kwargs
        )

    async def search_shopping(
        self,
        query: str,
        location: Optional[str] = "India",
        num: int = 10,
        **kwargs
    ) -> NormalizedSearchResponse:
        """Reusable convenience method for Google Shopping Search."""
        return await self.search(
            engine=SearchEngineType.GOOGLE_SHOPPING.value,
            query=query,
            location=location,
            num=num,
            **kwargs
        )

    async def search_youtube(
        self,
        query: str,
        **kwargs
    ) -> NormalizedSearchResponse:
        """Reusable convenience method for YouTube Search."""
        return await self.search(
            engine=SearchEngineType.YOUTUBE.value,
            query=query,
            **kwargs
        )
