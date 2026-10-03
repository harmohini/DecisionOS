import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.schemas import (
    ResearchPlan,
    NormalizedSearchResponse,
    NormalizedSearchResult,
    ResearchResult
)
from app.services.query_builder import QueryBuilder
from app.agents.researcher import InformationResearcher, normalize_url
from app.serpapi.client import SerpApiClient, SerpApiError, SerpApiNetworkError

@pytest.fixture
def sample_plan():
    return ResearchPlan(
        decision_category="electronics/product research",
        user_goal="Find a laptop for AI/ML development and gaming",
        budget="₹1,20,000",
        hard_constraints=["16GB RAM"],
        preferences=["good battery life"],
        important_attributes=["RAM", "Battery life", "GPU", "Price"],
        research_questions=[
            "Which laptops under ₹1,20,000 offer 16GB RAM?",
            "What is the battery life performance reported in coding reviews?"
        ],
        required_search_types=["web", "shopping", "youtube"],
        comparison_criteria=["RAM size", "Price", "Battery life"]
    )

@pytest.fixture
def mock_web_response():
    return NormalizedSearchResponse(
        query="laptop 16GB RAM",
        engine="google",
        total_results=2,
        results=[
            NormalizedSearchResult(
                id="1",
                title="ASUS ROG Zephyrus G14 Review",
                link="https://example.com/asus-g14?utm_source=test",
                source="example.com",
                snippet="Great laptop for ML and coding with RTX GPU.",
                rating=4.5,
                reviews_count=95
            ),
            NormalizedSearchResult(
                id="2",
                title="Lenovo Legion Slim 5 Deep Dive",
                link="https://tech-reviews.org/lenovo-legion",
                source="tech-reviews.org",
                snippet="Excellent 16GB RAM laptop under ₹1,20,000.",
                rating=4.7,
                reviews_count=140
            )
        ]
    )

@pytest.fixture
def mock_shopping_response():
    return NormalizedSearchResponse(
        query="buy laptop 16GB RAM",
        engine="google_shopping",
        total_results=1,
        results=[
            NormalizedSearchResult(
                id="shop_1",
                title="Lenovo Legion Slim 5 Gaming Laptop",
                link="https://shopping-store.com/lenovo-legion-slim-5",
                source="Lenovo Store",
                price="₹1,15,000",
                price_raw=115000.0,
                currency="INR",
                rating=4.6,
                reviews_count=120,
                thumbnail="https://example.com/thumb.jpg"
            )
        ]
    )

@pytest.fixture
def mock_youtube_response():
    return NormalizedSearchResponse(
        query="laptop review",
        engine="youtube",
        total_results=1,
        results=[
            NormalizedSearchResult(
                id="yt_1",
                title="Lenovo Legion Slim 5 Long-Term Review",
                link="https://www.youtube.com/watch?v=xyz123",
                source="YouTube (Tech Channel)",
                snippet="Battery life & ML thermal test results.",
                thumbnail="https://example.com/yt_thumb.jpg"
            )
        ]
    )

def test_url_normalization():
    url1 = "https://WWW.EXAMPLE.COM/product/laptop/?utm_source=google&ref=123"
    url2 = "https://example.com/product/laptop"
    assert normalize_url(url1) == normalize_url(url2)

def test_query_generation_from_plan(sample_plan):
    builder = QueryBuilder(max_queries=5)
    queries = builder.build_queries(sample_plan)

    assert len(queries) <= 5
    search_types = {q.search_type for q in queries}
    assert "web" in search_types
    assert "shopping" in search_types
    assert "youtube" in search_types

@pytest.mark.asyncio
async def test_web_search_execution(sample_plan, mock_web_response):
    mock_client = MagicMock(spec=SerpApiClient)
    mock_client.search_web = AsyncMock(return_value=mock_web_response)
    mock_client.search_shopping = AsyncMock(return_value=None)
    mock_client.search_youtube = AsyncMock(return_value=None)

    builder = QueryBuilder(max_queries=1)
    researcher = InformationResearcher(serpapi_client=mock_client, query_builder=builder)

    results = await researcher.execute_research(sample_plan)

    mock_client.search_web.assert_called_once()
    assert len(results) == 2
    assert results[0].source_type == "web"
    assert results[0].url == "https://example.com/asus-g14?utm_source=test"

@pytest.mark.asyncio
async def test_shopping_search_execution(mock_shopping_response):
    plan = ResearchPlan(
        decision_category="product",
        user_goal="Buy laptop",
        required_search_types=["shopping"]
    )
    mock_client = MagicMock(spec=SerpApiClient)
    mock_client.search_shopping = AsyncMock(return_value=mock_shopping_response)

    builder = QueryBuilder(max_queries=1)
    researcher = InformationResearcher(serpapi_client=mock_client, query_builder=builder)

    results = await researcher.execute_research(plan)

    mock_client.search_shopping.assert_called_once()
    assert len(results) == 1
    assert results[0].source_type == "shopping"
    assert results[0].price == "₹1,15,000"

@pytest.mark.asyncio
async def test_youtube_search_execution(mock_youtube_response):
    plan = ResearchPlan(
        decision_category="product",
        user_goal="Review laptop",
        required_search_types=["youtube"]
    )
    mock_client = MagicMock(spec=SerpApiClient)
    mock_client.search_youtube = AsyncMock(return_value=mock_youtube_response)

    builder = QueryBuilder(max_queries=1)
    researcher = InformationResearcher(serpapi_client=mock_client, query_builder=builder)

    results = await researcher.execute_research(plan)

    mock_client.search_youtube.assert_called_once()
    assert len(results) == 1
    assert results[0].source_type == "youtube"

