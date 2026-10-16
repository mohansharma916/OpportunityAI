"""
OpportunityOS — LinkedIn optimizer: export parsing, keywords, audit, grounded drafts,
Claude polish guardrails, and the draft approval API.
"""

import json
import zipfile
from types import SimpleNamespace

import anthropic
import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from apps.api.db import get_db, init_db
from apps.api.main import app
from apps.api.models import CandidateIntakeModel, LinkedInProfileDraftModel, LinkedInProfileSnapshotModel
from apps.api.services.intake_service import IntakeService
from packages.ai.claude_drafter import is_grounded, polish_drafts
from packages.linkedin_optimizer import (
    CandidateFacts,
    Experience,
    ProfileSnapshot,
    build_drafts,
    parse_export,
    run_audit,
    top_keywords,
)


def _export_zip(tmp_path, headline="Software Engineer", summary="I build things."):
    path = tmp_path / "Basic_LinkedInDataExport.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("Profile.csv",
                    "First Name,Last Name,Maiden Name,Address,Birth Date,Headline,Summary,Industry,Zip Code,Geo Location\n"
                    f'Priya,Raman,,,,"{headline}","{summary}",Software,,"Bengaluru, Karnataka, India"\n')
        zf.writestr("Positions.csv",
                    "Company Name,Title,Description,Location,Started On,Finished On\n"
                    'Acme,Backend Engineer,"Built APIs.",Bengaluru,Jan 2022,\n'
                    'Globex,Software Engineer,,Pune,Jun 2019,Dec 2021\n')
        zf.writestr("Skills.csv", "Name\nPython\nDjango\n")
        zf.writestr("Education.csv", "School Name,Start Date,End Date,Notes,Degree Name,Activities\nIIT,2015,2019,,BTech,\n")
        zf.writestr("Recommendations_Received.csv", "First Name,Last Name,Company,Job Title,Text,Creation Date,Status\n")
    return path


INTAKE = {
    "identity": {"full_name": "Priya Raman", "email": "priya@example.com", "country": "India",
                 "github_url": "https://github.com/priya"},
    "targeting": {"target_titles": ["Backend Engineer"]},
}
KEYWORDS = ["Python", "AWS", "PostgreSQL", "Kubernetes", "FastAPI"]
FACTS = CandidateFacts(
    full_name="Priya Raman", email="priya@example.com", target_titles=["Backend Engineer", "Platform Engineer"],
    positioning="I help fintech teams ship reliable APIs", topics=["API design"],
    skills=["FastAPI", "Python", "PostgreSQL", "Redis"], years_experience=6,
    wins=["Cut p99 latency by 45% for the payments API", "Scaled ingestion to 50M events/day"],
    experiences=[{"company": "Acme", "role": "Backend Engineer",
                  "achievements": ["Cut p99 latency by 45% for the payments API", "Led migration to PostgreSQL 15"],
                  "technologies": ["Python", "FastAPI"]}],
    github_url="https://github.com/priya",
)


def test_parse_export(tmp_path):
    snap = parse_export(str(_export_zip(tmp_path)))
    assert snap.source == "EXPORT"
    assert snap.name == "Priya Raman"
    assert snap.headline == "Software Engineer"
    assert [e.company for e in snap.experiences] == ["Acme", "Globex"]
    assert snap.skills == ["Python", "Django"]
    assert snap.education_count == 1
    assert snap.recommendations_count == 0
    assert snap.has_photo is None and snap.open_to_work is None  # not in exports


def test_parse_export_rejects_other_files(tmp_path):
    bad = tmp_path / "x.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("Connections.csv", "a,b\n")
    with pytest.raises(ValueError, match="Profile.csv"):
        parse_export(str(bad))


def test_top_keywords_weights_required_and_filters_titles():
    opps = [
        {"title": "Senior Backend Engineer", "required_skills": ["Python", "AWS"], "preferred_skills": ["Kafka"]},
        {"title": "Backend Developer", "required_skills": ["Python", "PostgreSQL"], "preferred_skills": ["AWS"]},
        {"title": "iOS Engineer", "required_skills": ["Swift", "Swift", "Swift"]},
    ]
    kws = top_keywords(opps, ["Backend Engineer"])
    assert kws[0] == "Python"
    assert "Swift" not in kws
    assert kws.index("AWS") < kws.index("Kafka")


