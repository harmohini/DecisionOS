import pytest
from unittest.mock import MagicMock
from app.models.schemas import (
    ResearchPlan,
    EvidenceClaim,
    DetectedConflict,
    ComparisonResult
)
from app.agents.comparison import OptionComparator
from app.services.llm import LLMService

@pytest.fixture
def sample_plan():
    return ResearchPlan(
        decision_category="electronics/product research",
        user_goal="Find a laptop for programming and AI/ML",
        budget="₹1,20,000",
        hard_constraints=["16GB RAM"],
        preferences=["good battery life"],
        important_attributes=["RAM", "GPU", "Battery life", "Price"],
        research_questions=["Which laptops under ₹1,20,000 offer 16GB RAM?"],
        required_search_types=["web", "shopping", "youtube"],
        comparison_criteria=["RAM size", "Price", "Battery life"]
    )

@pytest.fixture
def hotel_plan():
    return ResearchPlan(
        decision_category="travel/hotel research",
        user_goal="Find a beach resort in Goa under $800",
        budget="$800",
        hard_constraints=["beach resort"],
        preferences=["free breakfast"],
        important_attributes=["location", "amenities", "price"],
        research_questions=["Which hotels in Goa are under $800?"],
        required_search_types=["web"],
        comparison_criteria=["Price", "Beach access"]
    )

@pytest.fixture
def sample_claims_two_options():
    return [
        # Option 1: Lenovo Legion Slim 5
        EvidenceClaim(
            claim_id="c1",
            entity="Lenovo Legion Slim 5",
            attribute="RAM",
            value="16GB",
            source_url="https://lenovo.com/slim5",
            source_type="official",
            evidence_text="16GB DDR5 RAM"
        ),
        EvidenceClaim(
            claim_id="c2",
            entity="Lenovo Legion Slim 5",
            attribute="price",
            value="₹1,15,000",
            source_url="https://amazon.in/slim5",
            source_type="retailer",
            evidence_text="Price ₹1,15,000"
        ),
        EvidenceClaim(
            claim_id="c3",
            entity="Lenovo Legion Slim 5",
            attribute="battery life",
            value="described as good",
            source_url="https://techreview.com/slim5",
            source_type="review",
            evidence_text="Battery life described as good"
        ),
        # Option 2: ASUS ROG Zephyrus G14
        EvidenceClaim(
            claim_id="c4",
            entity="ASUS ROG Zephyrus G14",
            attribute="RAM",
            value="16GB",
            source_url="https://asus.com/g14",
            source_type="official",
            evidence_text="16GB LPDDR5 RAM"
        ),
        EvidenceClaim(
            claim_id="c5",
            entity="ASUS ROG Zephyrus G14",
            attribute="price",
            value="₹1,18,000",
            source_url="https://flipkart.com/g14",
            source_type="retailer",
            evidence_text="Price ₹1,18,000"
        )
    ]

@pytest.mark.asyncio
async def test_two_option_comparison(sample_plan, sample_claims_two_options):
    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=sample_claims_two_options)

    assert isinstance(res, ComparisonResult)
    assert len(res.compared_options) == 2
    assert "Lenovo Legion Slim 5" in res.compared_options
    assert "ASUS ROG Zephyrus G14" in res.compared_options
    assert len(res.option_comparisons) == 2

@pytest.mark.asyncio
async def test_three_option_comparison(sample_plan, sample_claims_two_options):
    option3_claims = [
        EvidenceClaim(
            claim_id="c6",
            entity="HP Omen 16",
            attribute="RAM",
            value="16GB",
            source_url="https://hp.com/omen16",
            source_type="official",
            evidence_text="16GB RAM"
        ),
        EvidenceClaim(
            claim_id="c7",
            entity="HP Omen 16",
            attribute="price",
            value="₹1,10,000",
            source_url="https://hp.com/omen16",
            source_type="official",
            evidence_text="Price ₹1,10,000"
        )
    ]
    all_claims = sample_claims_two_options + option3_claims

    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=all_claims)

    assert len(res.compared_options) == 3
    assert "HP Omen 16" in res.compared_options

@pytest.mark.asyncio
async def test_hard_constraint_satisfied(sample_plan, sample_claims_two_options):
    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=sample_claims_two_options)

    lenovo_opt = [o for o in res.option_comparisons if o.option_name == "Lenovo Legion Slim 5"][0]
    ram_match = [m for m in lenovo_opt.requirement_alignment if "16GB" in m.requirement][0]

    assert ram_match.status == "satisfies"
    assert "meets or exceeds" in ram_match.explanation or "16GB" in ram_match.explanation

@pytest.mark.asyncio
async def test_hard_constraint_not_satisfied(sample_plan):
    failing_claim = [
        EvidenceClaim(
            claim_id="cf",
            entity="Budget Laptop Y",
            attribute="RAM",
            value="8GB",
            source_url="https://store.com/laptopy",
            source_type="retailer",
            evidence_text="8GB RAM model"
        )
    ]

    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=failing_claim)

    opt = res.option_comparisons[0]
    ram_match = [m for m in opt.requirement_alignment if "16GB" in m.requirement][0]

    assert ram_match.status == "does_not_satisfy"
    assert "less than required" in ram_match.explanation

