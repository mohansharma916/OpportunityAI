"""
OpportunityOS — Answer Bank
Maps application form fields to the candidate's pre-approved intake answers.

Rule: an answer is only ever taken from the intake. A field with no mapped
answer returns None, and the caller must pause for the candidate instead of guessing.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FormField:
    label: str
    input_type: str = "text"  # text, email, tel, url, number, textarea, select, radio, checkbox, file
    name: str = ""
    required: bool = False
    options: List[str] = field(default_factory=list)


@dataclass
class FieldAnswer:
    key: str
    value: str
    kind: str = "text"  # text, file, choice


# Ordered: the first rule whose pattern matches the normalized label wins,
# so specific questions come before generic ones ("country" vs "authorized to work in country").
_RULES: List[tuple] = [
    ("resume", r"\b(resume|cv|curriculum vitae)\b"),
    ("cover_letter", r"\bcover\s*(letter|note)\b"),
    ("work_authorization", r"authori[sz]ed to work|work authori[sz]ation|legally (eligible|allowed|permitted)|right to work"),
    ("needs_sponsorship", r"sponsor"),
    ("willing_to_relocate", r"relocat"),
    ("willing_to_travel", r"\btravel\b"),
    ("eeo_gender", r"\bgender\b|\bsex\b"),
    ("eeo_race", r"\brace\b|ethnic|hispanic|latino"),
    ("eeo_veteran", r"veteran"),
    ("eeo_disability", r"disabilit"),
    ("pronouns", r"pronoun"),
    ("first_name", r"\b(first|given)\s*name\b"),
    ("last_name", r"\b(last|family)\s*name\b|\bsurname\b"),
    ("preferred_name", r"\bpreferred\s*name\b"),
    ("full_name", r"^(your\s+)?(full\s+|legal\s+|complete\s+)?name$"),
    ("email", r"e-?mail"),
    ("phone", r"\b(phone|mobile|cell|telephone)\b"),
    ("linkedin_url", r"linkedin"),
    ("github_url", r"github"),
    ("portfolio_url", r"portfolio|personal (web)?site|^website$|\bwebsite\b"),
    ("timezone", r"time\s*zone"),
    ("salary", r"salary|compensation|pay (expectation|range)|desired pay|expected (pay|ctc)|\bctc\b|hourly rate|\brate\b"),
    ("notice_period", r"notice period|start date|when can you start|earliest .*start|availability to start"),
    ("years_experience", r"years? of (professional |relevant |work )?experience|how many years"),
    ("why_company", r"why .*(us|company|join|interested|role|position|apply)"),
    ("about_long", r"tell us about yourself|introduce yourself|about you\b|summary|additional information|anything else"),
    ("referral_source", r"how did you (hear|find|learn)|referr|where did you (hear|find)"),
    ("country", r"\bcountry\b"),
    ("city", r"\b(city|location|where are you (located|based)|current address)\b"),
    ("current_company", r"current (company|employer)"),
    ("current_title", r"current (title|role|position)"),
]

_DECLINE = "Decline to answer"


def normalize_label(label: str) -> str:
    text = (label or "").lower().replace("*", " ")
    text = re.sub(r"\(required\)|\(optional\)", " ", text)
    text = re.sub(r"[^a-z0-9@\-\s/?']", " ", text)
    return re.sub(r"\s+", " ", text).strip(" ?:")


def classify_label(label: str) -> Optional[str]:
    norm = normalize_label(label)
    if not norm:
        return None
    for key, pattern in _RULES:
        if re.search(pattern, norm):
            return key
    return None


def canonical_question(text: str) -> str:
    """Same canonical form ProfileService uses for saved custom answers."""
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", (text or "").lower()).strip("_")
    return clean[:100] or "custom_question"


def _yes_no(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def pick_option(value: str, options: List[str]) -> Optional[str]:
    """Choose the select/radio option that matches an answer, or None if none clearly does."""
    if not value or not options:
        return None
    want = normalize_label(value)
    cleaned = [(opt, normalize_label(opt)) for opt in options]
    for opt, norm in cleaned:
        if norm == want:
            return opt
    if want in ("yes", "no"):
        for opt, norm in cleaned:
            if norm.split(" ")[0] == want:
                return opt
        return None
    if want.startswith("decline"):
        for opt, norm in cleaned:
            if any(w in norm for w in ("decline", "prefer not", "don't wish", "do not wish", "choose not")):
                return opt
        return None
    for opt, norm in cleaned:
        if norm and (want in norm or norm in want):
            return opt
    return None


class AnswerBank:
    def __init__(
        self,
        answers: Dict[str, str],
        resume_path: Optional[str] = None,
        custom_answers: Optional[Dict[str, str]] = None,
    ):
        self.answers = {k: v for k, v in answers.items() if v not in (None, "")}
        self.resume_path = resume_path
        # Verified answers to past custom questions, keyed by canonical question
        self.custom_answers = {k: v for k, v in (custom_answers or {}).items() if v}

    @classmethod
    def from_intake(
        cls,
        intake: Dict[str, Dict[str, Any]],
        profile: Optional[Dict[str, Any]] = None,
        resume_variant: Optional[str] = None,
        cover_note: Optional[str] = None,
        custom_answers: Optional[Dict[str, str]] = None,
    ) -> "AnswerBank":
        identity = intake.get("identity") or {}
        targeting = intake.get("targeting") or {}
        documents = intake.get("documents") or {}
        screening = intake.get("screening") or {}
        profile = profile or {}

        full_name = (identity.get("full_name") or "").strip()
        parts = full_name.split()
        salary = None
        if targeting.get("disclose_salary") and targeting.get("min_salary"):
            salary = f"{targeting['min_salary']} {targeting.get('salary_currency') or ''}".strip()
        city_country = ", ".join(p for p in (identity.get("city"), identity.get("country")) if p)

        answers = {
            "full_name": full_name,
            "first_name": parts[0] if parts else "",
            "last_name": " ".join(parts[1:]) if len(parts) > 1 else "",
            "preferred_name": identity.get("preferred_name") or (parts[0] if parts else ""),
            "pronouns": identity.get("pronouns"),
            "email": identity.get("email"),
            "phone": identity.get("phone"),
            "city": city_country or identity.get("city"),
            "country": identity.get("country"),
            "timezone": identity.get("timezone"),
            "linkedin_url": identity.get("linkedin_url"),
            "github_url": identity.get("github_url"),
            "portfolio_url": identity.get("portfolio_url"),
            "salary": salary,
            "notice_period": targeting.get("notice_period") or targeting.get("earliest_start"),
            "years_experience": _yes_no(targeting.get("years_experience")),
            "work_authorization": screening.get("work_authorization"),
            "needs_sponsorship": _yes_no(screening.get("needs_sponsorship")),
            "willing_to_relocate": _yes_no(screening.get("willing_to_relocate")),
            "willing_to_travel": _yes_no(screening.get("willing_to_travel")),
            "why_company": screening.get("why_company_template"),
            "about_long": screening.get("about_long") or screening.get("about_short"),
            "referral_source": screening.get("referral_source"),
            "eeo_gender": screening.get("eeo_gender") or _DECLINE,
            "eeo_race": screening.get("eeo_race") or _DECLINE,
            "eeo_veteran": screening.get("eeo_veteran") or _DECLINE,
            "eeo_disability": screening.get("eeo_disability") or _DECLINE,
            "current_company": profile.get("current_company"),
            "current_title": profile.get("current_title"),
            "cover_letter": cover_note,
        }

        variants = documents.get("resume_variants") or {}
        resume_path = variants.get(resume_variant) if resume_variant else None
        return cls(
            answers,
            resume_path=resume_path or documents.get("master_resume_path"),
            custom_answers=custom_answers,
        )

    def match(self, form_field: FormField) -> Optional[FieldAnswer]:
        key = classify_label(form_field.label) or classify_label(form_field.name.replace("_", " "))
        if form_field.input_type == "file":
            if key in (None, "resume") and self.resume_path:
                return FieldAnswer("resume", self.resume_path, kind="file")
            return None
        if key == "resume":
            return None
        value = self.answers.get(key) if key else None
        if not value:
            custom_key = canonical_question(form_field.label)
            value = self.custom_answers.get(custom_key)
            key = custom_key if value else key
        if not value:
            return None
        if form_field.input_type in ("select", "radio"):
            option = pick_option(value, form_field.options)
            return FieldAnswer(key, option, kind="choice") if option else None
        return FieldAnswer(key, value)
