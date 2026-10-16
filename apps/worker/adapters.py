"""
OpportunityOS — ATS adapters.

An adapter knows one applicant-tracking system's application form: where the form lives,
which field ids/names map to which answer-bank keys, and what its confirmation looks like.
Field knowledge comes from reading real Greenhouse and Lever forms (2026-10). Anything an
adapter does not know falls back to label matching in the answer bank.
"""

import re
from typing import Dict, List, Optional

from packages.answer_bank import FormField

DEFAULT_CONFIRMATION = re.compile(
    r"thank(s| you) for (applying|your application|your interest)|application (has been |was )?(received|submitted)"
    r"|we('ve| have) received your application|successfully (submitted|applied)",
    re.I,
)


class AtsAdapter:
    name = "GENERIC"
    confirmation = DEFAULT_CONFIRMATION
    confirmation_url: Optional[re.Pattern] = None

    def matches(self, url: str) -> bool:
        return True

    def form_url(self, url: str) -> str:
        return url

    def key_hint(self, field: FormField) -> Optional[str]:
        """Answer-bank key for a field this ATS always names the same way; "" = never fill."""
        return None

    def is_confirmed(self, url: str, page_text: str) -> bool:
        if self.confirmation_url and self.confirmation_url.search(url or ""):
            return True
        return bool(self.confirmation.search(page_text or ""))


class GreenhouseAdapter(AtsAdapter):
    """job-boards.greenhouse.io / boards.greenhouse.io, and company sites embedding it (gh_jid)."""
    name = "GREENHOUSE"
    confirmation_url = re.compile(r"/confirmation\b", re.I)
    _ids: Dict[str, str] = {
        "first_name": "first_name",
        "last_name": "last_name",
        "preferred_name": "preferred_name",
        "email": "email",
        "phone": "phone",
        "resume": "resume",
        "cover_letter": "cover_letter",
        "candidate-location": "city",
        "country": "country",
        "gender": "eeo_gender",
        "hispanic_ethnicity": "eeo_race",
        "race": "eeo_race",
        "veteran_status": "eeo_veteran",
        "disability_status": "eeo_disability",
    }

    def matches(self, url: str) -> bool:
        return bool(re.search(r"greenhouse\.io|[?&]gh_jid=", url or "", re.I))

    def key_hint(self, field: FormField) -> Optional[str]:
        return self._ids.get(field.element_id)


class LeverAdapter(AtsAdapter):
    name = "LEVER"
    confirmation_url = re.compile(r"/thanks\b", re.I)
    _names: Dict[str, str] = {
        "name": "full_name",
        "email": "email",
        "phone": "phone",
        "location": "city",
        "org": "current_company",
        "resume": "resume",
        "comments": "cover_letter",
        "urls[LinkedIn]": "linkedin_url",
        "urls[GitHub]": "github_url",
        "urls[Portfolio]": "portfolio_url",
        "urls[Other]": "portfolio_url",
        "urls[Twitter]": "",
    }

    def matches(self, url: str) -> bool:
        return "jobs.lever.co" in (url or "").lower()

    def form_url(self, url: str) -> str:
        base = url.split("?")[0].rstrip("/")
        return base if base.endswith("/apply") else base + "/apply"

    def key_hint(self, field: FormField) -> Optional[str]:
        return self._names.get(field.name)


class AshbyAdapter(AtsAdapter):
    """URL handling only; Ashby's form did not render for inspection, so fields use label matching."""
    name = "ASHBY"

    def matches(self, url: str) -> bool:
        return "jobs.ashbyhq.com" in (url or "").lower()

    def form_url(self, url: str) -> str:
        base = url.split("?")[0].rstrip("/")
        return base if base.endswith("/application") else base + "/application"


ADAPTERS: List[AtsAdapter] = [GreenhouseAdapter(), LeverAdapter(), AshbyAdapter()]


def detect_adapter(url: str) -> AtsAdapter:
    return next((a for a in ADAPTERS if a.matches(url)), AtsAdapter())
