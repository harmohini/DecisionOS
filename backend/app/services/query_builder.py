"""
Query Builder Service: Dynamically converts a ResearchPlan into targeted search queries
for SerpApi execution across Web, Shopping, and YouTube engines.
"""

from typing import List, Optional
from pydantic import BaseModel
from app.models.schemas import ResearchPlan
from app.config import settings

class SearchQueryTarget(BaseModel):
    query: str
    search_type: str  # "web", "shopping", "youtube"
    purpose: str

class QueryBuilder:
    def __init__(self, max_queries: Optional[int] = None):
        self.max_queries = max_queries or settings.MAX_RESEARCH_QUERIES

    def build_queries(self, plan: ResearchPlan) -> List[SearchQueryTarget]:
        """
        Dynamically constructs search queries from a structured ResearchPlan.
        """
        targets: List[SearchQueryTarget] = []
        allowed_types = set(plan.required_search_types or ["web"])

        # Extract context terms
        constraints_str = " ".join(plan.hard_constraints or [])
        pref_str = " ".join(plan.preferences or [])
        budget_str = f"under {plan.budget}" if plan.budget else ""
        
        # 1. Primary specification/product query (Web)
        if "web" in allowed_types:
            primary_q = f"{plan.user_goal} {constraints_str} {budget_str}".strip()
            targets.append(SearchQueryTarget(
                query=" ".join(primary_q.split()[:10]),  # Keep query concise
                search_type="web",
                purpose="Primary specification & candidate product identification"
            ))

        # 2. Research question queries (Web)
        if "web" in allowed_types and plan.research_questions:
            for q in plan.research_questions:
                if len(targets) >= self.max_queries:
                    break
                clean_q = q.replace("?", "").strip()
                targets.append(SearchQueryTarget(
                    query=clean_q,
                    search_type="web",
                    purpose="Answering specific research plan question"
                ))

        # 3. Shopping / Price comparison queries (Shopping)
        if "shopping" in allowed_types and len(targets) < self.max_queries:
            shopping_q = f"buy {plan.user_goal} {constraints_str} {budget_str}".strip()
            targets.append(SearchQueryTarget(
                query=" ".join(shopping_q.split()[:8]),
                search_type="shopping",
                purpose="Live market price & merchant availability comparison"
            ))

        # 4. Hands-on / Video reviews queries (YouTube)
        if "youtube" in allowed_types and len(targets) < self.max_queries:
            youtube_q = f"{plan.user_goal} review {pref_str}".strip()
            targets.append(SearchQueryTarget(
                query=" ".join(youtube_q.split()[:8]),
                search_type="youtube",
                purpose="Independent video review & thermal/performance benchmarks"
            ))

        # Fallback if no queries generated
        if not targets:
            targets.append(SearchQueryTarget(
                query=plan.user_goal,
                search_type="web",
                purpose="General web research fallback"
            ))

        # Apply maximum queries limit
        return targets[:self.max_queries]
