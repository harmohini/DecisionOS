import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for backend (directory containing app/)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE_PATH = os.path.join(BACKEND_DIR, ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "DecisionOS"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Server configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Database configuration (SQLite default, modular for PostgreSQL)
    DATABASE_URL: str = "sqlite:///./decisionos.db"
    
    # SerpApi configuration (MUST ONLY BE USED ON BACKEND)
    SERPAPI_API_KEY: str = ""
    MAX_RESEARCH_QUERIES: int = 6
    
    # LLM configuration
    LLM_PROVIDER: str = "openai"  # openai, groq, anthropic, google
    LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=(".env", ENV_FILE_PATH, "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
