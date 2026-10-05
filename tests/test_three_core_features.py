"""
OpportunityOS — Test Suite for the Three Core Features
1. Job / Project Web Scraper Tool (Platforms list, User & AI additions, Date grouping, User Status tracking, Human-like apply with credentials)
2. LinkedIn Scraper & Selenium-Style Connection Automation (Jobs scraping, Selenium bot execution, Post publisher, Credentials vault)
3. Automated Outreach & Networking CRM (Recruiter directory, 3-step cadences, AI outreach message generation, Sequence advancement)
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

        # 2. User adds a custom platform with credentials
        create_payload = {
            "name": "Wellfound Custom Startups",
            "url": "https://wellfound.com/jobs/startups",
            "category": "STARTUPS",
            "requires_auth": True,
            "auth_username": "candidate@opportunity.ai",
            "auth_password": "supersecretpassword123",
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

        # 7. Apply on behalf of user with human-like automation
        apply_payload = {
            "user_id": "candidate@opportunity.ai",
            "password": "supersecretpassword123",
        }
        res_apply = await client.post(f"/api/opportunities/{opp_id}/human-apply", json=apply_payload)
        assert res_apply.status_code == 200
        apply_result = res_apply.json()
        assert apply_result["success"] is True
        assert apply_result["status"] == "APPLIED"
        assert "confirmation_reference" in apply_result
        assert len(apply_result["steps"]) >= 5


@pytest.mark.asyncio
async def test_feature_2_linkedin_scraper_and_selenium_automation():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Scrape LinkedIn Opportunities
        res_opps = await client.post("/api/linkedin/scrape-opportunities")
        assert res_opps.status_code == 200
        opps_data = res_opps.json()
        assert opps_data["success"] is True
        assert len(opps_data["opportunities"]) >= 1

        # 2. Save and Retrieve LinkedIn Credentials
        creds_payload = {
            "username": "alex.engineer@example.com",
            "password": "linkedinpassword",
            "cookies": "li_at=AQEDAR05189XYZ...",
        }
        res_save_cred = await client.post("/api/linkedin/credentials", json=creds_payload)
        assert res_save_cred.status_code == 200

        res_get_cred = await client.get("/api/linkedin/credentials")
        assert res_get_cred.status_code == 200
        assert res_get_cred.json()["username"] == "alex.engineer@example.com"

        # 3. Run Selenium-Style Connection Automation Bot
        conn_payload = {
            "count": 2,
            "target_role": "VP of Engineering",
            "note_template": "Hi {name}, would love to connect regarding distributed systems!",
        }
        res_bot = await client.post("/api/linkedin/automate-connections", json=conn_payload)
        assert res_bot.status_code == 200
        bot_data = res_bot.json()
        assert bot_data["success"] is True
        assert bot_data["connected_count"] >= 1
        assert len(bot_data["logs"]) >= 4

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


@pytest.mark.asyncio
async def test_feature_3_crm_outreach_and_cadences():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Recruiter Contact
        contact_payload = {
            "company_name": "CloudScale Systems",
            "full_name": "Elena Rostova",
            "role": "Director of Technical Recruiting",
            "email": "elena.rostova@cloudscale.example.com",
            "linkedin_url": "https://linkedin.com/in/elena-rostova",
            "notes": "Hiring for Staff Infrastructure Engineers.",
        }
        res_contact = await client.post("/api/crm/contacts", json=contact_payload)
        assert res_contact.status_code == 200
        contact = res_contact.json()
        contact_id = contact["id"]

        # 2. Generate Personalized AI Outreach Message
        res_outreach = await client.post(
            f"/api/crm/contacts/{contact_id}/generate-outreach",
            json={"tone": "TECHNICAL"},
        )
        assert res_outreach.status_code == 200
        outreach_data = res_outreach.json()
        assert "subject" in outreach_data
        assert "body" in outreach_data
        assert "CloudScale Systems" in outreach_data["subject"]

        # 3. Create 3-Step Automated Outreach Sequence
        seq_payload = {
            "opportunity_id": "general-opp",
            "contact_id": contact_id,
        }
        res_seq = await client.post("/api/crm/sequences", json=seq_payload)
        assert res_seq.status_code == 200
        seq = res_seq.json()
        seq_id = seq["id"]
        assert len(seq["messages"]) == 3

        # 4. Advance Sequence (Dispatch Step 1)
        res_adv = await client.post(f"/api/crm/sequences/{seq_id}/advance")
        assert res_adv.status_code == 200
        adv_data = res_adv.json()
        assert adv_data["success"] is True
        assert adv_data["dispatched_step"] == 1
