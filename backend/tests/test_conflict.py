import pytest
from unittest.mock import MagicMock
from app.models.schemas import EvidenceClaim, DetectedConflict
from app.agents.conflict import ConflictDetector, normalize_entity, normalize_attribute
from app.services.llm import LLMService

@pytest.fixture
def base_claim():
    return EvidenceClaim(
        claim_id="c1",
        entity="Lenovo Legion Slim 5",
        attribute="RAM",
        value="16GB",
        source_url="https://www.lenovo.com/official",
        source_type="official",
        evidence_text="16GB DDR5 RAM",
        confidence="HIGH"
    )

@pytest.mark.asyncio
async def test_no_conflicting_claims(base_claim):
    detector = ConflictDetector()
    # Identical or matching claims -> no conflict
    claim2 = base_claim.model_copy(update={"claim_id": "c2", "source_url": "https://review.org"})
    
    conflicts = await detector.detect_conflicts([base_claim, claim2])
    assert conflicts == []

@pytest.mark.asyncio
async def test_two_different_ram_values(base_claim):
    detector = ConflictDetector()
    c2 = EvidenceClaim(
        claim_id="c2",
        entity="Lenovo Legion Slim 5",
        attribute="RAM",
        value="32GB",
        source_url="https://retailer-store.com/item",
        source_type="retailer",
        evidence_text="32GB DDR5 RAM",
        confidence="HIGH"
    )

    conflicts = await detector.detect_conflicts([base_claim, c2])

    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.attribute == "RAM"
    assert "16GB" in conflict.conflicting_values
    assert "32GB" in conflict.conflicting_values
    assert conflict.resolution_status in ["resolved", "insufficient_evidence"]
    assert len(conflict.supporting_claims) == 2

@pytest.mark.asyncio
async def test_different_gpu_values():
    detector = ConflictDetector()
    c1 = EvidenceClaim(
        claim_id="c1",
        entity="ASUS ROG Zephyrus G14",
        attribute="GPU",
        value="RTX 4060",
        source_url="https://asus.com/official",
        source_type="official",
        evidence_text="NVIDIA GeForce RTX 4060"
    )
    c2 = EvidenceClaim(
        claim_id="c2",
        entity="ASUS ROG Zephyrus G14",
        attribute="GPU",
        value="RTX 4070",
        source_url="https://retailer.com/g14",
        source_type="retailer",
        evidence_text="NVIDIA GeForce RTX 4070"
    )

    conflicts = await detector.detect_conflicts([c1, c2])

    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.attribute == "GPU"
    assert "RTX 4060" in conflict.conflicting_values
    assert "RTX 4070" in conflict.conflicting_values

@pytest.mark.asyncio
async def test_different_cpu_values():
    detector = ConflictDetector()
    c1 = EvidenceClaim(
        claim_id="c1",
        entity="Dell XPS 15",
        attribute="CPU",
        value="Intel Core i7",
        source_url="https://dell.com/xps15",
        source_type="official",
        evidence_text="Intel Core i7 Processor"
    )
    c2 = EvidenceClaim(
        claim_id="c2",
        entity="Dell XPS 15",
        attribute="CPU",
        value="AMD Ryzen 7",
        source_url="https://retailer.com/xps15",
        source_type="retailer",
        evidence_text="AMD Ryzen 7 Processor"
    )

    conflicts = await detector.detect_conflicts([c1, c2])

    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.attribute == "CPU"
    assert "Intel Core i7" in conflict.conflicting_values
    assert "AMD Ryzen 7" in conflict.conflicting_values

@pytest.mark.asyncio
async def test_price_differences_are_not_spec_conflicts():
    detector = ConflictDetector()
    c1 = EvidenceClaim(
        claim_id="c1",
        entity="Lenovo Legion Slim 5",
        attribute="price",
        value="₹99,999",
        source_url="https://amazon.in/legion",
        source_type="retailer",
        evidence_text="Price ₹99,999"
    )
    c2 = EvidenceClaim(
        claim_id="c2",
        entity="Lenovo Legion Slim 5",
        attribute="price",
        value="₹1,09,999",
        source_url="https://flipkart.com/legion",
        source_type="retailer",
        evidence_text="Price ₹1,09,999"
    )

    conflicts = await detector.detect_conflicts([c1, c2])

    assert len(conflicts) == 1
    conflict = conflicts[0]
    # Price variation is normal market behavior, resolution_status is no_conflict
    assert conflict.resolution_status == "no_conflict"
    assert conflict.severity == "low"
    assert "Price variation" in conflict.explanation

@pytest.mark.asyncio
async def test_different_product_variants_insufficient_evidence():
    detector = ConflictDetector()
    # Two retailer listings reporting 16GB vs 32GB without official tie-breaker -> variant likelihood
    c1 = EvidenceClaim(
        claim_id="c1",
        entity="Laptop X",
        attribute="RAM",
        value="16GB",
        source_url="https://retailerA.com/item",
        source_type="retailer",
        evidence_text="16GB RAM model"
    )
    c2 = EvidenceClaim(
        claim_id="c2",
        entity="Laptop X",
        attribute="RAM",
        value="32GB",
        source_url="https://retailerB.com/item",
        source_type="retailer",
        evidence_text="32GB RAM model"
    )

    conflicts = await detector.detect_conflicts([c1, c2])

    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.resolution_status == "insufficient_evidence"
    assert "configurations or SKUs" in conflict.explanation

