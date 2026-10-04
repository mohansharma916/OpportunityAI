"""
OpportunityOS — LinkedIn AI Growth Agent Integration Test Suite
Verifies Profile Optimizer, Brand Strategy, Content Generation & Quality Checks,
Network Discovery & Relationship CRM, Comment Opportunities,
Human-in-the-Loop Approval Queue, Agent Decision Planner, and Command Center.
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
async def test_linkedin_growth_agent_full_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Dashboard Overview & Daily Briefing
        dash_res = await client.get("/api/linkedin/dashboard")
        assert dash_res.status_code == 200
        dash = dash_res.json()
        assert "professional_growth_score" in dash
        assert dash["professional_growth_score"] >= 60.0
        assert "daily_briefing" in dash
        assert "priority_1" in dash["daily_briefing"]

        # 2. Profile Optimizer Analysis & Scoring
        opt_res = await client.get("/api/linkedin/profile-optimizer")
        assert opt_res.status_code == 200
        opt_data = opt_res.json()
        assert "headline_score" in opt_data
        assert "recruiter_discoverability_score" in opt_data
        assert len(opt_data.get("recommendations", [])) >= 2
        suggested_headline = opt_data["headline_suggested"]

        # Apply user-approved recommendation
        apply_res = await client.post(
            "/api/linkedin/profile-optimizer/apply",
            json={"field": "headline", "value": suggested_headline},
        )
        assert apply_res.status_code == 200
        assert apply_res.json()["applied"] is True

        # 3. Personal Brand Strategy & Topic Pillars
        brand_res = await client.get("/api/linkedin/brand-strategy")
        assert brand_res.status_code == 200
        brand_data = brand_res.json()
        assert len(brand_data.get("topic_pillars", [])) >= 4
        assert len(brand_data.get("seven_day_plan", [])) == 7
        assert len(brand_data.get("thirty_day_plan", [])) >= 4

        # 4. Content Engine: List and Generate Grounded Post
        posts_res = await client.get("/api/linkedin/content")
        assert posts_res.status_code == 200
        posts = posts_res.json()
        assert len(posts) >= 1

        # Generate a new technical post with pre-publication quality check
        gen_res = await client.post(
            "/api/linkedin/content/generate",
            json={
                "post_type": "TECHNICAL_BREAKDOWN",
                "topic_pillar": "Technical Deep-Dives",
                "custom_topic": "Architecting Zero-Downtime Event Sinks with FastAPI",
            },
        )
        assert gen_res.status_code == 200
        new_post = gen_res.json()
        assert "Zero-Downtime" in new_post["title"]
        assert new_post["quality_checks"]["fact_check_passed"] is True
        assert new_post["quality_checks"]["anti_generic_score"] >= 90
        assert new_post["status"] == "APPROVAL_REQUIRED"

        # 5. Knowledge-Based Post Generation (From GitHub commit / PR)
        knowledge_res = await client.post(
            "/api/linkedin/content/from-knowledge",
            json={
                "knowledge_input": "commit 8bf32a: Implemented Redis Redlock with jittered exponential backoff",
                "source_type": "GITHUB_COMMIT",
            },
        )
        assert knowledge_res.status_code == 200
        k_post = knowledge_res.json()
        assert "Engineering Takeaway" in k_post["title"]

        # 6. Network Discovery & Relationship CRM
        rel_res = await client.get("/api/linkedin/relationships")
        assert rel_res.status_code == 200
        relationships = rel_res.json()
        assert len(relationships) >= 2
        first_rel = relationships[0]
        assert first_rel["relationship_score"] >= 75.0
        assert len(first_rel["score_reasons"]) >= 1
        assert "Hi " in first_rel["suggested_connection_message"]

        # Update relationship stage
        stage_res = await client.put(
            f"/api/linkedin/relationships/{first_rel['id']}/stage",
            json={"stage": "CONNECTION_PROPOSED"},
        )
        assert stage_res.status_code == 200
        assert stage_res.json()["stage"] == "CONNECTION_PROPOSED"

        # 7. Comment Opportunity Engine (High-signal technical perspective)
        comment_res = await client.get("/api/linkedin/comment-opportunities")
        assert comment_res.status_code == 200
        comments = comment_res.json()
        assert len(comments) >= 1
        assert len(comments[0]["suggested_comment"]) > 40

        # 8. Target Company Intelligence
        comp_res = await client.get("/api/linkedin/companies")
        assert comp_res.status_code == 200
        comps = comp_res.json()
        assert len(comps) >= 2
        assert len(comps[0]["tech_stack"]) >= 3

        # 9. Human-in-the-Loop Approval Queue & Decision Engine
        actions_res = await client.get("/api/linkedin/actions/approvals")
        assert actions_res.status_code == 200
        pending_actions = actions_res.json()
        assert len(pending_actions) >= 1

        target_action = pending_actions[0]
        decide_res = await client.post(
            f"/api/linkedin/actions/{target_action['id']}/decide",
            json={"decision": "APPROVE"},
        )
        assert decide_res.status_code == 200
        assert decide_res.json()["status"] == "APPROVED"

        # 10. AI Agent Decision Planner Cycle
        cycle_res = await client.post("/api/linkedin/agent/run-cycle")
        assert cycle_res.status_code == 200
        cycle = cycle_res.json()
        assert cycle["cycle_completed"] is True
        assert "decision" in cycle

        # 11. Command Center (Natural Language Instruction Processing)
        cmd_res = await client.post(
            "/api/linkedin/command",
            json={"prompt": "Write a post about Redis distributed locks"},
        )
        assert cmd_res.status_code == 200
        cmd_data = cmd_res.json()
        assert cmd_data["intent"] == "GENERATE_POST"
        assert "Successfully drafted" in cmd_data["message"]
