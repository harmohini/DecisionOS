from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.config import settings
from app.models.schemas import HealthCheckResponse
from app.models.database import get_db
from app.serpapi.client import SerpApiClient, SerpApiMissingKeyError

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthCheckResponse)
@router.get("/api/v1/health", response_model=HealthCheckResponse)
async def check_health(db: Session = Depends(get_db)):
    # Check DB status
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    try:
        serpapi_client = SerpApiClient()
        serpapi_configured = serpapi_client.is_configured
    except SerpApiMissingKeyError:
        serpapi_configured = False

    return HealthCheckResponse(
        status="ok",
        app_name=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        serpapi_configured=serpapi_configured,
        llm_provider=settings.LLM_PROVIDER,
        database_status=db_status,
        timestamp=datetime.utcnow()
    )
