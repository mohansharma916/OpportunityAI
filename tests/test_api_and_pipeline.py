"""
OpportunityOS — Vertical Slice Integration Tests
Tests profile creation, opportunity discovery, multi-dimensional scoring,
tailored application package generation, approval & submission, and audit logs.
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
    # Cleanup after test suite
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_full_opportunity_vertical_slice():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health check
        res = await client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["service"] == "OpportunityOS"

        # 2. Candidate Profile & Verified Knowledge Base
        prof_res = await client.get("/api/profile")
        assert prof_res.status_code == 200
        profile_data = prof_res.json()
        assert profile_data["full_name"] == "Alex Morgan"
        assert len(profile_data["skills"]) >= 5
        assert len(profile_data["knowledge_items"]) >= 2
        assert len(profile_data["work_experiences"]) >= 2

        # 3. Discovery & Ingestion of Opportunities
        disc_res = await client.post("/api/opportunities/discover")
        assert disc_res.status_code == 200
        assert disc_res.json()["discovered_count"] >= 3

        # 4. List Opportunities with multi-dimensional match scores
        opps_res = await client.get("/api/opportunities")
        assert opps_res.status_code == 200
        opps = opps_res.json()
        assert len(opps) >= 3

        first_opp = opps[0]
        assert first_opp["company_name"] is not None
        assert "matching_score" in first_opp
        assert first_opp["matching_score"]["overall_match_score"] > 0
        assert "technical_match" in first_opp["matching_score"]
        assert len(first_opp["matching_score"]["match_rationale"]) > 10

        # 5. Manual Job Import (Pasting URL / text)
        import_res = await client.post(
            "/api/opportunities/import",
            json={
                "url": "https://careers.example.com/staff-frontend",
                "title": "Staff React / TypeScript Frontend Architect",
                "company": "NextGen Cloud",
                "body": "NextGen Cloud is seeking a Staff Frontend Architect with 6+ years React, TypeScript, Next.js, and web performance expertise. Remote worldwide. Offering $180,000 - $220,000.",
            },
        )
        assert import_res.status_code == 200
        imported_opp = import_res.json()
        assert imported_opp["company_name"] == "NextGen Cloud"
        assert imported_opp["matching_score"]["overall_match_score"] >= 80

        # 6. Prepare Application Package (Tailored Resume + Tailored Cover Letter)
        prep_res = await client.post(
            f"/api/opportunities/{imported_opp['id']}/prepare",
            json={"style": "TECHNICAL"},
        )
        assert prep_res.status_code == 200
        app_data = prep_res.json()
        assert app_data["status"] == "NEEDS_APPROVAL"
        assert app_data["resume_variant_id"] is not None
        assert app_data["cover_letter_id"] is not None

        # 7. Approve & Submit Application
        approve_res = await client.post(
            f"/api/applications/{app_data['id']}/approve",
            json={"user_notes": "Tailored resume highlights Next.js and latency accomplishments accurately."},
        )
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] == "SUBMITTED"

        # 8. Check Immutable Audit Activity Log
        activity_res = await client.get("/api/activity")
        assert activity_res.status_code == 200
        activities = activity_res.json()
        assert len(activities) >= 4
        actions = [a["action"] for a in activities]
        assert "APPLICATION_SUBMITTED" in actions
        assert "APPLICATION_PREPARED" in actions

        # 9. Verify Analytics & Funnel
        analytics_res = await client.get("/api/analytics")
        assert analytics_res.status_code == 200
        analytics = analytics_res.json()
        assert analytics["total_discovered"] >= 4
        assert analytics["applications_submitted"] >= 1
        assert len(analytics["funnel"]) == 6

        # 10. AI Command Bar execution
        cmd_res = await client.post(
            "/api/ai/command",
            json={"command": "Increase minimum contract rate to $95/hour"},
        )
        assert cmd_res.status_code == 200
        assert cmd_res.json()["new_value"] == 95.0

        # 11. Daily AI Briefing
        brief_res = await client.get("/api/briefing")
        assert brief_res.status_code == 200
        briefing = brief_res.json()
        assert "Alex" in briefing["summary_text"]
        assert briefing["opportunities_discovered_count"] >= 4