@pytest.mark.asyncio
async def test_partial_requirement_match(sample_plan, sample_claims_two_options):
    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=sample_claims_two_options)

    lenovo_opt = [o for o in res.option_comparisons if o.option_name == "Lenovo Legion Slim 5"][0]
    batt_match = [m for m in lenovo_opt.requirement_alignment if "battery" in m.requirement.lower()][0]

    assert batt_match.status == "partially_satisfies"

@pytest.mark.asyncio
async def test_unknown_requirement(sample_plan, sample_claims_two_options):
    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=sample_claims_two_options)

    asus_opt = [o for o in res.option_comparisons if o.option_name == "ASUS ROG Zephyrus G14"][0]
    # ASUS has no battery claim in fixture -> must be unknown
    batt_match = [m for m in asus_opt.requirement_alignment if "battery" in m.requirement.lower()][0]

    assert batt_match.status == "unknown"
    assert "No verified evidence available" in batt_match.explanation

@pytest.mark.asyncio
async def test_conflicting_evidence_handling(sample_plan, sample_claims_two_options):
    conflict = DetectedConflict(
        conflict_id="conf1",
        entity="Lenovo Legion Slim 5",
        attribute="RAM",
        conflicting_values=["16GB", "32GB"],
        severity="medium",
        resolution_status="unresolved",
        explanation="Opposing RAM values reported",
        recommended_verification="Verify SKU"
    )

    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=sample_claims_two_options, conflicts=[conflict])

    lenovo_opt = [o for o in res.option_comparisons if o.option_name == "Lenovo Legion Slim 5"][0]
    ram_match = [m for m in lenovo_opt.requirement_alignment if "16GB" in m.requirement][0]

    assert ram_match.status == "conflicting"
    assert "Conflicting information detected" in ram_match.explanation

@pytest.mark.asyncio
async def test_trade_off_extraction(sample_plan, sample_claims_two_options):
    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=sample_claims_two_options)

    assert isinstance(res.trade_offs, list)
    assert len(res.trade_offs) > 0

@pytest.mark.asyncio
async def test_provenance_preservation(sample_plan, sample_claims_two_options):
    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=sample_claims_two_options)

    for opt in res.option_comparisons:
        assert len(opt.source_references) > 0
        for src in opt.source_references:
            assert "url" in src
            assert src["url"].startswith("http")

@pytest.mark.asyncio
async def test_no_unsupported_claims(sample_plan, sample_claims_two_options):
    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=sample_claims_two_options)

    # Ensure no arbitrary 1-10 numerical ratings exist in option comparisons
    for opt in res.option_comparisons:
        assert not hasattr(opt, "rating_score")

@pytest.mark.asyncio
async def test_empty_evidence(sample_plan):
    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=[])

    assert res.compared_options == []
    assert res.option_comparisons == []

@pytest.mark.asyncio
async def test_empty_options(sample_plan):
    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=[])

    assert res.compared_options == []

@pytest.mark.asyncio
async def test_dynamic_option_identification(hotel_plan):
    hotel_claims = [
        EvidenceClaim(
            claim_id="h1",
            entity="Goa Marriott Resort & Spa",
            attribute="price",
            value="$750",
            source_url="https://marriott.com/goa",
            source_type="official",
            evidence_text="4 nights $750"
        ),
        EvidenceClaim(
            claim_id="h2",
            entity="Taj Fort Aguada Resort",
            attribute="price",
            value="$790",
            source_url="https://tajhotels.com/goa",
            source_type="official",
            evidence_text="4 nights $790"
        )
    ]

    comparator = OptionComparator()
    res = await comparator.compare_options(plan=hotel_plan, claims=hotel_claims)

    assert len(res.compared_options) == 2
    assert "Goa Marriott Resort & Spa" in res.compared_options
    assert "Taj Fort Aguada Resort" in res.compared_options

@pytest.mark.asyncio
async def test_budget_comparison(sample_plan, sample_claims_two_options):
    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=sample_claims_two_options)

    for opt in res.option_comparisons:
        budget_matches = [m for m in opt.requirement_alignment if "budget" in m.requirement.lower()]
        assert len(budget_matches) > 0
        assert budget_matches[0].status == "satisfies"

@pytest.mark.asyncio
async def test_multiple_criteria(sample_plan, sample_claims_two_options):
    comparator = OptionComparator()
    res = await comparator.compare_options(plan=sample_plan, claims=sample_claims_two_options)

    assert len(res.criteria) >= 3

@pytest.mark.asyncio
async def test_different_decision_categories(hotel_plan):
    hotel_claim = EvidenceClaim(
        claim_id="h1",
        entity="Goa Marriott Resort",
        attribute="beach resort",
        value="beachfront",
        source_url="https://marriott.com",
        source_type="official",
        evidence_text="Beachfront 4-star resort"
    )

    comparator = OptionComparator()
    res = await comparator.compare_options(plan=hotel_plan, claims=[hotel_claim])

    assert res.decision_category == "travel/hotel research"
    assert res.compared_options == ["Goa Marriott Resort"]
