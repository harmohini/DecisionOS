import pytest
from unittest.mock import MagicMock
from app.models.schemas import (
    ResearchPlan,
    ResearchResult,
    EvidenceClaim,
    DetectedConflict,
    OptionComparison,
    OptionRequirementMatch,
    ComparisonResult,
    FinalDecisionReport
)
from app.agents.report import FinalReportGenerator
from app.services.llm import LLMService

@pytest.fixture
def sample_plan():
    return ResearchPlan(
        decision_category="electronics/product research",
        user_goal="Find a laptop for programming and AI/ML",
        budget="₹1,20,000",
        hard_constraints=["16GB RAM"],
        preferences=["good battery life"],
        important_attributes=["RAM", "Price", "Battery life"]
    )

@pytest.fixture
def sample_results():
    return [
        ResearchResult(
            result_id="res_1",
            query="laptop 16GB RAM",
            source_type="web",
            title="Lenovo Legion Slim 5 Specs",
            url="https://lenovo.com/slim5",
            snippet="16GB DDR5 RAM, RTX 4060 GPU."
        )
    ]

@pytest.fixture
def sample_claims():
    return [
        EvidenceClaim(
            claim_id="c1",
            entity="Lenovo Legion Slim 5",
            attribute="RAM",
            value="16GB",
            source_url="https://lenovo.com/slim5",
            source_title="Lenovo Legion Slim 5 Specs",
            source_type="official",
            evidence_text="16GB DDR5 RAM"
        )
    ]

@pytest.fixture
def sample_conflict():
    return DetectedConflict(
        conflict_id="conf_1",
        entity="Lenovo Legion Slim 5",
        attribute="RAM",
        conflicting_values=["16GB", "32GB"],
        severity="medium",
        resolution_status="resolved",
        explanation="Official source confirms 16GB, single retailer lists 32GB.",
        recommended_verification="Check official Lenovo spec sheet."
    )

@pytest.fixture
def sample_comparison():
    return ComparisonResult(
        decision_category="electronics/product research",
        compared_options=["Lenovo Legion Slim 5"],
        criteria=["16GB RAM", "Budget <= ₹1,20,000"],
        option_comparisons=[
            OptionComparison(
                option_name="Lenovo Legion Slim 5",
                price="₹1,15,000",
                attributes={"RAM": "16GB", "price": "₹1,15,000"},
                requirement_alignment=[
                    OptionRequirementMatch(
                        requirement="16GB RAM",
                        status="satisfies",
                        explanation="RAM (16GB) meets 16GB requirement.",
                        supporting_evidence=["16GB DDR5 RAM"],
                        source_urls=["https://lenovo.com/slim5"]
                    )
                ],
                known_tradeoffs=["Price is ₹1,15,000."],
                uncertainties=["Lenovo Legion Slim 5: Battery life (Unknown)"],
                source_references=[{"title": "Lenovo Legion Slim 5 Specs", "url": "https://lenovo.com/slim5"}]
            )
        ],
        trade_offs=["Price vs RAM capacity"],
        uncertainties=["Lenovo Legion Slim 5: Battery life (Unknown)"],
        conflicts_considered=["Lenovo Legion Slim 5 - RAM: Official source confirms 16GB."]
    )

@pytest.mark.asyncio
async def test_basic_report_generation(sample_plan, sample_results, sample_claims, sample_comparison):
    generator = FinalReportGenerator()
    report = await generator.generate_report(
        plan=sample_plan,
        results=sample_results,
        claims=sample_claims,
        conflicts=[],
        comparison=sample_comparison
    )

    assert isinstance(report, FinalDecisionReport)
    assert "Decision Support Report" in report.title
    assert len(report.summary) > 0

@pytest.mark.asyncio
async def test_requirements_included(sample_plan, sample_comparison):
    generator = FinalReportGenerator()
    report = await generator.generate_report(plan=sample_plan, comparison=sample_comparison)

    assert len(report.user_requirements) >= 2
    assert any("16GB RAM" in req for req in report.user_requirements)

@pytest.mark.asyncio
async def test_multiple_options(sample_plan, sample_comparison):
    sample_comparison.compared_options.append("ASUS ROG Zephyrus G14")
    sample_comparison.option_comparisons.append(
        OptionComparison(
            option_name="ASUS ROG Zephyrus G14",
            price="₹1,18,000",
            attributes={"RAM": "16GB"},
            requirement_alignment=[],
            source_references=[{"title": "ASUS G14", "url": "https://asus.com/g14"}]
        )
    )

    generator = FinalReportGenerator()
    report = await generator.generate_report(plan=sample_plan, comparison=sample_comparison)

    assert len(report.options) == 2
    opt_names = [o.name for o in report.options]
    assert "Lenovo Legion Slim 5" in opt_names
    assert "ASUS ROG Zephyrus G14" in opt_names