def test_audit_scores_weak_vs_strong_profile():
    weak = ProfileSnapshot(source="SCREEN", headline="Engineer", about="Hi.", location="Bengaluru, India",
                           profile_url="https://www.linkedin.com/in/priya-raman-4b2a91c7",
                           has_photo=False, has_banner=False, open_to_work=False,
                           experiences=[Experience(title="Engineer", company="Acme", description="Did work")],
                           skills=["Django"], featured_count=0, recommendations_count=0, education_count=1)
    report = run_audit(weak, INTAKE, KEYWORDS)
    by = {s.key: s for s in report.sections}
    assert report.overall_score < 40
    assert by["headline"].status == "NEEDS_WORK"
    assert any("Backend Engineer" in f for f in by["headline"].findings)
    assert by["custom_url"].score == 40
    assert by["photo"].status == "MISSING"
    assert "Python" in report.missing_keywords

    strong = ProfileSnapshot(
        source="SCREEN",
        headline="Backend Engineer | Python, AWS, PostgreSQL, FastAPI | Reliable payments APIs | Remote",
        about=("I help fintech teams ship reliable APIs. " * 20) + "Cut p99 latency by 45%, scaled to 50M events, "
              "saved 30% infra. Python, AWS, PostgreSQL, Kubernetes, FastAPI. Looking for Backend Engineer roles. "
              "Reach me at priya@example.com",
        location="Bengaluru, India", profile_url="https://www.linkedin.com/in/priya-raman",
        has_photo=True, has_banner=True, open_to_work=True,
        experiences=[Experience(title="Backend Engineer", company="Acme",
                                description="• Cut latency 45% with Python\n• Scaled to 50M events on AWS\n• Led PostgreSQL 15 migration")],
        skills=KEYWORDS + [f"skill{i}" for i in range(30)], featured_count=3, recommendations_count=2, education_count=1)
    assert run_audit(strong, INTAKE, KEYWORDS).overall_score >= 90


def test_audit_excludes_unknown_sections():
    snap = ProfileSnapshot(source="EXPORT", headline="Backend Engineer | Python | Remote")
    report = run_audit(snap, INTAKE, KEYWORDS)
    by = {s.key: s for s in report.sections}
    assert by["photo"].score is None and by["photo"].status == "UNKNOWN"
    assert by["open_to_work"].score is None


def test_drafts_are_grounded_and_within_limits():
    snap = ProfileSnapshot(source="SCREEN", headline="Engineer", profile_url="https://linkedin.com/in/pr-12345",
                           experiences=[Experience(title="Backend Engineer", company="Acme")],
                           skills=["Python"], has_banner=False, open_to_work=False, featured_count=0,
                           recommendations_count=0)
    drafts = {d.section: d for d in build_drafts(snap, FACTS, KEYWORDS, [])}
    assert drafts["headline"].apply_mode == "AGENT"
    assert len(drafts["headline"].proposed) <= 220
    assert drafts["headline"].proposed.startswith("Backend Engineer | Python, PostgreSQL, FastAPI")
    assert "45%" in drafts["about"].proposed and "priya@example.com" in drafts["about"].proposed
    facts_text = FACTS.model_dump_json()
    for d in drafts.values():
        assert is_grounded(d.proposed, facts_text + (d.current or "") + "1584 396 top 3"), d.section
    # Skills draft never suggests a skill the candidate doesn't have
    assert "AWS" not in drafts["skills"].proposed and "Kubernetes" not in drafts["skills"].proposed
    assert drafts["custom_url"].proposed == "linkedin.com/in/priya-raman"
    assert drafts["experience"].proposed.startswith("• Cut p99 latency by 45%")
    assert {"open_to_work", "banner", "featured", "recommendations"} <= set(drafts)


class FakeClaude:
    def __init__(self, payload=None, stop_reason="end_turn", exc=None):
        self.payload, self.stop_reason, self.exc = payload, stop_reason, exc
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    async def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self.exc:
            raise self.exc
        return SimpleNamespace(stop_reason=self.stop_reason,
                               content=[SimpleNamespace(type="text", text=json.dumps(self.payload))])


def _template_drafts():
    snap = ProfileSnapshot(source="SCREEN", headline="Engineer", about="Old about",
                           experiences=[Experience(title="Backend Engineer", company="Acme")])
    return build_drafts(snap, FACTS, KEYWORDS, [])


