"""
Conflict Detection Agent: Groups EvidenceClaim objects by normalized entity and attribute,
deterministically detects contradictory claims, evaluates source hierarchy (official > review > forum),
identifies configuration/variant dependencies, and produces traceable DetectedConflict reports.
"""

import re
import uuid
from typing import List, Optional, Dict, Set, Tuple
from datetime import datetime

from app.models.schemas import EvidenceClaim, DetectedConflict
from app.services.llm import LLMService

# Source quality weight map for resolution heuristics
SOURCE_WEIGHTS = {
    "official": 4,
    "review": 3,
    "retailer": 2,
    "news": 2,
    "video": 2,
    "forum": 1,
    "general_web": 1,
    "unknown": 0
}

ATTRIBUTE_ALIASES = {
    "memory": "ram",
    "ram memory": "ram",
    "system memory": "ram",
    "graphics": "gpu",
    "graphics card": "gpu",
    "gpu model": "gpu",
    "processor": "cpu",
    "cpu model": "cpu",
    "cost": "price",
    "price tag": "price",
    "msrp": "price",
    "battery": "battery life",
    "battery life hours": "battery life"
}

def normalize_entity(entity: str) -> str:
    if not entity:
        return "unknown"
    clean = entity.lower().strip()
    # Remove noise terms
    for noise in ["laptop", "notebook", "review", "official", "specs", "specifications", "model"]:
        clean = re.sub(rf'\b{noise}\b', '', clean)
    clean = re.sub(r'[^\w\s]', '', clean)
    return " ".join(clean.split()) or entity.lower().strip()

def normalize_attribute(attr: str) -> str:
    if not attr:
        return "unknown"
    clean = attr.lower().strip()
    clean = re.sub(r'[^\w\s]', '', clean)
    clean = " ".join(clean.split())
    return ATTRIBUTE_ALIASES.get(clean, clean)

def normalize_value(val: str) -> str:
    if not val:
        return ""
    clean = val.strip().lower()
    # Normalize RAM strings like "16 gb" -> "16gb"
    clean = re.sub(r'(\d+)\s*gb', r'\1gb', clean)
    return clean

