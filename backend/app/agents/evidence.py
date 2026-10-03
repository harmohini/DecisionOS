"""
Evidence Agent: Analyzes ResearchResult items to extract traceable factual claims,
classifies source quality, calculates transparent confidence scores, and maintains
strict provenance back to original source URLs.
"""

import re
import uuid
import urllib.parse
from typing import List, Optional, Dict, Any, Set
from datetime import datetime

from app.models.schemas import (
    ResearchResult,
    EvidenceClaim,
    ExtractedClaimItem,
    ExtractedClaimList
)
from app.services.llm import LLMService, LLMNotConfiguredError, LLMError

# Known manufacturer domain signatures
OFFICIAL_DOMAINS = {
    "lenovo.com", "asus.com", "apple.com", "dell.com", "hp.com", "sony.com",
    "samsung.com", "bose.com", "microsoft.com", "acer.com", "msi.com", "razer.com"
}

RETAILER_DOMAINS = {
    "amazon.com", "amazon.in", "flipkart.com", "bestbuy.com", "walmart.com",
    "ebay.com", "newegg.com", "croma.com", "reliance-digital.in"
}

REVIEW_DOMAINS = {
    "tomsguide.com", "notebookcheck.net", "rtings.com", "theverge.com",
    "cnet.com", "gsmarena.com", "techradar.com", "wirecutter.com", "digitaltrends.com"
}

NEWS_DOMAINS = {
    "techcrunch.com", "wsj.com", "bbc.com", "reuters.com", "bloomberg.com", "nytimes.com"
}

FORUM_DOMAINS = {
    "reddit.com", "quora.com", "forums.lenovo.com", "linustechtips.com"
}

def classify_source(
    url: str,
    source_name: Optional[str] = None,
    title: Optional[str] = None,
    result_source_type: Optional[str] = None
) -> str:
    """
    Classifies a source URL/metadata into standard source_type categories.
    Categories: official, retailer, review, video, forum, news, general_web, unknown
    """
    if not url:
        return "unknown"

    url_lower = url.lower()
    source_lower = (source_name or "").lower()
    title_lower = (title or "").lower()

    if result_source_type == "youtube" or "youtube.com" in url_lower or "vimeo.com" in url_lower:
        return "video"

    try:
        netloc = urllib.parse.urlparse(url_lower).netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
    except Exception:
        netloc = ""

    if result_source_type == "shopping" or any(ret in netloc for ret in RETAILER_DOMAINS) or "store." in url_lower:
        return "retailer"

    if any(off in netloc for off in OFFICIAL_DOMAINS):
        return "official"

    if any(rev in netloc for rev in REVIEW_DOMAINS) or "review" in url_lower or "review" in title_lower:
        return "review"

    if any(n in netloc for n in NEWS_DOMAINS) or "news" in netloc:
        return "news"

    if any(f in netloc for f in FORUM_DOMAINS) or "forum" in url_lower or "discussions" in url_lower:
        return "forum"

    return "general_web"

def calculate_confidence(
    value: str,
    evidence_text: str,
    source_type: str,
    has_exact_num: bool = False
) -> str:
    """
    Calculates transparent confidence score: HIGH, MEDIUM, LOW, or UNKNOWN.
    """
    if not value or not evidence_text:
        return "UNKNOWN"

    val_lower = value.lower()
    is_qualitative = any(w in val_lower for w in ["described as", "good", "excellent", "decent", "approximate", "great"])

    # Regex check for numeric or explicit spec in value (e.g. 16GB, RTX 4060, ₹1,20,000, 7 hours)
    has_specs = bool(re.search(r'\d+|(?:gb|mb|tb|rtx|gtx|ghz|mah|inr|usd|₹|\$)', val_lower)) or has_exact_num

    if is_qualitative and not has_specs:
        if source_type in ["forum", "general_web"]:
            return "LOW"
        return "MEDIUM"

    if has_specs and source_type in ["official", "retailer", "review", "video", "news"]:
        return "HIGH"

    if has_specs and source_type in ["forum", "general_web"]:
        return "MEDIUM"

    return "MEDIUM"

