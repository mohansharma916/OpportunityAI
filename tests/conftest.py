"""
Pytest configuration for OpportunityOS.
Forces all test suites to use an isolated SQLite test database so that
the active development database (opportunity_os.db) is never dropped.
"""

import os
import sys

# Isolate database for tests before any apps.api module is imported
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_opportunity_os.db"
