"""
OpportunityOS — API Configuration
"""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "OpportunityOS"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./opportunity_os.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    TEMPORAL_HOST: str = os.getenv("TEMPORAL_HOST", "localhost:7233")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    AUTOMATION_LEVEL: int = int(os.getenv("AUTOMATION_LEVEL", "3"))  # 0 to 5
    SECRET_KEY: str = os.getenv("SECRET_KEY", "opportunity_os_super_secret_dev_key_2026")


settings = Settings()
