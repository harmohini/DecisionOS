"""
Final Report Agent: Receives ResearchPlan, ResearchResults, EvidenceClaims, DetectedConflicts,
and ComparisonResult to compile a concise, evidence-backed, traceable FinalDecisionReport.
Does NOT present absolute AI commands; supports human decision-making with transparent trade-offs.
"""

from typing import List, Optional, Dict, Any, Set
from datetime import datetime

from app.models.schemas import (
    ResearchPlan,
    ResearchResult,
    EvidenceClaim,
    DetectedConflict,
    ComparisonResult,
    ReportOptionItem,
    FinalDecisionReport
)
from app.services.llm import LLMService

class FinalReportGenerator:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or LLMService()

    async def generate_report(
        self,
        plan: Optional[ResearchPlan] = None,
        results: Optional[List[ResearchResult]] = None,
        claims: Optional[List[EvidenceClaim]] = None,
        conflicts: Optional[List[DetectedConflict]] = None,
        comparison: Optional[ComparisonResult] = None
    ) -> FinalDecisionReport:
        """
        Compiles all research pipeline artifacts into a structured FinalDecisionReport.
        """
        results_list = results or []
        claims_list = claims or []
        conflicts_list = conflicts or []

        user_goal = plan.user_goal if plan else "Decision Research"
        user_reqs = list(dict.fromkeys(
            ((plan.hard_constraints if plan else []) or []) + 
            ((plan.preferences if plan else []) or [])
        ))
        if plan and plan.budget:
            user_reqs.append(f"Budget: {plan.budget}")

        # 1. Collect Source References (Strict Provenance Preservation)
        source_refs: List[Dict[str, str]] = []
        seen_urls: Set[str] = set()

        for c in claims_list:
            if c.source_url and c.source_url not in seen_urls:
                seen_urls.add(c.source_url)
                source_refs.append({
                    "title": c.source_title or c.source_url,
                    "url": c.source_url
                })

        for r in results_list:
            if r.url and r.url not in seen_urls:
                seen_urls.add(r.url)
                source_refs.append({
                    "title": r.title or r.url,
                    "url": r.url
                })

        # 2. Build ReportOptionItem list
        report_options: List[ReportOptionItem] = []
        if comparison and comparison.option_comparisons:
            for opt in comparison.option_comparisons:
                strengths = [
                    m.explanation for m in opt.requirement_alignment 
                    if m.status in ["satisfies", "partially_satisfies"]
                ]
                report_options.append(
                    ReportOptionItem(
                        name=opt.option_name,
                        requirement_alignment=opt.requirement_alignment,
                        strengths=strengths,
                        tradeoffs=opt.known_tradeoffs,
                        uncertainties=opt.uncertainties,
                        evidence_references=opt.source_references
                    )
                )

        # 3. Generate Key Findings
        key_findings: List[str] = []
        if report_options:
            for opt in report_options:
                if opt.strengths:
                    key_findings.append(f"{opt.name} fulfills key requirements: {', '.join(opt.strengths[:2])}.")
        elif claims_list:
            top_claims = claims_list[:3]
            for c in top_claims:
                key_findings.append(f"{c.entity}: {c.attribute} reported as {c.value} ({c.source_type} source).")

        # 4. Generate Verification Items ("Before You Decide")
        verification_items: List[str] = [
            "Confirm current live pricing and promotional discounts with the seller.",
            "Verify seller warranty, return terms, and delivery availability."
        ]
        if conflicts_list:
            verification_items.append("Verify exact product SKU / hardware configuration sheet to resolve reported specification differences.")
        if comparison and comparison.uncertainties:
            verification_items.append("Check specific unverified attributes directly on official documentation before purchasing.")

        # 5. Build Decision Summary
        summary_text = self._build_summary(plan, comparison, report_options, conflicts_list)

        return FinalDecisionReport(
            title=f"Decision Support Report: {user_goal}",
            summary=summary_text,
            user_requirements=user_reqs,
            options=report_options,
            key_findings=key_findings,
            trade_offs=comparison.trade_offs if comparison else [],
            conflicts=conflicts_list,
            uncertainties=comparison.uncertainties if comparison else [],
            verification_items=list(dict.fromkeys(verification_items)),
            source_references=source_refs,
            generated_at=datetime.utcnow()
        )

    def _build_summary(
        self,
        plan: Optional[ResearchPlan],
        comparison: Optional[ComparisonResult],
        options: List[ReportOptionItem],
        conflicts: List[DetectedConflict]
    ) -> str:
        if not options:
            return "Research completed. No conclusive candidate options were identified from the available search evidence."

        opt_names = [o.name for o in options]
        aligned_opts = [o.name for o in options if any(m.status == "satisfies" for m in o.requirement_alignment)]

        if len(options) == 1:
            return (
                f"Based on available web evidence, {opt_names[0]} aligns with your research goal. "
                f"Please review known trade-offs and verification items before finalizing your decision."
            )

        if aligned_opts:
            return (
                f"The research evaluated candidate options ({', '.join(opt_names)}). "
                f"Options ({', '.join(aligned_opts)}) align with your primary requirements based on verified evidence. "
                f"Compare specific trade-offs, pricing, and uncertainties detailed below."
            )

        return (
            f"Evaluated {len(options)} options ({', '.join(opt_names)}). "
            f"Review requirement alignments and verification items to select the option best matching your priorities."
        )
