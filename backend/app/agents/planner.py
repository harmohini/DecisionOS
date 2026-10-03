"""
Planner Agent: Analyzes natural language decision requests and constructs
structured research plans using the LLM Service abstraction.
Does NOT execute search queries or call SerpApi directly.
"""

import re
from typing import Union, Optional
from app.models.schemas import ResearchRequest, ResearchPlan
from app.services.llm import LLMService, LLMNotConfiguredError, LLMError

class PlannerError(Exception):
    """Exception raised for errors during research plan generation."""
    pass

class ResearchPlanner:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self._is_explicit_llm = llm_service is not None
        self.llm_service = llm_service or LLMService()

    async def create_plan(self, request: Union[str, ResearchRequest]) -> ResearchPlan:
        """
        Analyzes natural-language user input and generates a structured ResearchPlan.
        Raises ValueError if query is empty.
        Raises LLMNotConfiguredError if LLM provider API key is missing and an explicit LLMService was provided.
        """
        if isinstance(request, ResearchRequest):
            user_input = request.query
        elif isinstance(request, str):
            user_input = request
        else:
            raise ValueError("Input request must be a string or ResearchRequest instance.")

        if not user_input or not user_input.strip():
            raise ValueError("Research request query cannot be empty.")

        query_text = user_input.strip()

        planner_system_prompt = (
            "You are the Planner Agent for DecisionOS, an autonomous evidence-based decision engine.\n"
            "Your objective is to analyze arbitrary natural language user decision requests and create a structured research plan.\n\n"
            "Rules:\n"
            "1. Identify the decision category dynamically (e.g. 'electronics/product research', 'travel/hotel research', 'software/tool comparison', 'vehicle research'). Do NOT restrict yourself to laptops.\n"
            "2. Extract explicit monetary budget if specified (e.g. '₹1,20,000' or '$1,500'). If not mentioned, return null.\n"
            "3. Separate hard non-negotiable constraints from desirable preferences.\n"
            "4. Formulate specific, objective research questions to guide facts extraction.\n"
            "5. Select required search engine types ONLY from ['web', 'shopping', 'youtube'] based on what is relevant for the decision category.\n"
            "6. Define objective comparison criteria tailored specifically to the user's request.\n"
            "7. Return ONLY a valid JSON object strictly matching the ResearchPlan schema."
        )

        try:
            plan = await self.llm_service.generate_structured_output(
                prompt=query_text,
                response_model=ResearchPlan,
                system_prompt=planner_system_prompt
            )
            return plan

        except LLMNotConfiguredError:
            if self._is_explicit_llm:
                raise
            return self._rule_based_plan(query_text)
        except LLMError as exc:
            raise PlannerError(f"Failed to generate research plan: {str(exc)}")
        except Exception as exc:
            raise PlannerError(f"Unexpected error in Planner Agent: {str(exc)}")

    def _rule_based_plan(self, query: str) -> ResearchPlan:
        """
        Rule-based heuristic plan generation when LLM API key is not configured in environment.
        """
        q_lower = query.lower()

        # Extract budget
        budget_match = re.search(r'(?:₹|\$|EUR|INR|USD)\s*[\d,]+|(?:under|below|budget|max|around)\s*(?:₹|\$|INR|USD)?\s*[\d,]+', query, re.IGNORECASE)
        budget = budget_match.group(0).strip() if budget_match else None

        # Category detection
        if any(k in q_lower for k in ["laptop", "computer", "macbook", "pc", "desktop"]):
            category = "electronics/product research"
        elif any(k in q_lower for k in ["hotel", "resort", "flight", "trip", "travel", "vacation"]):
            category = "travel/hotel research"
        elif any(k in q_lower for k in ["headphone", "earphone", "tv", "camera", "phone", "smartphone"]):
            category = "electronics/product research"
        elif any(k in q_lower for k in ["car", "ev", "suv", "vehicle", "bike"]):
            category = "vehicle research"
        else:
            category = "general research"

        # Constraints & Preferences
        constraints = []
        preferences = []
        if budget:
            constraints.append(f"budget max {budget}")

        ram_match = re.search(r'\b\d+\s*GB\s*(?:RAM|Memory)?\b', query, re.IGNORECASE)
        if ram_match:
            constraints.append(f"at least {ram_match.group(0).strip()}")

        if "battery" in q_lower:
            preferences.append("good battery life")
        if "gaming" in q_lower:
            preferences.append("occasional gaming capability")

        return ResearchPlan(
            decision_category=category,
            user_goal=query,
            budget=budget,
            hard_constraints=constraints if constraints else [query],
            preferences=preferences,
            important_attributes=["RAM capacity", "Processor (CPU)", "Price", "Battery life", "User Ratings"],
            research_questions=[
                f"What are the top options matching '{query}'?",
                "What are current prices and merchant availability?",
                "What are reported user review strengths and trade-offs?"
            ],
            required_search_types=["web", "shopping", "youtube"],
            comparison_criteria=["Price", "Specification Match", "Key Strengths", "Known Trade-offs"]
        )
