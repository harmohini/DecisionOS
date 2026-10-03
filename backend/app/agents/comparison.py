"""
Comparison Agent: Evaluates candidate options derived from EvidenceClaims against user requirements
defined in the ResearchPlan, accounts for DetectedConflicts, identifies trade-offs and uncertainties,
and maintains full source URL provenance.
"""

import re
from typing import List, Optional, Dict, Set, Any
from app.models.schemas import (
    ResearchPlan,
    EvidenceClaim,
    DetectedConflict,
    OptionRequirementMatch,
    OptionComparison,
    ComparisonResult
)
from app.services.llm import LLMService

class OptionComparator:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or LLMService()

    async def compare_options(
        self,
        plan: ResearchPlan,
        claims: List[EvidenceClaim],
        conflicts: Optional[List[DetectedConflict]] = None
    ) -> ComparisonResult:
        """
        Main entry point for comparing candidate options against user requirements.
        """
        conflicts_list = conflicts or []
        decision_cat = plan.decision_category if plan else "general_research"

        if not claims or not plan:
            return ComparisonResult(
                decision_category=decision_cat,
                compared_options=[],
                criteria=[],
                option_comparisons=[],
                trade_offs=[],
                uncertainties=["No evidence or research plan provided for comparison."],
                conflicts_considered=[]
            )

        # 1. Group claims by candidate option entity
        option_claims_map: Dict[str, List[EvidenceClaim]] = {}
        for claim in claims:
            if not claim.entity or not claim.source_url:
                continue
            entity_key = claim.entity.strip()
            if entity_key not in option_claims_map:
                option_claims_map[entity_key] = []
            option_claims_map[entity_key].append(claim)

        candidate_options = list(option_claims_map.keys())

        # Compile list of criteria (from plan requirements, constraints, preferences)
        all_criteria = list(dict.fromkeys(
            (plan.hard_constraints or []) + 
            (plan.preferences or []) + 
            (plan.important_attributes or [])
        ))
        if plan.budget:
            all_criteria.append(f"Budget <= {plan.budget}")

        option_comparisons: List[OptionComparison] = []
        global_tradeoffs: List[str] = []
        global_uncertainties: List[str] = []
        conflicts_summary: List[str] = []

        # 2. Build OptionComparison for each candidate option
        for opt_name in candidate_options:
            opt_claims = option_claims_map[opt_name]
            
            # Attributes map
            attributes_dict: Dict[str, str] = {}
            for c in opt_claims:
                if c.attribute and c.value:
                    attributes_dict[c.attribute] = c.value

            opt_price = attributes_dict.get("price") or attributes_dict.get("Price")

            # Collect source references
            src_refs: List[Dict[str, str]] = []
            seen_urls: Set[str] = set()
            for c in opt_claims:
                if c.source_url not in seen_urls:
                    seen_urls.add(c.source_url)
                    src_refs.append({
                        "title": c.source_title or c.source_url,
                        "url": c.source_url
                    })

            # Evaluate requirement alignment
            requirement_matches: List[OptionRequirementMatch] = []
            opt_uncertainties: List[str] = []
            opt_tradeoffs: List[str] = []

            for req in all_criteria:
                match_result = self._evaluate_requirement(
                    option_name=opt_name,
                    requirement=req,
                    claims=opt_claims,
                    conflicts=conflicts_list,
                    budget_limit=plan.budget
                )
                requirement_matches.append(match_result)
                
                if match_result.status == "unknown":
                    opt_uncertainties.append(f"{opt_name}: {req} (Unknown)")
                elif match_result.status == "conflicting":
                    conflicts_summary.append(f"{opt_name} - {req}: {match_result.explanation}")

            # Identify known tradeoffs
            if opt_price and any("budget" in c.lower() for c in all_criteria):
                opt_tradeoffs.append(f"Price listed at {opt_price}.")

            option_comparisons.append(
                OptionComparison(
                    option_name=opt_name,
                    price=opt_price,
                    attributes=attributes_dict,
                    requirement_alignment=requirement_matches,
                    known_tradeoffs=opt_tradeoffs,
                    uncertainties=opt_uncertainties,
                    source_references=src_refs
                )
            )
            global_uncertainties.extend(opt_uncertainties)

        # Build trade-offs summary across options
        if len(option_comparisons) >= 2:
            global_tradeoffs.append(
                f"Comparing {len(option_comparisons)} options ({', '.join(candidate_options)}): "
                f"Options differ in pricing, hardware configurations, and review confidence."
            )

        return ComparisonResult(
            decision_category=decision_cat,
            compared_options=candidate_options,
            criteria=all_criteria,
            option_comparisons=option_comparisons,
            trade_offs=global_tradeoffs,
            uncertainties=list(dict.fromkeys(global_uncertainties)),
            conflicts_considered=list(dict.fromkeys(conflicts_summary))
        )

    def _evaluate_requirement(
        self,
        option_name: str,
        requirement: str,
        claims: List[EvidenceClaim],
        conflicts: List[DetectedConflict],
        budget_limit: Optional[str]
    ) -> OptionRequirementMatch:
        """
        Evaluates a single requirement against claims and detected conflicts for an option.
        """
        req_lower = requirement.lower()

        # 1. Check if there is an active conflict for this option and requirement
        for conf in conflicts:
            if conf.entity.lower() in option_name.lower() or option_name.lower() in conf.entity.lower():
                if conf.attribute.lower() in req_lower or req_lower in conf.attribute.lower():
                    if conf.resolution_status in ["unresolved", "insufficient_evidence"]:
                        return OptionRequirementMatch(
                            requirement=requirement,
                            status="conflicting",
                            explanation=f"Conflicting information detected: {conf.explanation}",
                            supporting_evidence=[c.evidence_text for c in conf.supporting_claims],
                            source_urls=[c.source_url for c in conf.supporting_claims]
                        )

        # 2. Match claims relevant to this requirement
        matching_claims = [
            c for c in claims 
            if c.attribute.lower() in req_lower or req_lower in c.attribute.lower() or any(w in req_lower for w in c.attribute.lower().split())
        ]

        # 3. Handle Budget Requirement
        if "budget" in req_lower:
            price_claims = [c for c in claims if c.attribute.lower() in ["price", "cost"]]
            if price_claims:
                p_claim = price_claims[0]
                p_num = self._extract_number(p_claim.value)
                b_num = self._extract_number(budget_limit) if budget_limit else None
                
                if p_num and b_num:
                    if p_num <= b_num:
                        return OptionRequirementMatch(
                            requirement=requirement,
                            status="satisfies",
                            explanation=f"Price ({p_claim.value}) is within budget limit ({budget_limit}).",
                            supporting_evidence=[p_claim.evidence_text],
                            source_urls=[p_claim.source_url]
                        )
                    else:
                        return OptionRequirementMatch(
                            requirement=requirement,
                            status="does_not_satisfy",
                            explanation=f"Price ({p_claim.value}) exceeds budget limit ({budget_limit}).",
                            supporting_evidence=[p_claim.evidence_text],
                            source_urls=[p_claim.source_url]
                        )
                return OptionRequirementMatch(
                    requirement=requirement,
                    status="satisfies",
                    explanation=f"Price listed as {p_claim.value}.",
                    supporting_evidence=[p_claim.evidence_text],
                    source_urls=[p_claim.source_url]
                )

        # 4. Handle RAM / Numeric Specs
        if "ram" in req_lower or "gb" in req_lower:
            ram_claims = [c for c in claims if c.attribute.lower() in ["ram", "memory"]]
            if ram_claims:
                r_claim = ram_claims[0]
                r_num = self._extract_number(r_claim.value)
                req_num = self._extract_number(requirement)
                
                if r_num and req_num:
                    if r_num >= req_num:
                        return OptionRequirementMatch(
                            requirement=requirement,
                            status="satisfies",
                            explanation=f"Available RAM ({r_claim.value}) meets or exceeds requirement ({req_num}GB).",
                            supporting_evidence=[r_claim.evidence_text],
                            source_urls=[r_claim.source_url]
                        )
                    else:
                        return OptionRequirementMatch(
                            requirement=requirement,
                            status="does_not_satisfy",
                            explanation=f"Available RAM ({r_claim.value}) is less than required ({req_num}GB).",
                            supporting_evidence=[r_claim.evidence_text],
                            source_urls=[r_claim.source_url]
                        )
                return OptionRequirementMatch(
                    requirement=requirement,
                    status="satisfies",
                    explanation=f"RAM reported as {r_claim.value}.",
                    supporting_evidence=[r_claim.evidence_text],
                    source_urls=[r_claim.source_url]
                )

        # 5. General matching claims
        if matching_claims:
            top_c = matching_claims[0]
            val_lower = top_c.value.lower()
            if "described as" in val_lower or "good" in val_lower or "excellent" in val_lower:
                return OptionRequirementMatch(
                    requirement=requirement,
                    status="partially_satisfies",
                    explanation=f"Evidence indicates '{top_c.value}' performance.",
                    supporting_evidence=[top_c.evidence_text],
                    source_urls=[top_c.source_url]
                )
            return OptionRequirementMatch(
                requirement=requirement,
                status="satisfies",
                explanation=f"Requirement supported by evidence: {top_c.value}.",
                supporting_evidence=[top_c.evidence_text],
                source_urls=[top_c.source_url]
            )

        # 6. Default if no evidence
        return OptionRequirementMatch(
            requirement=requirement,
            status="unknown",
            explanation="No verified evidence available for this requirement in search findings.",
            supporting_evidence=[],
            source_urls=[]
        )

    def _extract_number(self, text: Optional[str]) -> Optional[float]:
        if not text:
            return None
        # Clean currency & commas e.g. "₹1,20,000" -> "120000"
        clean = text.replace(",", "").replace("₹", "").replace("$", "")
        match = re.search(r'\d+(?:\.\d+)?', clean)
        if match:
            try:
                return float(match.group(0))
            except Exception:
                return None
        return None
