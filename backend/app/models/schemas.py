from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class HealthCheckResponse(BaseModel):
    status: str = Field("ok", description="Service health status")
    app_name: str
    version: str
    serpapi_configured: bool
    llm_provider: str
    database_status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SystemStatusResponse(BaseModel):
    status: str
    message: str
    components: Dict[str, Any]

class ResearchRequest(BaseModel):
    query: str = Field(..., description="User decision goal or research request")
    category: Optional[str] = Field("product_research", description="Research category e.g. product/laptop research")
    budget_currency: Optional[str] = "INR"
    max_budget: Optional[float] = None
    constraints: Optional[List[str]] = Field(default_factory=list, description="Extracted user constraints")

class ResearchPlanItem(BaseModel):
    step_id: int
    query: str
    purpose: str
    engine: str = "google"

class ResearchPlan(BaseModel):
    decision_category: str = Field(..., description="Type of decision e.g. electronics/product research, travel/hotel research, software/tool comparison")
    user_goal: str = Field(..., description="High-level user decision goal")
    budget: Optional[str] = Field(None, description="Extracted monetary budget limit e.g. ₹1,20,000 or $1,500")
    hard_constraints: List[str] = Field(default_factory=list, description="Non-negotiable required specifications or criteria")
    preferences: List[str] = Field(default_factory=list, description="Desirable features or preferences")
    important_attributes: List[str] = Field(default_factory=list, description="Key product/service dimensions to evaluate")
    research_questions: List[str] = Field(default_factory=list, description="Specific questions to answer through research")
    required_search_types: List[str] = Field(default_factory=list, description="Search engines needed e.g. ['web', 'shopping', 'youtube']")
    comparison_criteria: List[str] = Field(default_factory=list, description="Criteria for comparing candidate options")

class ClaimEvidence(BaseModel):
    source_title: str
    source_url: str
    domain: str
    snippet: str
    confidence_score: float

class FactualClaim(BaseModel):
    claim_id: str
    product_name: str
    attribute: str
    stated_value: str
    evidence_status: str  # verified, reported, unverified, conflicting
    sources: List[ClaimEvidence]

class ConflictItem(BaseModel):
    attribute: str
    product_name: str
    conflicting_claims: List[Dict[str, Any]]
    resolution_notes: str

class ProductComparisonOption(BaseModel):
    product_name: str
    price: Optional[str] = None
    specs: Dict[str, Any]
    pros: List[str]
    cons: List[str]
    matched_requirements: List[str]
    unmet_requirements: List[str]

class DecisionReport(BaseModel):
    session_id: str
    query: str
    summary: str
    recommended_options: List[ProductComparisonOption]
    claims: List[FactualClaim]
    conflicts: List[ConflictItem]
    trade_offs: List[str]
    uncertainties: List[str]
    sources: List[Dict[str, str]]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NormalizedSearchResult(BaseModel):
    id: Optional[str] = None
    title: str
    link: str
    source: Optional[str] = None
    snippet: Optional[str] = None
    price: Optional[str] = None
    price_raw: Optional[float] = None
    currency: Optional[str] = None
    product_info: Optional[Dict[str, Any]] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    thumbnail: Optional[str] = None
    result_type: str = "organic"  # organic, shopping, youtube, knowledge_graph
    raw_metadata: Optional[Dict[str, Any]] = None

class NormalizedSearchResponse(BaseModel):
    query: str
    engine: str
    total_results: int
    results: List[NormalizedSearchResult]
    search_metadata: Optional[Dict[str, Any]] = None

class ResearchResult(BaseModel):
    result_id: Optional[str] = None
    query: str
    source_type: str  # web, shopping, youtube
    title: str
    url: str  # Mandatory source URL for provenance
    snippet: Optional[str] = None
    price: Optional[str] = None
    price_raw: Optional[float] = None
    currency: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    product_name: Optional[str] = None
    publication_date: Optional[str] = None
    thumbnail: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    raw_metadata: Optional[Dict[str, Any]] = None

class EvidenceClaim(BaseModel):
    claim_id: str
    entity: str
    attribute: str
    value: str
    source_url: str
    source_title: Optional[str] = None
    source_type: str = "general_web"  # official, retailer, review, video, forum, news, general_web, unknown
    evidence_text: str
    confidence: str = "MEDIUM"  # HIGH, MEDIUM, LOW, UNKNOWN
    supporting_result_id: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)

class ExtractedClaimItem(BaseModel):
    entity: str
    attribute: str
    value: str
    evidence_text: str

class ExtractedClaimList(BaseModel):
    claims: List[ExtractedClaimItem] = Field(default_factory=list)

class DetectedConflict(BaseModel):
    conflict_id: str
    entity: str
    attribute: str
    conflicting_values: List[str]
    supporting_claims: List[EvidenceClaim] = Field(default_factory=list)
    severity: str = "medium"  # low, medium, high
    resolution_status: str = "unresolved"  # no_conflict, resolved, unresolved, insufficient_evidence
    explanation: str
    recommended_verification: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OptionRequirementMatch(BaseModel):
    requirement: str
    status: str = "unknown"  # satisfies, does_not_satisfy, partially_satisfies, unknown, conflicting
    explanation: str
    supporting_evidence: List[str] = Field(default_factory=list)
    source_urls: List[str] = Field(default_factory=list)

class OptionComparison(BaseModel):
    option_name: str
    price: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)
    requirement_alignment: List[OptionRequirementMatch] = Field(default_factory=list)
    known_tradeoffs: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    source_references: List[Dict[str, str]] = Field(default_factory=list)

class ComparisonResult(BaseModel):
    decision_category: str
    compared_options: List[str] = Field(default_factory=list)
    criteria: List[str] = Field(default_factory=list)
    option_comparisons: List[OptionComparison] = Field(default_factory=list)
    trade_offs: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    conflicts_considered: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReportOptionItem(BaseModel):
    name: str
    requirement_alignment: List[OptionRequirementMatch] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    evidence_references: List[Dict[str, str]] = Field(default_factory=list)

class FinalDecisionReport(BaseModel):
    title: str
    summary: str
    user_requirements: List[str] = Field(default_factory=list)
    options: List[ReportOptionItem] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    trade_offs: List[str] = Field(default_factory=list)
    conflicts: List[DetectedConflict] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    verification_items: List[str] = Field(default_factory=list)
    source_references: List[Dict[str, str]] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)






