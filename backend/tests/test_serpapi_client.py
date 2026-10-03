import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.serpapi.client import (
    SerpApiClient,
    SerpApiMissingKeyError,
    SerpApiAuthError,
    SerpApiRateLimitError,
    SerpApiNetworkError,
    SerpApiError
)
from app.serpapi.engines import SearchEngineType

@pytest.mark.asyncio
async def test_missing_api_key_empty_string_raises_exception():
    with pytest.raises(SerpApiMissingKeyError):
        SerpApiClient(api_key="")

@pytest.mark.asyncio
async def test_missing_api_key_none_raises_exception():
    with patch("app.serpapi.client.settings.SERPAPI_API_KEY", ""):
        with pytest.raises(SerpApiMissingKeyError):
            SerpApiClient(api_key=None)

@pytest.mark.asyncio
async def test_missing_api_key_whitespace_raises_exception():
    with pytest.raises(SerpApiMissingKeyError):
        SerpApiClient(api_key="   ")

@pytest.mark.asyncio
async def test_organic_web_search_normalization():
    client = SerpApiClient(api_key="test_mock_key")
    
    mock_response_data = {
        "search_metadata": {
            "id": "search_123",
            "status": "Success",
            "total_time_taken": 0.45
        },
        "knowledge_graph": {
            "entity_id": "kg_1",
            "title": "ASUS ROG Zephyrus G14",
            "description": "High performance gaming laptop",
            "source": {"name": "ASUS Official", "link": "https://asus.com"}
        },
        "organic_results": [
            {
                "position": 1,
                "title": "Best Laptops for Machine Learning 2026",
                "link": "https://example.com/ml-laptops",
                "displayed_link": "example.com",
                "snippet": "Top picks include ASUS ROG, Lenovo Legion with 16GB RAM and RTX 4060."
            }
        ]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response_data
        mock_get.return_value = mock_resp

        res = await client.search_web("laptop for ML", location="India")

        assert res.query == "laptop for ML"
        assert res.engine == "google"
        assert res.total_results == 2  # 1 knowledge graph + 1 organic
        assert res.results[0].result_type == "knowledge_graph"
        assert res.results[0].title == "ASUS ROG Zephyrus G14"
        assert res.results[1].result_type == "organic"
        assert res.results[1].title == "Best Laptops for Machine Learning 2026"
        assert res.results[1].source == "example.com"

@pytest.mark.asyncio
async def test_shopping_search_normalization():
    client = SerpApiClient(api_key="test_mock_key")
    
    mock_shopping_data = {
        "shopping_results": [
            {
                "position": 1,
                "title": "Lenovo Legion Slim 5 Gaming Laptop",
                "link": "https://shopping-example.com/lenovo",
                "source": "Lenovo Store",
                "price": "₹1,15,000",
                "extracted_price": 115000.0,
                "currency": "INR",
                "rating": 4.6,
                "reviews": 128,
                "thumbnail": "https://example.com/thumb.jpg",
                "extensions": ["16GB RAM", "512GB SSD", "RTX 4060"]
            }
        ]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_shopping_data
        mock_get.return_value = mock_resp

        res = await client.search_shopping("gaming laptop ₹120000")

        assert res.engine == "google_shopping"
        assert res.total_results == 1
        item = res.results[0]
        assert item.result_type == "shopping"
        assert item.price == "₹1,15,000"
        assert item.price_raw == 115000.0
        assert item.source == "Lenovo Store"
        assert item.rating == 4.6
        assert item.reviews_count == 128

@pytest.mark.asyncio
async def test_youtube_search_normalization():
    client = SerpApiClient(api_key="test_mock_key")
    
    mock_youtube_data = {
        "video_results": [
            {
                "video_id": "xyz123",
                "title": "Lenovo Legion Slim 5 Review - Worth it for Programming?",
                "link": "https://www.youtube.com/watch?v=xyz123",
                "channel": {"name": "Tech Reviews"},
                "description": "Comprehensive review testing battery life, thermal specs and coding benchmarks.",
                "views": "150K views",
                "length": "12:45"
            }
        ]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_youtube_data
        mock_get.return_value = mock_resp

        res = await client.search_youtube("lenovo legion slim 5 review")

        assert res.engine == "youtube"
        assert res.total_results == 1
        item = res.results[0]
        assert item.result_type == "youtube"
        assert item.id == "xyz123"
        assert "Tech Reviews" in item.source

@pytest.mark.asyncio
async def test_auth_error_handling():
    client = SerpApiClient(api_key="invalid_key")
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        with pytest.raises(SerpApiAuthError):
            await client.search(query="test query")

@pytest.mark.asyncio
async def test_rate_limit_error_handling():
    client = SerpApiClient(api_key="test_mock_key")
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_get.return_value = mock_resp

        with pytest.raises(SerpApiRateLimitError):
            await client.search(query="test query")

@pytest.mark.asyncio
async def test_network_timeout_handling():
    client = SerpApiClient(api_key="test_mock_key")
    
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(SerpApiNetworkError):
            await client.search(query="test query")

@pytest.mark.asyncio
async def test_inline_serpapi_error_response():
    client = SerpApiClient(api_key="test_mock_key")
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"error": "Invalid API key."}
        mock_get.return_value = mock_resp

        with pytest.raises(SerpApiAuthError):
            await client.search(query="test query")

@pytest.mark.asyncio
async def test_empty_results_handling():
    client = SerpApiClient(api_key="test_mock_key")
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_get.return_value = mock_resp

        res = await client.search_web("nonexistent query")
        assert res.total_results == 0
        assert res.results == []
