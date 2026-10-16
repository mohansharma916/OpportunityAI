"""
OpportunityOS — Auto-apply flow: adapters, answer matching, submit guardrails,
the tracker approval workflow (API), the apply runner, and Claude answer suggestions.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import List

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from apps.api.db import get_db, init_db
from apps.api.main import app
from apps.api.models import ApplicationAnswerModel, CandidateIntakeModel, TrackedApplicationModel
from apps.api.services.intake_service import IntakeService
from apps.api.services.tracker_service import TrackerService
from apps.worker.adapters import GreenhouseAdapter, LeverAdapter, detect_adapter
from apps.worker.apply_runner import SkipRow, run_row
from apps.worker.automation import DetectedField, FormAutomationWorker, HumanPacer, answers_fingerprint
from packages.ai.claude_answers import suggest_answers
from packages.answer_bank import AnswerBank, FormField, pick_option

INTAKE = {
    "identity": {"full_name": "Priya Raman", "email": "priya@example.com", "phone": "+91 98765 43210",
                 "city": "Bengaluru", "country": "India", "linkedin_url": "https://linkedin.com/in/priya"},
    "documents": {"master_resume_path": "/tmp/resume.pdf"},
    "screening": {"needs_sponsorship": False},
}
BANK = AnswerBank.from_intake(INTAKE, profile={"current_company": "Acme"})


async def _no_sleep(_):
    return None


PACER = HumanPacer(sleep=_no_sleep)


def test_adapters_and_key_hints():
    assert detect_adapter("https://job-boards.greenhouse.io/gitlab/jobs/1").name == "GREENHOUSE"
    assert detect_adapter("https://acme.com/careers?gh_jid=123").name == "GREENHOUSE"
    assert detect_adapter("https://example.com/jobs/1").name == "GENERIC"
    lever = LeverAdapter()
    assert lever.form_url("https://jobs.lever.co/acme/abc") == "https://jobs.lever.co/acme/abc/apply"
    assert lever.form_url("https://jobs.lever.co/acme/abc/apply") == "https://jobs.lever.co/acme/abc/apply"

    # Lever names its fields; Greenhouse its ids. Both "Attach" file inputs on Greenhouse are told apart by id.
    org = FormField(label="Current company", name="org")
    org.key_hint = lever.key_hint(org)
    assert BANK.match(org).value == "Acme"
    twitter = FormField(label="Twitter URL", name="urls[Twitter]")
    twitter.key_hint = lever.key_hint(twitter)
    assert BANK.match(twitter) is None
    gh = GreenhouseAdapter()
    resume = FormField(label="Attach", input_type="file", element_id="resume")
    cover = FormField(label="Attach", input_type="file", element_id="cover_letter")
    resume.key_hint, cover.key_hint = gh.key_hint(resume), gh.key_hint(cover)
    assert BANK.match(resume).value == "/tmp/resume.pdf"
    assert BANK.match(cover) is None


def test_option_picking_from_real_forms():
    countries = ["British Indian Ocean Territory", "India +91", "Indonesia +62"]
    assert pick_option("India", countries) == "India +91"
    visas = ["No", "Yes, EU Blue Card", "Yes, but not one of the visas listed here"]
    assert pick_option("No", visas) == "No"
    assert pick_option("Decline to answer", ["Male", "Female", "Decline To Self Identify"]) == "Decline To Self Identify"
    # Comboboxes: with options -> a choice, without (async search) -> typed
    assert BANK.match(FormField(label="Country", input_type="combobox", options=countries)).kind == "choice"
    assert BANK.match(FormField(label="Location (City)", input_type="combobox")).kind == "search"
    assert BANK.match(FormField(label="(city, country) ✱")).value == "Bengaluru, India"


class FakeDriver:
    def __init__(self, fields: List[DetectedField], confirm_after: int = 0, captcha_after_submit: bool = False):
        self.fields, self.confirm_after, self.captcha_after_submit = fields, confirm_after, captcha_after_submit
        self.submitted, self.polls = False, 0
        self.adapter_name = "GREENHOUSE"

    async def goto(self, url): pass
    async def detect_blockers(self): return ["captcha"] if (self.submitted and self.captcha_after_submit) else []
    async def list_fields(self): return self.fields
    async def open_application_form(self): return False
    async def fill(self, field, answer, typing_delay_ms): pass
    async def screenshot(self, path: Path): path.write_bytes(b"png")
    async def click_submit(self):
        self.submitted = True
        return True
    async def confirmation_detected(self):
        if not self.submitted:
            return False
        self.polls += 1
        return self.confirm_after >= 0 and self.polls > self.confirm_after


def _fields():
    return [DetectedField(ref="a", frame_index=0, label="Email", required=True),
            DetectedField(ref="b", frame_index=0, label="Phone")]


URL = "https://job-boards.greenhouse.io/acme/jobs/1"


@pytest.mark.asyncio
async def test_submit_requires_matching_fingerprint(tmp_path):
    dry = await FormAutomationWorker(FakeDriver(_fields()), pacer=PACER, evidence_dir=tmp_path).apply(URL, BANK)
    assert dry.status == "FILLED" and dry.adapter == "GREENHOUSE"
    assert [f["key"] for f in dry.fields] == ["email", "phone"]
    assert dry.fingerprint == answers_fingerprint(dry.fields)

    changed = await FormAutomationWorker(FakeDriver(_fields()), pacer=PACER, evidence_dir=tmp_path).apply(
        URL, BANK, submit=True, expected_fingerprint="something-else")
    assert changed.step_reached == "FORM_CHANGED"

    driver = FakeDriver(_fields())
    ok = await FormAutomationWorker(driver, pacer=PACER, evidence_dir=tmp_path).apply(
        URL, BANK, submit=True, expected_fingerprint=dry.fingerprint)
    assert ok.status == "SUBMITTED" and driver.submitted


@pytest.mark.asyncio
async def test_captcha_after_submit_waits_for_candidate(tmp_path):
    calls = []

    async def announce():
        calls.append(1)

    driver = FakeDriver(_fields(), confirm_after=5, captcha_after_submit=True)
    res = await FormAutomationWorker(driver, pacer=PACER, evidence_dir=tmp_path, on_captcha=announce).apply(URL, BANK, submit=True)
    assert res.status == "SUBMITTED" and res.needs_captcha_solved and calls == [1]

    never = FakeDriver(_fields(), confirm_after=-1, captcha_after_submit=True)
    res = await FormAutomationWorker(never, pacer=PACER, evidence_dir=tmp_path, captcha_wait_s=10).apply(URL, BANK, submit=True)
    assert res.status == "NEEDS_CANDIDATE" and "CAPTCHA" in res.details


# ---------------------------------------------------------------------------
# Tracker workflow
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db():
    await init_db()
    async for session in get_db():
        for m in (TrackedApplicationModel, CandidateIntakeModel):
            await session.execute(delete(m))
        await session.execute(delete(ApplicationAnswerModel).where(ApplicationAnswerModel.source == "CANDIDATE"))
        await session.commit()
        await IntakeService.update(session, {**INTAKE, "targeting": {"daily_cap": 5}})
        yield session
        break


def _run(status, fields=None, unanswered=None, step="X"):
    fields = fields or [{"label": "Email", "value": "priya@example.com", "key": "email", "source": "bank"}]
    return {"status": status, "step_reached": step, "details": "d", "adapter": "GREENHOUSE", "fields": fields,
            "unanswered_fields": unanswered or [], "fingerprint": answers_fingerprint(fields), "screenshots": []}


QUESTION = {"label": "Have you previously worked at Acme?*", "type": "combobox", "options": ["Yes", "No"],
            "canonical": "have_you_previously_worked_at_acme"}


@pytest.mark.asyncio
async def test_tracker_workflow_api(db, tmp_path):
    row = await TrackerService.create(db, {"company": "Acme", "role": "Backend Engineer", "job_url": URL})
    suggestion = {"have_you_previously_worked_at_acme": {"answer": "No", "confidence": "high", "basis": "work history"}}
    await TrackerService.record_run(db, row.id, _run("NEEDS_CANDIDATE", unanswered=[QUESTION]), suggestions=suggestion)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        paused = (await client.get("/api/tracker")).json()[0]
        assert paused["status"] == "PAUSED" and paused["next_action"] == "Answer the open questions"
        assert paused["form"]["unanswered"][0]["suggestion"]["answer"] == "No"

        assert (await client.post(f"/api/tracker/{row.id}/approve")).status_code == 400  # nothing filled yet
        bad = await client.post(f"/api/tracker/{row.id}/answers", json={"answers": {"not_a_question": "x"}})
        assert bad.status_code == 400

        ans = (await client.post(f"/api/tracker/{row.id}/answers",
                                 json={"answers": {"have_you_previously_worked_at_acme": "No"}})).json()
        assert ans["status"] == "QUEUED" and ans["form"]["manual_answers"] == 1
        saved = (await db.execute(select(ApplicationAnswerModel).where(
            ApplicationAnswerModel.question_canonical == "have_you_previously_worked_at_acme"))).scalar_one()
        assert saved.answer_text == "No" and saved.is_verified
        # The next fill of any form asking this question uses the saved answer
        bank = await IntakeService.build_answer_bank(db)
        assert bank.match(FormField(label=QUESTION["label"], input_type="combobox", options=["Yes", "No"])).value == "No"

        await TrackerService.record_run(db, row.id, _run("FILLED", step="AWAITING_APPROVAL"))
        approved = (await client.post(f"/api/tracker/{row.id}/approve")).json()
        assert approved["status"] == "APPROVED"
        assert approved["form"]["approved_fingerprint"] == approved["form"]["fingerprint"]

        # Evidence is served only from the evidence folder
        row_db = await TrackerService.get(db, row.id)
        row_db.evidence = ["/etc/hosts"]
        await db.commit()
        assert (await client.get(f"/api/tracker/{row.id}/evidence/0")).status_code == 404
        assert (await client.get(f"/api/tracker/{row.id}/evidence/5")).status_code == 404

        # Follow-ups
        await TrackerService.update(db, row.id, {"status": "SUBMITTED",
                                                 "submitted_at": (datetime.utcnow() - timedelta(days=8)).isoformat(),
                                                 "next_action_due": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                                                 "contact_name": "Ravi K"})
        due = (await client.get("/api/tracker/follow-ups")).json()
        assert len(due) == 1 and due[0]["message"].startswith("Hi Ravi, I applied for the Backend Engineer role at Acme 8 days ago")
        assert due[0]["message"].endswith("— Priya Raman")
        first = (await client.post(f"/api/tracker/{row.id}/follow-up", json={"note": "emailed"})).json()
        assert first["follow_ups"] == 1 and first["next_action"] == "Follow up again" and "followed up — emailed" in first["notes"]
        second = (await client.post(f"/api/tracker/{row.id}/follow-up", json={})).json()
        assert second["next_action_due"] is None and "ghosted" in second["next_action"]
        assert (await client.get("/api/tracker/follow-ups")).json() == []


@pytest.mark.asyncio
async def test_run_row_gating_and_trust(db, tmp_path, monkeypatch):
    monkeypatch.setattr("apps.worker.automation.EVIDENCE_DIR", tmp_path)
    row = await TrackerService.create(db, {"company": "Beta", "role": "Backend Engineer", "job_url": URL,
                                           "apply_channel": "GREENHOUSE"})
    with pytest.raises(SkipRow, match="Not approved"):
        await run_row(db, row, FakeDriver(_fields()), PACER, submit=True)

    dry = await run_row(db, row, FakeDriver(_fields()), PACER, submit=False)
    row = await TrackerService.get(db, row.id)
    assert dry.status == "FILLED" and row.status == "AWAITING_APPROVAL" and row.form["fields"]
    await TrackerService.approve(db, row.id)
    row = await TrackerService.get(db, row.id)
    sent = await run_row(db, row, FakeDriver(_fields()), PACER, submit=True)
    row = await TrackerService.get(db, row.id)
    assert sent.status == "SUBMITTED" and row.status == "SUBMITTED" and row.submitted_at

    # Daily cap
    await IntakeService.update(db, {"targeting": {"daily_cap": 1}})
    other = await TrackerService.create(db, {"company": "Gamma", "role": "Backend Engineer", "job_url": URL})
    other.status, other.form = "APPROVED", {"approved_fingerprint": "x"}
    await db.commit()
    with pytest.raises(SkipRow, match="cap"):
        await run_row(db, other, FakeDriver(_fields()), PACER, submit=True)

    # Trusted ATS: opt-in + 20 clean submissions lets a queued row submit without approval
    await IntakeService.update(db, {"targeting": {"daily_cap": 50, "auto_submit_trusted": True}})
    queued = await TrackerService.create(db, {"company": "Delta", "role": "Backend Engineer", "job_url": URL,
                                              "apply_channel": "GREENHOUSE"})
    assert not await TrackerService.is_trusted(db, "GREENHOUSE", True)
    for i in range(19):
        db.add(TrackedApplicationModel(dedup_key=f"clean-{i}", company=f"C{i}", role="r", status="SUBMITTED",
                                       apply_channel="GREENHOUSE", form={"approved_fingerprint": "f"},
                                       submitted_at=datetime.utcnow() - timedelta(days=3)))
    await db.commit()
    assert await TrackerService.is_trusted(db, "GREENHOUSE", True)
    assert not await TrackerService.is_trusted(db, "GREENHOUSE", False)
    auto = await run_row(db, queued, FakeDriver(_fields()), PACER, submit=True)
    assert auto.status == "SUBMITTED"


class FakeClaude:
    def __init__(self, payload):
        self.payload = payload
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    async def _create(self, **kwargs):
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(self.payload))])


@pytest.mark.asyncio
async def test_claude_suggestions_are_validated():
    questions = [
        QUESTION,
        {"label": "Visa type", "type": "combobox", "options": ["None", "H-1B"], "canonical": "visa_type"},
        {"label": "Why Acme?", "type": "textarea", "options": [], "canonical": "why_acme"},
        {"label": "Biggest team you led?", "type": "text", "options": [], "canonical": "team_size"},
        {"label": "Non-compete?", "type": "combobox", "options": ["Yes", "No"], "canonical": "non_compete"},
    ]
    fake = FakeClaude({"answers": [
        {"canonical": "have_you_previously_worked_at_acme", "answer": "no", "confidence": "high", "basis": "work history"},
        {"canonical": "visa_type", "answer": "L-1", "confidence": "medium", "basis": "?"},          # not an option
        {"canonical": "why_acme", "answer": "I build payment APIs and Acme's platform is where I want to do it.",
         "confidence": "medium", "basis": "experience"},
        {"canonical": "team_size", "answer": "I led a team of 40 engineers.", "confidence": "high", "basis": "?"},  # invented
        {"canonical": "non_compete", "answer": "", "confidence": "low", "basis": "unknown"},
    ]})
    out = await suggest_answers(questions, {"experiences": [{"company": "Globex", "achievements": ["Led 5 engineers"]}]},
                                {"company": "Acme", "title": "Backend Engineer"}, client=fake)
    assert out["have_you_previously_worked_at_acme"]["answer"] == "No"
    assert set(out) == {"have_you_previously_worked_at_acme", "why_acme"}
