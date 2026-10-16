"""
OpportunityOS — Test Suite for the Core Features
1. Job discovery (sources, discovery run, scoring, queue to apply)
2. LinkedIn Post Studio (Post publisher, Post analysis, Human post synthesis)
"""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.main import app
from apps.api.db import init_db
from packages.connectors.job_feeds import JobPosting


@pytest.mark.asyncio
async def test_feature_1_sources_discovery_and_queue(monkeypatch):
    await init_db()

    async def fake_fetch(client, url, source, company=None):
        return [JobPosting(
            source=source, source_kind="WWR", external_id="t-1", title="Backend Engineer",
            company="Acme Feature Test", url="https://example.com/job/1", apply_url="https://example.com/job/1/apply",
            location="Anywhere in the World", remote=True, regions=[], description="Build services in Haskell.",
            posted_at=datetime.utcnow() - timedelta(days=10),
        )]

    monkeypatch.setattr("apps.api.services.discovery_service.fetch_postings", fake_fetch)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.put("/api/intake", json={"targeting": {"target_titles": ["Backend Engineer"], "min_salary": None},
                                             "identity": {"country": "India"}})

        # 1. Default sources: job boards + verified company boards, nothing pretends to have run
        platforms = (await client.get("/api/platforms")).json()
        names = {p["name"]: p for p in platforms}
        assert {"Remote OK", "GitLab", "PostHog"} <= set(names)
        assert any(n.startswith("We Work Remotely") for n in names)
        wellfound = next(p for p in platforms if "wellfound.com" in p["url"])
        assert wellfound["status"] == "NEEDS_LOGIN"
        assert names["GitLab"]["category"] == "COMPANY_BOARD"
        assert all("has_password" not in p for p in platforms)

        # 2. Adding a source: supported board URLs only
        bad = await client.post("/api/platforms", json={"name": "Random", "url": "https://example.com/careers"})
        assert bad.status_code == 400
        res = await client.post("/api/platforms", json={"name": "Acme Board", "url": "https://jobs.ashbyhq.com/acme-feature-test"})
        assert res.status_code == 200
        platform = res.json()
        assert platform["category"] == "COMPANY_BOARD" and platform["added_by"] == "USER"
        dup = await client.post("/api/platforms", json={"name": "Again", "url": "https://jobs.ashbyhq.com/acme-feature-test/"})
        assert dup.status_code == 400

        # 3. Run discovery for that source
        run = (await client.post(f"/api/platforms/{platform['id']}/scrape")).json()
        assert run["platforms_run"] == 1 and run["fetched"] == 1 and run["new"] == 1 and run["maybe"] == 1
        maybe = (await client.get("/api/opportunities", params={"status": "MAYBE"})).json()
        opp = next(o for o in maybe if o["company_name"] == "Acme Feature Test")
        assert opp["raw_metadata"]["score_breakdown"]["title"] == 25

        # 4. Queue it by hand; a second queue is a duplicate
        res_apply = await client.post(f"/api/opportunities/{opp['id']}/human-apply")
        assert res_apply.status_code == 200 and res_apply.json()["status"] == "QUEUED"
        assert (await client.post(f"/api/opportunities/{opp['id']}/human-apply")).status_code == 409

        # 5. Running again doesn't duplicate the job
        again = (await client.post(f"/api/platforms/{platform['id']}/scrape")).json()
        assert again["new"] == 0

        await client.delete(f"/api/platforms/{platform['id']}")


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