@pytest.mark.asyncio
async def test_claude_polish_keeps_only_grounded_text():
    drafts = _template_drafts()
    fake = FakeClaude({
        "headline_options": ["Backend Engineer | Python & FastAPI | Cut p99 latency 45% | Remote",
                             "Backend Engineer | 10x engineer who saved $2M | Remote"],  # invented numbers
        "about": "I help fintech teams ship reliable APIs. I cut p99 latency by 45%. Reach me at priya@example.com.",
        "experience": [{"company": "Acme", "bullets": ["Cut p99 latency by 45% for the payments API",
                                                       "Led migration to PostgreSQL 15"]}],
    })
    out = {d.section: d for d in await polish_drafts(FACTS, KEYWORDS, drafts, client=fake)}
    call = fake.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["fallbacks"] == "default" and call["betas"] == ["server-side-fallback-2026-07-01"]
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert out["headline"].generated_by == "CLAUDE"
    assert out["headline"].proposed.startswith("Backend Engineer | Python & FastAPI")
    assert all("$2M" not in a for a in out["headline"].alternatives)
    assert out["about"].generated_by == "CLAUDE"
    assert out["experience"].proposed == "• Cut p99 latency by 45% for the payments API\n• Led migration to PostgreSQL 15"


@pytest.mark.asyncio
async def test_claude_polish_rejects_invented_about_and_survives_failures():
    drafts = _template_drafts()
    invented = FakeClaude({"headline_options": [], "about": "I grew revenue 300% at 4 startups.", "experience": []})
    out = {d.section: d for d in await polish_drafts(FACTS, KEYWORDS, drafts, client=invented)}
    assert out["about"].generated_by == "TEMPLATE"

    refused = FakeClaude({"headline_options": ["x"], "about": "y", "experience": []}, stop_reason="refusal")
    assert await polish_drafts(FACTS, KEYWORDS, drafts, client=refused) == drafts

    down = FakeClaude(exc=anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com")))
    assert await polish_drafts(FACTS, KEYWORDS, drafts, client=down) == drafts


@pytest_asyncio.fixture
async def clean_optimizer_tables():
    await init_db()
    async for db in get_db():
        for model in (LinkedInProfileDraftModel, LinkedInProfileSnapshotModel, CandidateIntakeModel):
            await db.execute(delete(model))
        await db.commit()
        await IntakeService.update(db, {
            "identity": {"full_name": "Priya Raman", "email": "priya@example.com", "country": "India"},
            "targeting": {"target_titles": ["Backend Engineer"]},
            "linkedin": {"positioning": "I help fintech teams ship reliable APIs"},
        })
        break
    yield


@pytest.mark.asyncio
async def test_optimizer_api_flow(tmp_path, clean_optimizer_tables):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        empty = await client.post("/api/linkedin/optimizer/analyze?use_claude=false")
        assert empty.status_code == 404

        res = await client.post("/api/linkedin/optimizer/import-export",
                                json={"path": str(_export_zip(tmp_path)), "use_claude": False})
        assert res.status_code == 200
        state = res.json()
        assert state["snapshot"]["source"] == "EXPORT"
        assert 0 < state["audit"]["overall_score"] < 100
        drafts = {d["section"]: d for d in state["drafts"]}
        headline = drafts["headline"]
        assert headline["status"] == "PENDING" and headline["current_value"] == "Software Engineer"

        too_long = await client.post(f"/api/linkedin/optimizer/drafts/{headline['id']}",
                                     json={"decision": "APPROVE", "value": "x" * 221})
        assert too_long.status_code == 400

        ok = await client.post(f"/api/linkedin/optimizer/drafts/{headline['id']}",
                               json={"decision": "APPROVE", "value": "Backend Engineer | Python | Remote"})
        assert ok.json()["status"] == "APPROVED"
        assert ok.json()["proposed_value"] == "Backend Engineer | Python | Remote"

        manual = next(d for d in state["drafts"] if d["apply_mode"] == "MANUAL")
        done = await client.post(f"/api/linkedin/optimizer/drafts/{manual['id']}", json={"decision": "MARK_APPLIED"})
        assert done.json()["status"] == "APPLIED" and done.json()["applied_at"]

        # Re-analysing replaces pending drafts but keeps decisions already made
        again = (await client.post("/api/linkedin/optimizer/analyze?use_claude=false")).json()
        statuses = {d["id"]: d["status"] for d in again["drafts"]}
        assert statuses[headline["id"]] == "APPROVED"
        assert statuses[manual["id"]] == "APPLIED"
        assert sum(1 for d in again["drafts"] if d["section"] == "headline") == 2

        bad = await client.post(f"/api/linkedin/optimizer/drafts/{headline['id']}", json={"decision": "SHIP_IT"})
        assert bad.status_code == 400
