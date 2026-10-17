"""
OpportunityOS — API Configuration
"""

import os
from pathlib import Path
from pydantic import BaseModel

# AI settings may live in the project's .env, so the API and the worker on the Mac both pick them up.
# Only these keys are read from it, and a variable already set in the environment wins.
_ENV_FILE_KEYS = ("OPENAI_API_KEY", "OPENAI_MODEL", "ANTHROPIC_API_KEY", "LLM_PROVIDER")


def _load_env_file(path: Path = Path(__file__).resolve().parents[2] / ".env") -> None:
    if os.getenv("OPPORTUNITY_OS_SKIP_ENV_FILE") or not path.is_file():
        return
    for line in path.read_text().splitlines():
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if sep and key in _ENV_FILE_KEYS and value and not os.getenv(key):
            os.environ[key] = value


_load_env_file()


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
