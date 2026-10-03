export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
  serpapi_configured: boolean;
  llm_provider: string;
  database_status: string;
  timestamp: string;
}

export interface ResearchPlan {
  decision_category: string;
  user_goal: string;
  budget?: string | null;
  hard_constraints: string[];
  preferences: string[];
  important_attributes: string[];
  research_questions: string[];
  required_search_types: string[];
  comparison_criteria: string[];
}

export interface ResearchResult {
  result_id?: string;
  query: string;
  source_type: string;
  title: string;
  url: string;
  snippet?: string;
  price?: string;
  price_raw?: number;
  currency?: string;
  rating?: number;
  reviews_count?: number;
  product_name?: string;
  publication_date?: string;
  thumbnail?: string;
  retrieved_at: string;
  raw_metadata?: Record<string, any>;
}

export interface EvidenceClaim {
  claim_id: string;
  entity: string;
  attribute: string;
  value: string;
  source_url: string;
  source_title?: string;
  source_type: string;
  evidence_text: string;
  confidence: string; // HIGH, MEDIUM, LOW, UNKNOWN
  supporting_result_id?: string;
  retrieved_at: string;
}

export interface DetectedConflict {
  conflict_id: string;
  entity: string;
  attribute: string;
  conflicting_values: string[];
  supporting_claims: EvidenceClaim[];
  severity: string; // low, medium, high
  resolution_status: string; // no_conflict, resolved, unresolved, insufficient_evidence
  explanation: string;
  recommended_verification: string;
  created_at: string;
}

export interface OptionRequirementMatch {
  requirement: string;
  status: 'satisfies' | 'does_not_satisfy' | 'partially_satisfies' | 'unknown' | 'conflicting';
  explanation: string;
  supporting_evidence: string[];
  source_urls: string[];
}

export interface OptionComparison {
  option_name: string;
  price?: string;
  attributes: Record<string, string>;
  requirement_alignment: OptionRequirementMatch[];
  known_tradeoffs: string[];
  uncertainties: string[];
  source_references: { title?: string; url: string }[];
}

export interface ComparisonResult {
  decision_category: string;
  compared_options: string[];
  criteria: string[];
  option_comparisons: OptionComparison[];
  trade_offs: string[];
  uncertainties: string[];
  conflicts_considered: string[];
  created_at: string;
}

export interface ReportOptionItem {
  name: string;
  requirement_alignment: OptionRequirementMatch[];
  strengths: string[];
  tradeoffs: string[];
  uncertainties: string[];
  evidence_references: { title?: string; url: string }[];
}

export interface FinalDecisionReport {
  title: string;
  summary: string;
  user_requirements: string[];
  options: ReportOptionItem[];
  key_findings: string[];
  trade_offs: string[];
  conflicts: DetectedConflict[];
  uncertainties: string[];
  verification_items: string[];
  source_references: { title?: string; url: string }[];
  generated_at: string;
}

export interface FullResearchResponse {
  research_plan: ResearchPlan;
  total_results: number;
  research_results: ResearchResult[];
  total_claims: number;
  evidence_claims: EvidenceClaim[];
  total_conflicts: number;
  conflicts: DetectedConflict[];
  comparison: ComparisonResult;
  final_report: FinalDecisionReport;
}
