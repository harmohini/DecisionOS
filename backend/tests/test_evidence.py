import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.schemas import ResearchResult, EvidenceClaim, ExtractedClaimList, ExtractedClaimItem
from app.agents.evidence import EvidenceExtractor, classify_source, calculate_confidence
from app.services.llm import LLMService

@pytest.fixture
def sample_laptop_result():
    return ResearchResult(
        result_id="res_001",
        query="laptop 16GB RAM RTX 4060",
        source_type="web",
        title="Lenovo Legion Slim 5 Review",
        url="https://notebookcheck.net/lenovo-legion-slim-5-review.html",
        snippet="16GB RAM, RTX 4060 GPU and approximately 7 hours of battery life.",
        price="₹1,15,000",
        rating=4.6
    )

@pytest.fixture
def official_result():
    return ResearchResult(
        result_id="res_002",
        query="Lenovo Legion official specs",
        source_type="web",
        title="Lenovo Official Store - Legion Slim 5",
        url="https://www.lenovo.com/in/en/laptops/legion/slim-5",
        snippet="Official specs: 16GB RAM, 512GB SSD.",
        price="₹1,15,000"
    )

@pytest.fixture
def retailer_result():
    return ResearchResult(
        result_id="res_003",
        query="buy Lenovo Legion Slim 5",
        source_type="shopping",
        title="Lenovo Legion Slim 5 on Amazon",
        url="https://www.amazon.in/dp/B0C123456",
        snippet="Buy Lenovo Legion Slim 5 with 16GB RAM.",
        price="₹1,12,000"
    )

def test_source_classification():
    assert classify_source("https://www.lenovo.com/in/en/laptops") == "official"
    assert classify_source("https://www.amazon.in/dp/B0C123") == "retailer"
    assert classify_source("https://www.notebookcheck.net/review") == "review"
    assert classify_source("https://www.youtube.com/watch?v=123", result_source_type="youtube") == "video"
    assert classify_source("https://www.reddit.com/r/laptops") == "forum"
    assert classify_source("https://www.techcrunch.com/ai-news") == "news"
    assert classify_source("https://random-blog.org/my-thoughts") == "general_web"
    assert classify_source("") == "unknown"

def test_confidence_calculation():
    # Explicit spec + official/review source -> HIGH
    assert calculate_confidence("16GB", "16GB RAM spec", "official") == "HIGH"
    assert calculate_confidence("RTX 4060", "RTX 4060 GPU included", "review") == "HIGH"
    
    # Qualitative vague statement + general web -> LOW
    assert calculate_confidence("described as excellent", "Review mentions good battery", "general_web") == "LOW"
    assert calculate_confidence("described as excellent", "Good battery performance", "forum") == "LOW"

    # Qualitative vague statement + review source -> MEDIUM
    assert calculate_confidence("described as excellent", "Good battery performance", "review") == "MEDIUM"

    # Missing evidence or value -> UNKNOWN
    assert calculate_confidence("", "evidence text", "official") == "UNKNOWN"
    assert calculate_confidence("16GB", "", "official") == "UNKNOWN"

@pytest.mark.asyncio
async def test_explicit_spec_and_price_extraction(sample_laptop_result):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.is_configured = False  # Test rule-based extraction path

    extractor = EvidenceExtractor(llm_service=mock_llm)
    claims = await extractor.extract_evidence([sample_laptop_result])

    attributes = {c.attribute: c.value for c in claims}
    assert "price" in attributes
    assert attributes["price"] == "₹1,15,000"
    assert "RAM" in attributes
    assert attributes["RAM"] == "16GB"
    assert "GPU" in attributes
    assert attributes["GPU"] == "RTX 4060"

@pytest.mark.asyncio
async def test_review_statement_and_multiple_claims(sample_laptop_result):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.is_configured = False

    extractor = EvidenceExtractor(llm_service=mock_llm)
    claims = await extractor.extract_evidence([sample_laptop_result])

    assert len(claims) >= 3  # price, RAM, GPU, battery
    for claim in claims:
        assert claim.source_url == sample_laptop_result.url
        assert claim.supporting_result_id == sample_laptop_result.result_id