@pytest.mark.asyncio
async def test_evidence_included(sample_plan, sample_results, sample_claims, sample_comparison):
    generator = FinalReportGenerator()
    report = await generator.generate_report(
        plan=sample_plan,
        results=sample_results,
        claims=sample_claims,
        comparison=sample_comparison
    )

    assert len(report.key_findings) > 0
    assert len(report.source_references) > 0

@pytest.mark.asyncio
async def test_conflicts_included(sample_plan, sample_claims, sample_conflict, sample_comparison):
    generator = FinalReportGenerator()
    report = await generator.generate_report(
        plan=sample_plan,
        claims=sample_claims,
        conflicts=[sample_conflict],
        comparison=sample_comparison
    )

    assert len(report.conflicts) == 1
    assert report.conflicts[0].attribute == "RAM"
    assert any("SKU" in v or "specification" in v.lower() for v in report.verification_items)

@pytest.mark.asyncio
async def test_trade_offs_included(sample_plan, sample_comparison):
    generator = FinalReportGenerator()
    report = await generator.generate_report(plan=sample_plan, comparison=sample_comparison)

    assert len(report.trade_offs) > 0
    assert "Price vs RAM capacity" in report.trade_offs

@pytest.mark.asyncio
async def test_unknown_information_preserved(sample_plan, sample_comparison):
    generator = FinalReportGenerator()
    report = await generator.generate_report(plan=sample_plan, comparison=sample_comparison)

    assert len(report.uncertainties) > 0
    assert any("Battery life" in u for u in report.uncertainties)

@pytest.mark.asyncio
async def test_verification_items_generated(sample_plan, sample_comparison):
    generator = FinalReportGenerator()
    report = await generator.generate_report(plan=sample_plan, comparison=sample_comparison)

    assert len(report.verification_items) >= 2
    assert any("pricing" in v.lower() for v in report.verification_items)

@pytest.mark.asyncio
async def test_source_urls_preserved_and_no_invented_urls(sample_plan, sample_claims, sample_comparison):
    generator = FinalReportGenerator()
    report = await generator.generate_report(
        plan=sample_plan,
        claims=sample_claims,
        comparison=sample_comparison
    )

    urls = [s["url"] for s in report.source_references]
    assert "https://lenovo.com/slim5" in urls
    for u in urls:
        assert u.startswith("http")

@pytest.mark.asyncio
async def test_no_unsupported_claims_or_commanding_language(sample_plan, sample_comparison):
    generator = FinalReportGenerator()
    report = await generator.generate_report(plan=sample_plan, comparison=sample_comparison)

    # Must NOT contain commanding absolute statements like "Buy Laptop A. It is objectively the best."
    assert "objectively the best" not in report.summary.lower()
    assert "buy laptop" not in report.summary.lower()

@pytest.mark.asyncio
async def test_empty_evidence(sample_plan):
    generator = FinalReportGenerator()
    report = await generator.generate_report(plan=sample_plan, claims=[], results=[], comparison=None)

    assert report.options == []
    assert "No conclusive candidate options" in report.summary

@pytest.mark.asyncio
async def test_empty_conflicts(sample_plan, sample_comparison):
    generator = FinalReportGenerator()
    report = await generator.generate_report(plan=sample_plan, conflicts=[], comparison=sample_comparison)

    assert report.conflicts == []

@pytest.mark.asyncio
async def test_multiple_conflicts(sample_plan, sample_conflict, sample_comparison):
    conf2 = sample_conflict.model_copy(update={"conflict_id": "conf_2", "attribute": "GPU"})
    generator = FinalReportGenerator()
    report = await generator.generate_report(
        plan=sample_plan,
        conflicts=[sample_conflict, conf2],
        comparison=sample_comparison
    )

    assert len(report.conflicts) == 2

@pytest.mark.asyncio
async def test_pydantic_validation(sample_plan, sample_comparison):
    generator = FinalReportGenerator()
    report = await generator.generate_report(plan=sample_plan, comparison=sample_comparison)

    assert isinstance(report, FinalDecisionReport)
    assert report.title.startswith("Decision Support Report")

@pytest.mark.asyncio
async def test_llm_unconfigured_fallback(sample_plan, sample_comparison):
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.is_configured = False

    generator = FinalReportGenerator(llm_service=mock_llm)
    report = await generator.generate_report(plan=sample_plan, comparison=sample_comparison)

    assert isinstance(report, FinalDecisionReport)
    assert len(report.summary) > 0
