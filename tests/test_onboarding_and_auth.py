"""
OpportunityOS — Candidate Onboarding, Resume Parsing & Auth Tests
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
async def test_candidate_registration_parsing_and_onboarding():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Register new user
        reg_res = await client.post(
            "/api/auth/register",
            json={
                "email": "sarah.connor@example.com",
                "password": "securepassword123",
                "full_name": "Sarah Connor",
            },
        )
        assert reg_res.status_code == 200
        user = reg_res.json()
        assert user["email"] == "sarah.connor@example.com"
        assert user["onboarding_completed"] is False

        # 2. Upload / Parse resume text
        sample_resume = """
        Sarah Connor
        Senior Full Stack & AI Systems Architect
        sarah.connor@example.com | San Francisco, CA
        Summary: 8+ years architecting high-throughput distributed systems in Python, FastAPI, React, and TypeScript.
        Skills: React, TypeScript, Python, FastAPI, PostgreSQL, Docker, Redis, Kubernetes
        Experience:
        - Loomis Technologies | Staff Software Engineer (2021 - Present)
        Reduced API latency by 45% using async streaming in FastAPI and PostgreSQL.
        Scaled real-time telemetry pipeline to 50M daily events with Redis caching.
        """

        parse_res = await client.post(
            "/api/onboarding/parse-resume",
            json={"resume_text": sample_resume},
        )
        assert parse_res.status_code == 200
        parsed = parse_res.json()
        assert "Sarah Connor" in parsed["parsed_profile"]["full_name"]
        assert len(parsed["skills"]) >= 4
        assert len(parsed["knowledge_items"]) >= 1
        assert len(parsed["missing_fields"]) >= 5

        # 3. Complete onboarding with verified fields & launch discovery
        verified_payload = {
            "personal": parsed["parsed_profile"],
            "preferences": {
                "target_roles": ["Staff Software Engineer", "Founding Engineer"],
                "minimum_salary_annual": 170000.0,
                "minimum_hourly_rate": 95.0,
                "remote_preference": "REMOTE",
                "timezone_overlap_hours": 4,
                "notice_period_days": 14,
                "visa_sponsorship_needed": False,
                "authorized_countries": ["US", "EU"],
                "automation_level": 4,  # High-fit auto apply!
            },
            "skills": parsed["skills"],
            "knowledge_items": parsed["knowledge_items"],
            "work_experiences": parsed["work_experiences"],
        }

        complete_res = await client.post(
            "/api/onboarding/complete",
            json={
                "user_id": user["id"],
                "verified_data": verified_payload,
            },
        )
        assert complete_res.status_code == 200
        result = complete_res.json()
        assert result["status"] == "COMPLETED"
        assert result["opportunities_discovered"] >= 1

        # 4. Verify user state is now onboarding_completed = True
        me_res = await client.get(f"/api/auth/me?user_id={user['id']}")
        assert me_res.status_code == 200
        assert me_res.json()["onboarding_completed"] is True


@pytest.mark.asyncio
async def test_resume_file_upload_and_extraction():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        file_content = b"""Alex Morgan
Staff Systems Architect
alex.morgan@test.com | Remote
Skills: Python, FastAPI, React, PostgreSQL, Docker, Temporal
Achievements:
- Architected distributed event pipelines handling 100k+ events/day.
- Reduced database p95 response time by 35% with query optimization.
"""
        files = {"file": ("alex_morgan_resume.txt", file_content, "text/plain")}
        res = await client.post("/api/onboarding/upload-resume", files=files)
        assert res.status_code == 200
        data = res.json()
        assert "Alex Morgan" in data["parsed_profile"]["full_name"]
        assert len(data["skills"]) >= 3
        assert data["filename"] == "alex_morgan_resume.txt"
        assert "raw_extracted_text" in data


@pytest.mark.asyncio
async def test_auth_logout():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.post("/api/auth/logout")
        assert res.status_code == 200
        assert res.json()["status"] == "SUCCESS"