@pytest.mark.asyncio
async def test_multiple_sources_agreeing(base_claim):
    detector = ConflictDetector()
    # Official (16GB) + Review (16GB) vs Retailer (32GB)
    c_review = EvidenceClaim(
        claim_id="c_rev",
        entity="Lenovo Legion Slim 5",
        attribute="RAM",
        value="16GB",
        source_url="https://notebookcheck.net/review",
        source_type="review",
        evidence_text="16GB RAM tested"
    )
    c_ret = EvidenceClaim(
        claim_id="c_ret",
        entity="Lenovo Legion Slim 5",
        attribute="RAM",
        value="32GB",
        source_url="https://retailer.com/item",
        source_type="retailer",
        evidence_text="32GB RAM listing"
    )

    conflicts = await detector.detect_conflicts([base_claim, c_review, c_ret])

    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.resolution_status == "resolved"
    assert "16GB" in conflict.explanation

@pytest.mark.asyncio
async def test_official_source_vs_retailer_disagreement(base_claim):
    detector = ConflictDetector()
    c_retailer = EvidenceClaim(
        claim_id="c_ret",
        entity="Lenovo Legion Slim 5",
        attribute="RAM",
        value="32GB",
        source_url="https://random-store.com/item",
        source_type="retailer",
        evidence_text="32GB listing"
    )

    conflicts = await detector.detect_conflicts([base_claim, c_retailer])

    assert len(conflicts) == 1
    conflict = conflicts[0]
    # Official source authority favors 16GB
    assert conflict.resolution_status == "resolved"
    assert "favors '16GB'" in conflict.explanation

@pytest.mark.asyncio
async def test_review_vs_manufacturer_disagreement():
    detector = ConflictDetector()
    c_mfr = EvidenceClaim(
        claim_id="c1",
        entity="Gadget Z",
        attribute="battery life",
        value="10 hours",
        source_url="https://mfr.com/specs",
        source_type="official",
        evidence_text="Up to 10 hours battery"
    )
    c_rev = EvidenceClaim(
        claim_id="c2",
        entity="Gadget Z",
        attribute="battery life",
        value="6 hours",
        source_url="https://tech-review.org/test",
        source_type="review",
        evidence_text="Real world test measured 6 hours"
    )

    conflicts = await detector.detect_conflicts([c_mfr, c_rev])

    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert "10 hours" in conflict.conflicting_values
    assert "6 hours" in conflict.conflicting_values

@pytest.mark.asyncio
async def test_insufficient_evidence():
    detector = ConflictDetector()
    c1 = EvidenceClaim(
        claim_id="c1",
        entity="Product Y",
        attribute="screen refresh rate",
        value="120Hz",
        source_url="https://forum.org/post1",
        source_type="forum",
        evidence_text="Post says 120Hz"
    )
    c2 = EvidenceClaim(
        claim_id="c2",
        entity="Product Y",
        attribute="screen refresh rate",
        value="165Hz",
        source_url="https://blog.org/post2",
        source_type="general_web",
        evidence_text="Blog says 165Hz"
    )

    conflicts = await detector.detect_conflicts([c1, c2])

    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.resolution_status in ["insufficient_evidence", "unresolved"]

@pytest.mark.asyncio
async def test_empty_claim_list():
    detector = ConflictDetector()
    conflicts = await detector.detect_conflicts([])
    assert conflicts == []

@pytest.mark.asyncio
async def test_duplicate_claims(base_claim):
    detector = ConflictDetector()
    # Passing identical claims -> no conflict
    conflicts = await detector.detect_conflicts([base_claim, base_claim])
    assert conflicts == []

def test_entity_normalization():
    assert normalize_entity("Lenovo Legion Slim 5 Laptop Review") == "lenovo legion slim 5"
    assert normalize_entity("ASUS ROG Zephyrus G14 Notebook Specs") == "asus rog zephyrus g14"

def test_attribute_normalization():
    assert normalize_attribute("Memory") == "ram"
    assert normalize_attribute("Graphics Card") == "gpu"
    assert normalize_attribute("Cost") == "price"

@pytest.mark.asyncio
async def test_provenance_preservation(base_claim):
    detector = ConflictDetector()
    c2 = EvidenceClaim(
        claim_id="c2",
        entity="Lenovo Legion Slim 5",
        attribute="RAM",
        value="32GB",
        source_url="https://retailer-store.com/item",
        source_type="retailer",
        evidence_text="32GB DDR5 RAM"
    )

    conflicts = await detector.detect_conflicts([base_claim, c2])

    conflict = conflicts[0]
    urls = [c.source_url for c in conflict.supporting_claims]
    assert "https://www.lenovo.com/official" in urls
    assert "https://retailer-store.com/item" in urls

@pytest.mark.asyncio
async def test_conflict_explanation_and_resolution_status(base_claim):
    detector = ConflictDetector()
    c2 = EvidenceClaim(
        claim_id="c2",
        entity="Lenovo Legion Slim 5",
        attribute="RAM",
        value="32GB",
        source_url="https://retailer-store.com/item",
        source_type="retailer",
        evidence_text="32GB DDR5 RAM"
    )

    conflicts = await detector.detect_conflicts([base_claim, c2])

    conflict = conflicts[0]
    assert len(conflict.explanation) > 0
    assert len(conflict.recommended_verification) > 0
    assert conflict.resolution_status in ["no_conflict", "resolved", "unresolved", "insufficient_evidence"]
