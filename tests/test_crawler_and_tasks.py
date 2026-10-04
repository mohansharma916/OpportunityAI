"""
OpportunityOS — Autonomous Crawler & Application Lifecycle Task Tests
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from apps.api.main import app
from apps.api.db import init_db, engine, Base, get_db
from apps.api.services.profile_service import ProfileService


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    await init_db()
    async for db in get_db():
        await ProfileService.get_or_create_profile(db, seed_if_empty=True)
        break
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_crawler_execution_and_application_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Update candidate profile with specific preferences and currency
        prof_res = await client.put(
            "/api/profile",
            json={
                "full_name": "Alex Mercer",
                "headline": "Lead Systems Architect & Python Engineer",
                "location": "Berlin, Germany",
                "salary_currency": "EUR",
                "minimum_salary_annual": 85000.0,
                "remote_preference": "REMOTE",
                "target_roles": ["Python Engineer", "Backend Architect"],
            },
        )
        assert prof_res.status_code == 200
        prof_data = prof_res.json()
        assert prof_data["salary_currency"] == "EUR"
        assert prof_data["minimum_salary_annual"] == 85000.0

        # 2. Add skill with duration
        skill_res = await client.post(
            "/api/profile/skills",
            json={
                "skill_name": "FastAPI",
                "proficiency": "EXPERT",
                "experience_years": 5.0,
            },
        )
        assert skill_res.status_code == 200
        assert skill_res.json()["skill_name"] == "FastAPI"
        assert skill_res.json()["experience_years"] == 5.0

        # 3. Trigger autonomous crawler with custom limits (10 mins, max 2 apps)
        crawl_res = await client.post(
            "/api/crawler/run",
            json={
                "max_duration_minutes": 10,
                "max_applications": 2,
                "min_match_score": 50.0,
                "target_platforms": ["arbeitnow", "jobicy", "github", "hackernews"],
                "opportunity_types": ["FULL_TIME", "REMOTE", "CONTRACT_PART_TIME", "OPEN_SOURCE_CONTRIBUTION"],
                "auto_apply_enabled": True,
            },
        )
        assert crawl_res.status_code == 200
        crawl_data = crawl_res.json()
        assert "session_id" in crawl_data
        assert "summary_text" in crawl_data
        assert len(crawl_data["execution_logs"]) > 0

        # 4. Check crawler status endpoint
        status_res = await client.get("/api/crawler/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["latest_session"] is not None

        # 5. Check opportunities and applications
        opps_res = await client.get("/api/opportunities")
        assert opps_res.status_code == 200
        opps = opps_res.json()
        if len(opps) == 0:
            disc_res = await client.post("/api/opportunities/discover")
            assert disc_res.status_code == 200
            opps_res = await client.get("/api/opportunities")
            opps = opps_res.json()
        assert len(opps) > 0

        # Find or prepare an application
        target_opp = opps[0]
        app_prep = await client.post(f"/api/opportunities/{target_opp['id']}/prepare")
        assert app_prep.status_code == 200
        app_data = app_prep.json()
        app_id = app_data["id"]

        # Verify default lifecycle tasks are attached
        assert len(app_data.get("tasks", [])) >= 4

        # 6. Add custom lifecycle task
        task_res = await client.post(
            f"/api/applications/{app_id}/tasks",
            json={
                "title": "Prepare portfolio live demo link",
            },
        )
        assert task_res.status_code == 200
        updated_tasks = task_res.json()
        assert any(t["title"] == "Prepare portfolio live demo link" for t in updated_tasks)

        # 7. Toggle completion of the newly added task (initial status PENDING -> COMPLETED)
        target_task_id = updated_tasks[-1]["id"]
        toggle_res = await client.put(f"/api/applications/{app_id}/tasks/{target_task_id}")
        assert toggle_res.status_code == 200
        toggled_tasks = toggle_res.json()
        target_task = next(t for t in toggled_tasks if t["id"] == target_task_id)
        assert target_task["status"] == "COMPLETED"

        # 8. Update application status
        status_update = await client.put(
            f"/api/applications/{app_id}/status",
            json={"status": "INTERVIEWING"},
        )
        assert status_update.status_code == 200
        assert status_update.json()["status"] == "INTERVIEWING"

        # 9. Verify autonomous schedule creation
        sched_res = await client.post(
            "/api/crawler/schedule",
            json={
                "interval_hours": 6,
                "max_duration_minutes": 15,
                "max_applications": 5,
                "min_match_score": 75.0,
                "target_platforms": ["arbeitnow", "jobicy"],
                "opportunity_types": ["REMOTE", "CONTRACT_PART_TIME"],
                "auto_apply_enabled": True,
            },
        )
        assert sched_res.status_code == 200
        sched_data = sched_res.json()
        assert sched_data["interval_hours"] == 6
        assert sched_data["is_active"] is True
