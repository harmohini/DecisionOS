from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from app.models.schemas import ResearchRequest
from app.services.pipeline import ResearchPipeline
from app.serpapi.client import SerpApiMissingKeyError, SerpApiAuthError, SerpApiRateLimitError
from app.services.llm import LLMNotConfiguredError, LLMError
from app.agents.planner import PlannerError

router = APIRouter(prefix="/api/v1/decisions", tags=["Decisions"])

@router.post("/research")
async def execute_decision_research(request: ResearchRequest) -> Dict[str, Any]:
    """
    Submits a natural language decision request and executes full DecisionOS research pipeline:
    Planner -> Researcher -> EvidenceExtractor -> ConflictDetector -> OptionComparator -> FinalReportGenerator
    Returns structured plan, results, claims, conflicts, comparison matrix, and final decision report.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'query' cannot be empty."
        )

    pipeline = ResearchPipeline()

    try:
        pipeline_output = await pipeline.run_research_pipeline(request)
        return pipeline_output

    except SerpApiMissingKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except SerpApiAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"SerpApi Authentication Error: {exc.message}"
        )
    except SerpApiRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"SerpApi Rate Limit Exceeded: {exc.message}"
        )
    except LLMNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except (PlannerError, LLMError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research Pipeline Error: {str(exc)}"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error during decision research: {str(exc)}"
        )