@pytest.mark.asyncio
async def test_missing_and_vague_evidence():
    vague_result = ResearchResult(
        result_id="res_vague",
        query="battery life review",
        source_type="web",
        title="Laptop User Thoughts",
        url="https://general-forum.org/post1",
        snippet="Overall decent battery life."
    )

    mock_llm = MagicMock(spec=LLMService)
    mock_llm.is_configured = False

    extractor = EvidenceExtractor(llm_service=mock_llm)
    claims = await extractor.extract_evidence([vague_result])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.attribute == "battery life"
    assert "described as" in claim.value
    assert claim.confidence in ["LOW", "MEDIUM"]
    assert claim.value != "10 hours"  # Must NOT invent numeric specs from vague statement!

@pytest.mark.asyncio
async def test_official_retailer_review_classification(official_result, retailer_result, sample_laptop_result):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.is_configured = False

    extractor = EvidenceExtractor(llm_service=mock_llm)
    
    off_claims = await extractor.extract_evidence([official_result])
    ret_claims = await extractor.extract_evidence([retailer_result])
    rev_claims = await extractor.extract_evidence([sample_laptop_result])

    assert off_claims[0].source_type == "official"
    assert ret_claims[0].source_type == "retailer"
    assert rev_claims[0].source_type == "review"

@pytest.mark.asyncio
async def test_provenance_preservation(sample_laptop_result):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.is_configured = True
    
    mock_llm.generate_structured_output = AsyncMock(return_value=ExtractedClaimList(
        claims=[
            ExtractedClaimItem(
                entity="Lenovo Legion Slim 5",
                attribute="RAM",
                value="16GB",
                evidence_text="16GB RAM spec"
            )
        ]
    ))

    extractor = EvidenceExtractor(llm_service=mock_llm)
    claims = await extractor.extract_evidence([sample_laptop_result])

    assert len(claims) > 0
    for claim in claims:
        assert claim.source_url == sample_laptop_result.url  # Strict provenance requirement
        assert claim.supporting_result_id == sample_laptop_result.result_id

@pytest.mark.asyncio
async def test_duplicate_claim_handling(sample_laptop_result):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.is_configured = False

    extractor = EvidenceExtractor(llm_service=mock_llm)
    # Pass duplicate result items with same URL and specs
    claims = await extractor.extract_evidence([sample_laptop_result, sample_laptop_result])

    # Identical claims from same URL must be deduplicated
    unique_keys = set(f"{c.entity}|{c.attribute}|{c.value}|{c.source_url}" for c in claims)
    assert len(claims) == len(unique_keys)

@pytest.mark.asyncio
async def test_invalid_llm_output_handling(sample_laptop_result):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.is_configured = True
    # LLM returns invalid empty items
    mock_llm.generate_structured_output = AsyncMock(return_value=ExtractedClaimList(
        claims=[
            ExtractedClaimItem(entity="", attribute="", value="", evidence_text="")
        ]
    ))

    extractor = EvidenceExtractor(llm_service=mock_llm)
    claims = await extractor.extract_evidence([sample_laptop_result])

    # Rule-based claims still extracted, invalid empty LLM items filtered out
    for claim in claims:
        assert claim.entity != ""
        assert claim.attribute != ""
        assert claim.value != ""

@pytest.mark.asyncio
async def test_missing_source_url_handling():
    no_url_result = ResearchResult(
        result_id="res_nourl",
        query="no url test",
        source_type="web",
        title="Test Title",
        url="",  # Empty URL
        snippet="16GB RAM spec"
    )

    mock_llm = MagicMock(spec=LLMService)
    mock_llm.is_configured = False

    extractor = EvidenceExtractor(llm_service=mock_llm)
    claims = await extractor.extract_evidence([no_url_result])

    assert claims == []  # Items missing source URL are ignored

@pytest.mark.asyncio
async def test_empty_research_results_handling():
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.is_configured = False

    extractor = EvidenceExtractor(llm_service=mock_llm)
    claims = await extractor.extract_evidence([])

    assert claims == []
