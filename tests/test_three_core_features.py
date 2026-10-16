"""
OpportunityOS — Test Suite for the Core Features
1. Job discovery (Platforms list, User & AI additions, Date grouping, User status tracking, Queue to apply)
2. LinkedIn Post Studio (Post publisher, Post analysis, Human post synthesis)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.main import app
from apps.api.db import init_db


@pytest.mark.asyncio
async def test_feature_1_job_scraper_and_human_apply():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch platforms (seeds defaults if empty)
        resp = await client.get("/api/platforms")
        assert resp.status_code == 200
        platforms = resp.json()
        assert len(platforms) >= 4
        platform_names = [p["name"] for p in platforms]
        assert any("Arbeitnow" in n for n in platform_names)

        # 2. User adds a custom platform (logins live in the browser profile, never in the API)
        create_payload = {
            "name": "Wellfound Custom Startups",
            "url": "https://wellfound.com/jobs/startups",
            "category": "STARTUPS",
            "requires_auth": True,
            "auth_notes": "Requires 2FA verification code.",
            "crawl_frequency_hours": 8,
        }
        res_create = await client.post("/api/platforms", json=create_payload)
        assert res_create.status_code == 200
        new_platform = res_create.json()
        assert new_platform["name"] == "Wellfound Custom Startups"
        assert new_platform["added_by"] == "USER"
        platform_id = new_platform["id"]

        # 3. AI discovers and adds new platforms
        res_ai = await client.post("/api/platforms/ai-discover")
        assert res_ai.status_code == 200
        ai_data = res_ai.json()
        assert ai_data["success"] is True

        # 4. Scrape single platform
        res_single_scrape = await client.post(f"/api/platforms/{platform_id}/scrape")
        assert res_single_scrape.status_code == 200
        scrape_result = res_single_scrape.json()
        assert scrape_result["status"] == "SUCCESS"

        # 5. Get date-grouped opportunities
        res_grouped = await client.get("/api/opportunities/grouped-by-date")
        assert res_grouped.status_code == 200
        grouped_data = res_grouped.json()
        assert "groups" in grouped_data
        assert "today" in grouped_data["groups"]
        assert "status_counts" in grouped_data

        # Find an opportunity to track status and apply
        all_opps = (
            grouped_data["groups"]["today"]
            + grouped_data["groups"]["yesterday"]
            + grouped_data["groups"]["this_week"]
            + grouped_data["groups"]["earlier"]
        )
        assert len(all_opps) > 0
        target_opp = all_opps[0]
        opp_id = target_opp["id"]

        # 6. User maintains and updates status
        res_status = await client.put(
            f"/api/opportunities/{opp_id}/user-status",
            json={"status": "REVIEWING", "reason": "Candidate evaluating compensation package."},
        )
        assert res_status.status_code == 200
        assert res_status.json()["status"] == "REVIEWING"

        # 7. Queue the application in the tracker (the worker fills it; nothing is submitted here)
        res_apply = await client.post(f"/api/opportunities/{opp_id}/human-apply")
        assert res_apply.status_code == 200
        apply_result = res_apply.json()
        assert apply_result["success"] is True
        assert apply_result["status"] == "QUEUED"
        assert apply_result["application"]["opportunity_id"] == opp_id

        # 8. Queuing the same role again is rejected as a duplicate
        res_dup = await client.post(f"/api/opportunities/{opp_id}/human-apply")
        assert res_dup.status_code == 409

        # 9. No credential fields are exposed for platforms
        assert all("has_password" not in p for p in (await client.get("/api/platforms")).json())


@pytest.mark.asyncio
async def test_feature_2_linkedin_post_studio():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Removed: bulk scraping, connection bot and the credentials vault
        assert (await client.post("/api/linkedin/automate-connections", json={"count": 1})).status_code in (404, 405)
        assert (await client.get("/api/linkedin/credentials")).status_code in (404, 405)

        # 4. Generate & Publish Post to LinkedIn
        post_gen = await client.post(
            "/api/linkedin/content/generate",
            json={"post_type": "TECHNICAL_BREAKDOWN", "topic_pillar": "Technical Deep-Dives"},
        )
        assert post_gen.status_code == 200
        post_id = post_gen.json()["id"]

        res_pub = await client.post(f"/api/linkedin/posts/{post_id}/publish")
        assert res_pub.status_code == 200
        assert res_pub.json()["status"] == "PUBLISHED"

        # 5. Multi-Type Post Scraping (Hiring, Freelancing, Collab, Interesting)
        res_multi_scraped = await client.get("/api/linkedin/scraped-posts")
        assert res_multi_scraped.status_code == 200
        scraped_posts = res_multi_scraped.json()
        assert len(scraped_posts) >= 4
        # Verify presence of multiple types
        types_found = {p["scrape_type"] for p in scraped_posts}
        assert "HIRING_POST" in types_found
        assert "FREELANCE_GIG" in types_found
        assert "INTERESTING_POST" in types_found

        target_scraped = scraped_posts[0]
        scraped_id = target_scraped["id"]

        # 6. Analyze Post Dynamics in Post Studio
        res_analysis = await client.post(f"/api/linkedin/posts/{scraped_id}/analyze")
        assert res_analysis.status_code == 200
        analysis_data = res_analysis.json()
        assert "hook_technique" in analysis_data
        assert "human_angles" in analysis_data
        assert len(analysis_data["human_angles"]) >= 3

        # 7. Synthesize Human-like Post based on Analysis
        angle_key = analysis_data["human_angles"][0]["key"]
        res_synth = await client.post(
            f"/api/linkedin/posts/{scraped_id}/synthesize-human-post",
            json={"angle_key": angle_key, "custom_notes": "Tested in our multi-worker cluster."},
        )
        assert res_synth.status_code == 200
        synth_data = res_synth.json()
        assert "content_text" in synth_data
        assert synth_data["post_type"] == "HUMAN_SYNTHESIS"
        assert synth_data["quality_checks"]["human_rhythm_verified"] is True
        assert len(synth_data["content_text"]) > 200

        # 8. Check Post Studio Analyzed Library Tracking
        res_lib = await client.get("/api/linkedin/post-studio/library")
        assert res_lib.status_code == 200
        lib_data = res_lib.json()
        assert len(lib_data) >= 1
        assert lib_data[0]["id"] == scraped_id
        assert lib_data[0]["linked_draft"] is not None
