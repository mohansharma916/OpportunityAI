"""
OpportunityOS — Auto-Apply Engine & Safety Circuit Breaker Tests
Verifies Automation Level 4/5 autonomous application flow and circuit breaker protections.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from apps.api.main import app
from apps.api.db import init_db, engine, Base


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_auto_apply_policy_and_circuit_breakers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Discover initial opportunities
        await client.post("/api/opportunities/discover")

        # Ingest a high-match opportunity (Score >= 88%)
        high_res = await client.post(
            "/api/opportunities/import",
            json={
                "url": "https://remote-tech.example.com/staff-platform",
                "title": "Staff Platform & Distributed Systems Engineer",
                "company": "CloudStream Systems",
                "body": "Seeking a Staff Engineer with deep React, TypeScript, Python, FastAPI, and PostgreSQL experience. 100% remote worldwide. $190,000 - $230,000.",
            },
        )
        assert high_res.status_code == 200
        high_opp = high_res.json()
        assert high_opp["matching_score"]["overall_match_score"] >= 88.0

        # Ingest a CAPTCHA-blocked opportunity to test the circuit breaker
        blocked_res = await client.post(
            "/api/opportunities/import",
            json={
                "url": "https://secure-careers.example.com/apply?turnstile_captcha_required=true",
                "title": "Senior Engineer (Anti-Bot Challenge)",
                "company": "SecurityLock Inc",
                "body": "Position requiring human verification with React and Python.",
            },
        )
        assert blocked_res.status_code == 200
        blocked_opp = blocked_res.json()

        # 2. Test under default Automation Level 3 (Approval Gate)
        # Attempting auto-apply without force should halt because level < 4
        level3_attempt = await client.post(f"/api/opportunities/{high_opp['id']}/auto-apply")
        assert level3_attempt.status_code == 200
        l3_data = level3_attempt.json()
        assert l3_data["applied"] is False
        assert l3_data["status"] == "APPROVAL_REQUIRED"

        # 3. Upgrade Automation Policy to Level 4 via AI Command
        cmd_res = await client.post(
            "/api/ai/command",
            json={"command": "Set automation level to 4"},
        )
        assert cmd_res.status_code == 200
        assert cmd_res.json()["automation_level"] == 4

        # 4. Now execute Auto-Apply on the high-match opportunity
        auto_res = await client.post(f"/api/opportunities/{high_opp['id']}/auto-apply")
        assert auto_res.status_code == 200
        auto_data = auto_res.json()
        assert auto_data["applied"] is True
        assert auto_data["status"] == "SUBMITTED"
        assert auto_data["confirmation_reference"] is not None

        # Verify opportunity status transitioned to APPLIED
        opp_check = await client.get(f"/api/opportunities/{high_opp['id']}")
        assert opp_check.json()["status"] == "APPLIED"

        # 5. Test Circuit Breaker: Auto-Apply on CAPTCHA / anti-bot challenge
        cb_res = await client.post(
            f"/api/opportunities/{blocked_opp['id']}/auto-apply",
            params={"force": True},
        )
        assert cb_res.status_code == 200
        cb_data = cb_res.json()
        assert cb_data["applied"] is False
        assert cb_data["status"] == "NEEDS_ATTENTION"
        assert cb_data["circuit_breaker"] is True

        # Verify opportunity status transitioned to NEEDS_ATTENTION
        blocked_check = await client.get(f"/api/opportunities/{blocked_opp['id']}")
        assert blocked_check.json()["status"] == "NEEDS_ATTENTION"

        # 6. Verify Audit Logs recorded AUTO_AGENT and CIRCUIT_BREAKER actors
        audit_res = await client.get("/api/activity")
        assert audit_res.status_code == 200
        audit_events = audit_res.json()
        actors = [e["actor"] for e in audit_events]
        assert "AUTO_AGENT" in actors
        assert "CIRCUIT_BREAKER" in actors
