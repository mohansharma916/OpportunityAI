"""
Pytest configuration for OpportunityOS.
Forces all test suites to use an isolated SQLite test database so that
the active development database (opportunity_os.db) is never dropped.
"""

import os
import sys

# Isolate database for tests before any apps.api module is imported
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_opportunity_os.db"
# Never call a real AI provider from tests: ignore .env keys and clear any in the shell
os.environ["OPPORTUNITY_OS_SKIP_ENV_FILE"] = "1"
for _key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "LLM_PROVIDER"):
    os.environ.pop(_key, None)
