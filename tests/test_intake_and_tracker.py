"""
OpportunityOS — Candidate Intake (answer bank) & Application Tracker API Tests
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, delete, inspect, text

from apps.api.main import app
from apps.api.db import init_db, get_db, _purge_stored_credentials
from apps.api.models import CandidateIntakeModel, TrackedApplicationModel
from apps.api.services.intake_service import IntakeService


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    await init_db()
    async for db in get_db():
        await db.execute(delete(TrackedApplicationModel))
        await db.execute(delete(CandidateIntakeModel))
        await db.commit()
        break
    yield


@pytest.mark.asyncio
async def test_intake_completeness_and_secret_stripping():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/intake")
        assert res.status_code == 200
        intake = res.json()
        assert intake["targeting"]["daily_cap"] == 15
        assert intake["completeness"]["ready_for_automation"] is False

        res = await client.put("/api/intake", json={
            "identity": {
                "full_name": "Priya Raman", "email": "priya@example.com", "phone": "+91 98765 43210",
                "country": "India", "timezone": "Asia/Kolkata", "linkedin_url": "https://linkedin.com/in/priya",
                "password": "must-not-be-stored",
            },
            "accounts": {"linkedin": True, "li_at": "cookie-must-not-be-stored"},
        })
        assert res.status_code == 200
        data = res.json()
        assert data["identity"]["full_name"] == "Priya Raman"
        assert "password" not in data["identity"]
        assert "li_at" not in data["accounts"]
        assert data["completeness"]["missing"]["identity"] == []
        assert "target_titles" in data["completeness"]["missing"]["targeting"]

        # Partial updates merge instead of replacing the section
        res = await client.put("/api/intake", json={"identity": {"city": "Bengaluru"}})
        assert res.json()["identity"]["full_name"] == "Priya Raman"
        assert res.json()["identity"]["city"] == "Bengaluru"


@pytest.mark.asyncio
async def test_answer_bank_built_from_intake():
    await init_db()
    async for db in get_db():
        await IntakeService.update(db, {
            "identity": {"full_name": "Priya Raman", "email": "priya@example.com"},
            "screening": {"needs_sponsorship": False},
            "documents": {"master_resume_path": "/tmp/resume.pdf"},
        })
        bank = await IntakeService.build_answer_bank(db)
        break
    assert bank.answers["first_name"] == "Priya"
    assert bank.answers["last_name"] == "Raman"
    assert bank.answers["needs_sponsorship"] == "No"
    assert bank.resume_path == "/tmp/resume.pdf"


@pytest.mark.asyncio
async def test_tracker_crud_dedup_and_follow_up():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/tracker", json={
            "company": "Supabase Inc.", "role": "Backend Engineer",
            "job_url": "https://jobs.ashbyhq.com/supabase/123", "source_platform": "We Work Remotely",
            "apply_channel": "ASHBY", "match_score": 82,
        })
        assert res.status_code == 200
        row = res.json()
        assert row["status"] == "QUEUED"

        # Same company + role from another board is a duplicate
        dup = await client.post("/api/tracker", json={"company": "supabase", "role": "backend engineer"})
        assert dup.status_code == 409
        assert dup.json()["detail"]["application"]["id"] == row["id"]

        bad = await client.put(f"/api/tracker/{row['id']}", json={"status": "TELEPORTED"})
        assert bad.status_code == 400

        res = await client.put(f"/api/tracker/{row['id']}", json={"status": "submitted"})
        assert res.status_code == 200
        submitted = res.json()
        assert submitted["status"] == "SUBMITTED"
        assert submitted["submitted_at"] is not None
        assert submitted["next_action"] == "Follow up"
        assert submitted["next_action_due"] > submitted["submitted_at"]

        # LinkedIn hiring post row
        post = await client.post("/api/tracker", json={
            "company": "Acme Remote", "role": "Python Developer", "source_platform": "LinkedIn post",
            "apply_channel": "LINKEDIN_DM", "post_url": "https://www.linkedin.com/posts/acme-hiring",
        })
        assert post.status_code == 200

        listed = await client.get("/api/tracker", params={"source_platform": "LinkedIn post"})
        assert [r["company"] for r in listed.json()] == ["Acme Remote"]

        stats = (await client.get("/api/tracker/stats")).json()
        assert stats["by_status"]["SUBMITTED"] >= 1
        assert stats["submitted_today"] >= 1
        assert "QUEUED" in stats["statuses"]

        assert (await client.delete(f"/api/tracker/{post.json()['id']}")).status_code == 200
        assert (await client.delete(f"/api/tracker/{post.json()['id']}")).status_code == 404


def test_purge_drops_legacy_credentials(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE account_credentials (id TEXT, password TEXT)"))
        conn.execute(text(
            "CREATE TABLE scraping_platforms (id TEXT, name TEXT, auth_username TEXT, auth_password TEXT)"
        ))
        conn.execute(text("INSERT INTO scraping_platforms VALUES ('1', 'Wellfound', 'me', 'secret')"))
        _purge_stored_credentials(conn)
    inspector = inspect(engine)
    assert "account_credentials" not in inspector.get_table_names()
    cols = {c["name"] for c in inspector.get_columns("scraping_platforms")}
    assert cols == {"id", "name"}


@pytest.mark.asyncio
async def test_signed_in_user_claims_intake_saved_before_sign_in():
    async for db in get_db():
        await IntakeService.update(db, {"identity": {"full_name": "Priya Raman"}})
        claimed = await IntakeService.get_or_create(db, user_id="user-1")
        assert claimed.identity["full_name"] == "Priya Raman"
        assert claimed.user_id == "user-1"
        # Calls without a user (worker, optimizer) read the same row
        assert (await IntakeService.get_or_create(db)).id == claimed.id
        break
