"""
OpportunityOS — Answer Bank matching & Form Automation Worker guardrail tests.
The worker runs against a fake page driver, so no browser is needed.
"""

from pathlib import Path
from typing import List

import pytest

from apps.worker.automation import AutomationResult, DetectedField, FormAutomationWorker, HumanPacer
from packages.answer_bank import AnswerBank, FormField, classify_label, pick_option

INTAKE = {
    "identity": {
        "full_name": "Priya Raman", "email": "priya@example.com", "phone": "+91 98765 43210",
        "city": "Bengaluru", "country": "India", "linkedin_url": "https://linkedin.com/in/priya",
        "github_url": "https://github.com/priya",
    },
    "targeting": {"min_salary": 60000, "salary_currency": "USD", "disclose_salary": False},
    "documents": {"master_resume_path": "/tmp/resume.pdf", "resume_variants": {"backend-v2": "/tmp/backend.pdf"}},
    "screening": {"work_authorization": "Yes, India", "needs_sponsorship": False, "about_short": "Backend engineer."},
}


@pytest.mark.parametrize("label,key", [
    ("First Name *", "first_name"),
    ("Last name", "last_name"),
    ("Name", "full_name"),
    ("Email address", "email"),
    ("Phone", "phone"),
    ("LinkedIn Profile", "linkedin_url"),
    ("Are you legally authorized to work in the country where this job is located?", "work_authorization"),
    ("Will you now or in the future require visa sponsorship?", "needs_sponsorship"),
    ("How did you hear about us?", "referral_source"),
    ("Why do you want to join Supabase?", "why_company"),
    ("Company name", None),
    ("Describe your favourite data structure", None),
])
def test_classify_label(label, key):
    assert classify_label(label) == key


def test_pick_option():
    assert pick_option("No", ["Select...", "Yes", "No"]) == "No"
    assert pick_option("Decline to answer", ["Male", "Female", "I don't wish to answer"]) == "I don't wish to answer"
    assert pick_option("India", ["United States", "India"]) == "India"
    assert pick_option("Yes", ["Maybe"]) is None


def test_answer_bank_match_rules():
    bank = AnswerBank.from_intake(INTAKE, resume_variant="backend-v2", custom_answers={
        "describe_your_favourite_data_structure": "A B-tree.",
    })
    assert bank.match(FormField(label="First Name")).value == "Priya"
    assert bank.match(FormField(label="Location (City)")).value == "Bengaluru, India"
    assert bank.match(FormField(label="Resume/CV", input_type="file")).value == "/tmp/backend.pdf"
    sponsor = bank.match(FormField(label="Require sponsorship?", input_type="select", options=["Yes", "No"]))
    assert (sponsor.kind, sponsor.value) == ("choice", "No")
    # Salary is not disclosed, so the worker must pause rather than invent one
    assert bank.match(FormField(label="Expected salary")) is None
    # Unknown question with no saved answer -> None; with a saved verified answer -> used
    assert bank.match(FormField(label="What is your favourite colour?")) is None
    assert bank.match(FormField(label="Describe your favourite data structure")).value == "A B-tree."
    assert bank.match(FormField(label="Cover letter", input_type="file")) is None


class FakeDriver:
    def __init__(self, fields: List[DetectedField], blockers=None, confirm=True, submit_ok=True):
        self.fields = fields
        self.blockers = blockers or []
        self.confirm = confirm
        self.submit_ok = submit_ok
        self.filled = {}
        self.submitted = False

    async def goto(self, url): pass
    async def detect_blockers(self): return list(self.blockers)
    async def list_fields(self): return self.fields
    async def open_application_form(self): return False
    async def fill(self, field, answer, typing_delay_ms): self.filled[field.label] = answer.value
    async def screenshot(self, path: Path): path.write_bytes(b"png")
    async def click_submit(self):
        self.submitted = self.submit_ok
        return self.submit_ok
    async def confirmation_detected(self): return self.confirm


def _field(label, input_type="text", required=True, options=None):
    return DetectedField(ref=label, frame_index=0, label=label, input_type=input_type,
                         required=required, options=options or [])


async def _no_sleep(_):
    return None


def _worker(driver, tmp_path):
    return FormAutomationWorker(driver, pacer=HumanPacer(sleep=_no_sleep), evidence_dir=tmp_path)


BANK = AnswerBank.from_intake(INTAKE)
URL = "https://boards.greenhouse.io/acme/jobs/1"


@pytest.mark.asyncio
async def test_dry_run_fills_but_never_submits(tmp_path):
    driver = FakeDriver([_field("First Name"), _field("Email"), _field("Resume", "file"),
                         _field("Favourite colour", required=False)])
    result = await _worker(driver, tmp_path).apply(URL, BANK)
    assert result.status == "FILLED"
    assert result.step_reached == "AWAITING_APPROVAL"
    assert driver.filled == {"First Name": "Priya", "Email": "priya@example.com", "Resume": "/tmp/resume.pdf"}
    assert driver.submitted is False
    assert result.screenshots and Path(result.screenshots[0]).exists()


@pytest.mark.asyncio
async def test_unknown_required_question_pauses(tmp_path):
    driver = FakeDriver([_field("First Name"), _field("Expected salary"), _field("I agree to the privacy policy", "checkbox")])
    result = await _worker(driver, tmp_path).apply(URL, BANK, submit=True)
    assert result.status == "NEEDS_CANDIDATE"
    assert result.step_reached == "UNKNOWN_QUESTIONS"
    assert result.unanswered == ["Expected salary", "I agree to the privacy policy"]
    assert driver.submitted is False


@pytest.mark.asyncio
async def test_captcha_and_login_are_handed_to_candidate(tmp_path):
    driver = FakeDriver([_field("First Name")], blockers=["captcha"])
    result = await _worker(driver, tmp_path).apply(URL, BANK, submit=True)
    assert result.status == "NEEDS_CANDIDATE"
    assert result.needs_captcha_solved is True
    assert driver.filled == {}

    driver = FakeDriver([_field("First Name")], blockers=["login"])
    result = await _worker(driver, tmp_path).apply(URL, BANK)
    assert result.step_reached == "SECURITY_GATE"
    assert result.needs_captcha_solved is False


@pytest.mark.asyncio
async def test_submit_requires_confirmation(tmp_path):
    ok = await _worker(FakeDriver([_field("Email")]), tmp_path).apply(URL, BANK, submit=True)
    assert ok.status == "SUBMITTED"

    unconfirmed = await _worker(FakeDriver([_field("Email")], confirm=False), tmp_path).apply(URL, BANK, submit=True)
    assert unconfirmed.status == "NEEDS_CANDIDATE"

    no_button = await _worker(FakeDriver([_field("Email")], submit_ok=False), tmp_path).apply(URL, BANK, submit=True)
    assert no_button.step_reached == "SUBMIT_BUTTON"


@pytest.mark.asyncio
async def test_no_form_and_bad_url(tmp_path):
    assert (await _worker(FakeDriver([]), tmp_path).apply(URL, BANK)).step_reached == "FORM_DETECTION"
    assert (await _worker(FakeDriver([]), tmp_path).apply("ftp://x", BANK)).step_reached == "URL_VALIDATION"


@pytest.mark.asyncio
async def test_pacer_gaps_stay_in_range():
    slept = []

    async def record(s):
        slept.append(s)

    pacer = HumanPacer(min_gap_s=30, max_gap_s=120, sleep=record)
    for _ in range(20):
        await pacer.between_applications()
    assert all(30 <= s <= 120 for s in slept)
    assert all(40 <= pacer.typing_delay_ms() <= 120 for _ in range(20))