@pytest.mark.asyncio
async def test_multiple_search_types_execution(
    sample_plan,
    mock_web_response,
    mock_shopping_response,
    mock_youtube_response
):
    mock_client = MagicMock(spec=SerpApiClient)
    mock_client.search_web = AsyncMock(return_value=mock_web_response)
    mock_client.search_shopping = AsyncMock(return_value=mock_shopping_response)
    mock_client.search_youtube = AsyncMock(return_value=mock_youtube_response)

    researcher = InformationResearcher(serpapi_client=mock_client)

    results = await researcher.execute_research(sample_plan)

    source_types = {r.source_type for r in results}
    assert "web" in source_types
    assert "shopping" in source_types
    assert "youtube" in source_types

@pytest.mark.asyncio
async def test_result_normalization_and_provenance(sample_plan, mock_shopping_response):
    mock_client = MagicMock(spec=SerpApiClient)
    mock_client.search_shopping = AsyncMock(return_value=mock_shopping_response)
    mock_client.search_web = AsyncMock(return_value=None)
    mock_client.search_youtube = AsyncMock(return_value=None)

    researcher = InformationResearcher(serpapi_client=mock_client)
    results = await researcher.execute_research(sample_plan)

    item = results[0]
    assert isinstance(item, ResearchResult)
    assert item.url == "https://shopping-store.com/lenovo-legion-slim-5"  # Exact provenance URL
    assert item.title == "Lenovo Legion Slim 5 Gaming Laptop"
    assert item.price == "₹1,15,000"
    assert item.rating == 4.6

@pytest.mark.asyncio
async def test_duplicate_removal(sample_plan):
    duplicate_response = NormalizedSearchResponse(
        query="laptop 16GB RAM",
        engine="google",
        total_results=2,
        results=[
            NormalizedSearchResult(
                id="1",
                title="ASUS ROG Review - Site A",
                link="https://example.com/asus-g14?utm_source=a"
            ),
            NormalizedSearchResult(
                id="2",
                title="ASUS ROG Review - Duplicate link",
                link="https://example.com/asus-g14?utm_source=b"
            )
        ]
    )

    mock_client = MagicMock(spec=SerpApiClient)
    mock_client.search_web = AsyncMock(return_value=duplicate_response)
    mock_client.search_shopping = AsyncMock(return_value=None)
    mock_client.search_youtube = AsyncMock(return_value=None)

    builder = QueryBuilder(max_queries=1)
    researcher = InformationResearcher(serpapi_client=mock_client, query_builder=builder)

    results = await researcher.execute_research(sample_plan)

    assert len(results) == 1  # Duplicate filtered out
    assert results[0].url == "https://example.com/asus-g14?utm_source=a"

@pytest.mark.asyncio
async def test_empty_search_results(sample_plan):
    empty_response = NormalizedSearchResponse(query="empty", engine="google", total_results=0, results=[])
    mock_client = MagicMock(spec=SerpApiClient)
    mock_client.search_web = AsyncMock(return_value=empty_response)
    mock_client.search_shopping = AsyncMock(return_value=empty_response)
    mock_client.search_youtube = AsyncMock(return_value=empty_response)

    researcher = InformationResearcher(serpapi_client=mock_client)
    results = await researcher.execute_research(sample_plan)

    assert results == []

@pytest.mark.asyncio
async def test_serpapi_failure_handling_continues_other_queries(sample_plan, mock_web_response):
    mock_client = MagicMock(spec=SerpApiClient)
    # First search fails with network error, second succeeds
    mock_client.search_web = AsyncMock(side_effect=[SerpApiNetworkError("Timeout"), mock_web_response])
    mock_client.search_shopping = AsyncMock(return_value=None)
    mock_client.search_youtube = AsyncMock(return_value=None)

    researcher = InformationResearcher(serpapi_client=mock_client)
    results = await researcher.execute_research(sample_plan)

    # Whole research run does not crash, valid results from second query returned
    assert len(results) == 2

@pytest.mark.asyncio
async def test_max_query_limit_enforcement(sample_plan, mock_web_response):
    mock_client = MagicMock(spec=SerpApiClient)
    mock_client.search_web = AsyncMock(return_value=mock_web_response)
    mock_client.search_shopping = AsyncMock(return_value=None)
    mock_client.search_youtube = AsyncMock(return_value=None)

    builder = QueryBuilder(max_queries=2)
    researcher = InformationResearcher(serpapi_client=mock_client, query_builder=builder)

    await researcher.execute_research(sample_plan)

    total_calls = mock_client.search_web.call_count + mock_client.search_shopping.call_count + mock_client.search_youtube.call_count
    assert total_calls <= 2

@pytest.mark.asyncio
async def test_preservation_of_source_urls(sample_plan, mock_web_response):
    mock_client = MagicMock(spec=SerpApiClient)
    mock_client.search_web = AsyncMock(return_value=mock_web_response)
    mock_client.search_shopping = AsyncMock(return_value=None)
    mock_client.search_youtube = AsyncMock(return_value=None)

    builder = QueryBuilder(max_queries=1)
    researcher = InformationResearcher(serpapi_client=mock_client, query_builder=builder)

    results = await researcher.execute_research(sample_plan)

    for item in results:
        assert item.url is not None
        assert item.url.startswith("http")
