"""
DecisionOS Autonomous Pipeline Service: Connects Planner Agent, Research Agent, Evidence Agent, Conflict Agent, Comparison Agent, and Final Report Agent.
"""

from typing import List, Dict, Any, Union, Optional
from app.models.schemas import (
    ResearchRequest,
    ResearchPlan,
    ResearchResult,
    EvidenceClaim,
    DetectedConflict,
    ComparisonResult,
    FinalDecisionReport
)
from app.agents.planner import ResearchPlanner
from app.agents.researcher import InformationResearcher
from app.agents.evidence import EvidenceExtractor
from app.agents.conflict import ConflictDetector
from app.agents.comparison import OptionComparator
from app.agents.report import FinalReportGenerator

class ResearchPipeline:
    def __init__(
        self,
        planner: Optional[ResearchPlanner] = None,
        researcher: Optional[InformationResearcher] = None,
        evidence_extractor: Optional[EvidenceExtractor] = None,
        conflict_detector: Optional[ConflictDetector] = None,
        option_comparator: Optional[OptionComparator] = None,
        report_generator: Optional[FinalReportGenerator] = None
    ):
        self.planner = planner or ResearchPlanner()
        self.researcher = researcher or InformationResearcher()
        self.evidence_extractor = evidence_extractor or EvidenceExtractor()
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.option_comparator = option_comparator or OptionComparator()
        self.report_generator = report_generator or FinalReportGenerator()

    async def run_research_pipeline(
        self,
        request: Union[str, ResearchRequest]
    ) -> Dict[str, Any]:
        """
        Executes complete autonomous research pipeline:
        Planner -> Researcher -> EvidenceExtractor -> ConflictDetector -> OptionComparator -> FinalReportGenerator
        """
        plan: ResearchPlan = await self.planner.create_plan(request)
        results: List[ResearchResult] = await self.researcher.execute_research(plan)
        claims: List[EvidenceClaim] = await self.evidence_extractor.extract_evidence(results)
        conflicts: List[DetectedConflict] = await self.conflict_detector.detect_conflicts(claims)
        comparison: ComparisonResult = await self.option_comparator.compare_options(
            plan=plan,
            claims=claims,
            conflicts=conflicts
        )
        final_report: FinalDecisionReport = await self.report_generator.generate_report(
            plan=plan,
            results=results,
            claims=claims,
            conflicts=conflicts,
            comparison=comparison
        )
        
        return {
            "research_plan": plan,
            "total_results": len(results),
            "research_results": results,
            "total_claims": len(claims),
            "evidence_claims": claims,
            "total_conflicts": len(conflicts),
            "conflicts": conflicts,
            "comparison": comparison,
            "final_report": final_report
        }