class ConflictDetector:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or LLMService()

    async def detect_conflicts(self, claims: List[EvidenceClaim]) -> List[DetectedConflict]:
        """
        Scans EvidenceClaim items for contradictory specifications or values on the same entity.
        Returns a list of DetectedConflict objects with full source provenance.
        """
        if not claims:
            return []

        # 1. Group claims by (normalized_entity, normalized_attribute)
        grouped_claims: Dict[Tuple[str, str], List[EvidenceClaim]] = {}

        for claim in claims:
            if not claim.entity or not claim.attribute or not claim.value or not claim.source_url:
                continue

            norm_ent = normalize_entity(claim.entity)
            norm_attr = normalize_attribute(claim.attribute)
            key = (norm_ent, norm_attr)

            if key not in grouped_claims:
                grouped_claims[key] = []
            grouped_claims[key].append(claim)

        conflicts: List[DetectedConflict] = []

        # 2. Analyze each entity-attribute group for conflicts
        for (norm_ent, norm_attr), group_claims in grouped_claims.items():
            # Extract unique values
            value_map: Dict[str, List[EvidenceClaim]] = {}
            for c in group_claims:
                n_val = normalize_value(c.value)
                if n_val not in value_map:
                    value_map[n_val] = []
                value_map[n_val].append(c)

            unique_values = list(value_map.keys())

            # Display original raw values in conflicting_values list
            display_values = list(dict.fromkeys(c.value for c in group_claims))

            display_entity = group_claims[0].entity
            display_attr = group_claims[0].attribute

            # Case A: Only 1 unique value -> No conflict
            if len(unique_values) <= 1:
                continue

            # Case B: Price attribute variation -> Normal market behavior (not a spec contradiction)
            if norm_attr == "price":
                conflicts.append(
                    DetectedConflict(
                        conflict_id=f"conflict_{uuid.uuid4().hex[:10]}",
                        entity=display_entity,
                        attribute=display_attr,
                        conflicting_values=display_values,
                        supporting_claims=group_claims,
                        severity="low",
                        resolution_status="no_conflict",
                        explanation=f"Price variation across different merchants or listing dates ({', '.join(display_values)}) is normal market behavior.",
                        recommended_verification="Check seller website for current pricing and discounts."
                    )
                )
                continue

            # Case C: Material spec difference (e.g. RAM 16GB vs 32GB, GPU RTX 4060 vs RTX 4070)
            # Evaluate source weights and configuration likelihood
            conflict_obj = self._resolve_spec_conflict(
                entity=display_entity,
                attribute=display_attr,
                norm_attr=norm_attr,
                display_values=display_values,
                value_map=value_map,
                group_claims=group_claims
            )
            conflicts.append(conflict_obj)

        return conflicts

    def _resolve_spec_conflict(
        self,
        entity: str,
        attribute: str,
        norm_attr: str,
        display_values: List[str],
        value_map: Dict[str, List[EvidenceClaim]],
        group_claims: List[EvidenceClaim]
    ) -> DetectedConflict:
        """
        Determines severity, resolution_status, and explanation for spec conflicts.
        """
        # Calculate source weight totals for each value
        value_scores: Dict[str, int] = {}
        value_source_types: Dict[str, Set[str]] = {}

        for val_key, claim_list in value_map.items():
            score = sum(SOURCE_WEIGHTS.get(c.source_type, 1) for c in claim_list)
            value_scores[val_key] = score
            value_source_types[val_key] = {c.source_type for c in claim_list}

        # Check if values indicate different product configurations/variants
        # e.g., 16GB vs 32GB RAM options on laptops are frequently SKU variants
        is_variant_likely = norm_attr in ["ram", "storage", "ssd", "gpu", "cpu"] and len(display_values) == 2

        sorted_values = sorted(value_scores.keys(), key=lambda v: value_scores[v], reverse=True)
        top_val = sorted_values[0]
        second_val = sorted_values[1]

        top_score = value_scores[top_val]
        second_score = value_scores[second_val]

        top_sources = value_source_types[top_val]
        second_sources = value_source_types[second_val]

        # Scenario 1: Variant / Configuration likelihood
        if is_variant_likely and "official" not in top_sources and "official" not in second_sources:
            return DetectedConflict(
                conflict_id=f"conflict_{uuid.uuid4().hex[:10]}",
                entity=entity,
                attribute=attribute,
                conflicting_values=display_values,
                supporting_claims=group_claims,
                severity="medium",
                resolution_status="insufficient_evidence",
                explanation=f"The reported {attribute} values ({', '.join(display_values)}) may represent different product configurations or SKUs rather than a direct contradiction.",
                recommended_verification="Verify specific SKU/model number with seller or manufacturer before purchasing."
            )

        # Scenario 2: Clear consensus / Official source agreement vs single weak source
        if "official" in top_sources or (top_score >= second_score + 2):
            top_raw = value_map[top_val][0].value
            second_raw = value_map[second_val][0].value
            top_src_names = ", ".join(list(top_sources))
            second_src_names = ", ".join(list(second_sources))

            return DetectedConflict(
                conflict_id=f"conflict_{uuid.uuid4().hex[:10]}",
                entity=entity,
                attribute=attribute,
                conflicting_values=display_values,
                supporting_claims=group_claims,
                severity="medium",
                resolution_status="resolved",
                explanation=f"Resolved: Evidence favors '{top_raw}' ({top_src_names}) over '{second_raw}' ({second_src_names}) based on source authority and agreement.",
                recommended_verification=f"Confirm '{top_raw}' specification on official manufacturer spec sheet."
            )

        # Scenario 3: High severity unresolved disagreement between authoritative sources
        return DetectedConflict(
            conflict_id=f"conflict_{uuid.uuid4().hex[:10]}",
            entity=entity,
            attribute=attribute,
            conflicting_values=display_values,
            supporting_claims=group_claims,
            severity="high",
            resolution_status="unresolved",
            explanation=f"Unresolved conflict: Opposing {attribute} values ({', '.join(display_values)}) reported by authoritative sources without clear configuration resolution.",
            recommended_verification="Direct manufacturer spec sheet verification required before relying on this attribute."
        )