class EvidenceExtractor:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or LLMService()

    async def extract_evidence(self, results: List[ResearchResult]) -> List[EvidenceClaim]:
        """
        Extracts verifiable factual claims from research results.
        Enforces source URL provenance and classifies confidence & source type.
        """
        if not results:
            return []

        all_claims: List[EvidenceClaim] = []
        seen_claim_keys: Set[str] = set()

        for item in results:
            if not item.url:
                continue

            extracted_items: List[ExtractedClaimItem] = []

            # 1. Deterministic Rule-Based Extraction (Prices, RAM, GPU, Battery from snippet/title/item fields)
            rule_claims = self._rule_based_extract(item)
            extracted_items.extend(rule_claims)

            # 2. LLM Extraction if available
            if self.llm_service.is_configured and item.snippet:
                try:
                    llm_claims = await self._llm_extract(item)
                    extracted_items.extend(llm_claims)
                except Exception:
                    # Fallback cleanly to rule-based claims if LLM fails
                    pass

            source_cat = classify_source(
                url=item.url,
                source_name=item.query,
                title=item.title,
                result_source_type=item.source_type
            )

            # 3. Construct and validate EvidenceClaim objects
            for ext in extracted_items:
                if not ext.entity or not ext.attribute or not ext.value or not ext.evidence_text:
                    continue

                # Deduplication key: entity + attribute + value + url
                dedup_key = f"{ext.entity.lower().strip()}|{ext.attribute.lower().strip()}|{ext.value.lower().strip()}|{item.url}"
                if dedup_key in seen_claim_keys:
                    continue
                seen_claim_keys.add(dedup_key)

                conf_level = calculate_confidence(
                    value=ext.value,
                    evidence_text=ext.evidence_text,
                    source_type=source_cat
                )

                claim_obj = EvidenceClaim(
                    claim_id=f"claim_{uuid.uuid4().hex[:10]}",
                    entity=ext.entity.strip(),
                    attribute=ext.attribute.strip(),
                    value=ext.value.strip(),
                    source_url=item.url,  # Strict provenance preservation
                    source_title=item.title,
                    source_type=source_cat,
                    evidence_text=ext.evidence_text.strip(),
                    confidence=conf_level,
                    supporting_result_id=item.result_id
                )
                all_claims.append(claim_obj)

        return all_claims

    def _rule_based_extract(self, item: ResearchResult) -> List[ExtractedClaimItem]:
        """
        Deterministic rule-based extraction for price, RAM, GPU, and battery specs.
        """
        items: List[ExtractedClaimItem] = []
        text = f"{item.title or ''} {item.snippet or ''}".strip()
        entity = item.product_name or self._guess_entity(item.title)

        # Price claim
        if item.price:
            items.append(ExtractedClaimItem(
                entity=entity,
                attribute="price",
                value=item.price,
                evidence_text=f"Price listed as {item.price} in search results."
            ))

        # RAM regex
        ram_match = re.search(r'(\d+\s*GB)\s*(?:RAM|DDR\d|Memory)', text, re.IGNORECASE)
        if ram_match:
            items.append(ExtractedClaimItem(
                entity=entity,
                attribute="RAM",
                value=ram_match.group(1).replace(" ", ""),
                evidence_text=ram_match.group(0)
            ))

        # GPU regex
        gpu_match = re.search(r'(RTX\s*\d{4}|GTX\s*\d{4}|Radeon\s*\w+|Apple\s*M\d\s*GPU)', text, re.IGNORECASE)
        if gpu_match:
            items.append(ExtractedClaimItem(
                entity=entity,
                attribute="GPU",
                value=gpu_match.group(1),
                evidence_text=gpu_match.group(0)
            ))

        # Battery qualitative / quantitative regex
        batt_num = re.search(r'(\d+(?:\.\d+)?)\s*(?:hours|hrs)\s*(?:of)?\s*battery', text, re.IGNORECASE)
        if batt_num:
            items.append(ExtractedClaimItem(
                entity=entity,
                attribute="battery life",
                value=f"{batt_num.group(1)} hours",
                evidence_text=batt_num.group(0)
            ))
        elif re.search(r'(?:excellent|good|great|decent|long)\s*battery', text, re.IGNORECASE):
            items.append(ExtractedClaimItem(
                entity=entity,
                attribute="battery life",
                value="described as excellent",
                evidence_text="Review mentions battery performance."
            ))

        return items

    async def _llm_extract(self, item: ResearchResult) -> List[ExtractedClaimItem]:
        prompt = (
            f"Extract verifiable factual claims from this search result.\n"
            f"Title: {item.title}\n"
            f"Snippet: {item.snippet}\n\n"
            f"Rules:\n"
            f"1. Do NOT invent specifications or numbers. If battery life is vague (e.g. 'great battery'), set value='described as excellent'.\n"
            f"2. Extract entity (product/hotel name), attribute (e.g. RAM, price, battery life), value, and verbatim evidence_text from snippet."
        )

        sys_prompt = (
            "You are the Evidence Agent for DecisionOS. Extract structured claims strictly grounded in the provided text.\n"
            "Return ONLY JSON matching ExtractedClaimList schema."
        )

        res = await self.llm_service.generate_structured_output(
            prompt=prompt,
            response_model=ExtractedClaimList,
            system_prompt=sys_prompt
        )
        return res.claims if res and res.claims else []

    def _guess_entity(self, title: str) -> str:
        if not title:
            return "Unknown Product"
        # Take first 4-5 words of title before hyphens or colons
        clean_title = title.split("-")[0].split("|")[0].split(":")[0].strip()
        words = clean_title.split()
        return " ".join(words[:5]) if words else "Unknown Product"
