from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from app.serpapi.client import (
    SerpApiClient,
    SerpApiMissingKeyError,
    SerpApiAuthError,
    SerpApiRateLimitError,
    SerpApiNetworkError,
    SerpApiError
)
from app.models.schemas import NormalizedSearchResponse

router = APIRouter(prefix="/api/v1/search", tags=["Search"])

@router.get("/test", response_model=NormalizedSearchResponse)
async def test_search(
    q: str = Query("latest artificial intelligence news", description="Search query string"),
    engine: str = Query("google", description="Engine type: 'google', 'google_shopping', or 'youtube'"),
    location: Optional[str] = Query("India", description="Location context for search")
):
    """
    Test endpoint for executing SerpApi search from backend.
    Returns normalized Python data models without exposing API keys.
    """
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'q' cannot be empty."
        )

    client = SerpApiClient()

    try:
        response = await client.search(
            engine=engine,
            query=q,
            location=location
        )
        return response

    except SerpApiMissingKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except SerpApiAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"SerpApi authentication error: {exc.message}"
        )
    except SerpApiRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"SerpApi rate limit exceeded: {exc.message}"
        )
    except SerpApiNetworkError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SerpApi network connection error: {exc.message}"
        )
    except SerpApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SerpApi search error: {exc.message}"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(exc)}"
        )
