"""
LinkedIn profile audit: scores each checklist section of the pivot plan and says what to fix.
Sections that could not be read score as UNKNOWN and are left out of the overall score.
"""

import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field

from packages.linkedin_optimizer.snapshot import ProfileSnapshot

HEADLINE_LIMIT = 220
ABOUT_LIMIT = 2600

# Section weights (sum 100): what recruiters see and search first weighs most.
WEIGHTS = {
    "headline": 20,
    "about": 15,
    "experience": 15,
    "skills": 12,
    "photo": 8,
    "open_to_work": 6,
    "featured": 6,
    "recommendations": 5,
    "custom_url": 4,
    "banner": 4,
    "credentials": 3,
    "location": 2,
}

LABELS = {
    "headline": "Headline",
    "about": "About",
    "experience": "Experience",
    "skills": "Skills",
    "photo": "Profile photo",
    "open_to_work": "Open to Work",
    "featured": "Featured",
    "recommendations": "Recommendations",
    "custom_url": "Custom URL",
    "banner": "Banner",
    "credentials": "Education & certifications",
    "location": "Location",
}


_GENERIC_TITLE_WORDS = {
    "engineer", "developer", "senior", "junior", "lead", "staff", "principal", "software",
    "manager", "head", "and", "the", "remote", "intern", "associate",
}


class SectionAudit(BaseModel):
    key: str
    label: str
    score: Optional[int] = None  # None = unknown
    status: str = "UNKNOWN"  # GOOD, NEEDS_WORK, MISSING, UNKNOWN
    findings: List[str] = Field(default_factory=list)


class AuditReport(BaseModel):
    overall_score: int
    sections: List[SectionAudit]
    keywords: List[str]
    missing_keywords: List[str]
    source: str


def top_keywords(
    opportunities: Iterable[Dict[str, Any]],
    target_titles: List[str],
    limit: int = 15,
) -> List[str]:
    """
    The skills recruiters ask for most in the roles the candidate targets.
    `opportunities` are dicts with title / required_skills / preferred_skills.
    """
    words = {w for t in target_titles for w in re.findall(r"[a-z]+", t.lower()) if len(w) > 2}
    # "Engineer" or "Senior" alone would match every tech role; filter on the specific words.
    title_words = (words - _GENERIC_TITLE_WORDS) or words
    counts: Counter = Counter()
    display: Dict[str, str] = {}
    for opp in opportunities:
        title = (opp.get("title") or "").lower()
        if title_words and not any(w in title for w in title_words):
            continue
        for weight, key in ((2, "required_skills"), (1, "preferred_skills")):
            for skill in opp.get(key) or []:
                norm = skill.strip().lower()
                if norm:
                    counts[norm] += weight
                    display.setdefault(norm, skill.strip())
    return [display[k] for k, _ in counts.most_common(limit)]


def _contains(text: str, keyword: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(keyword.lower()) + r"(?![a-z0-9])", text.lower()) is not None


def _status(score: int, present: bool = True) -> str:
    if not present:
        return "MISSING"
    return "GOOD" if score >= 80 else "NEEDS_WORK"


def _bool_section(key: str, value: Optional[bool], good: str, bad: str, bad_score: int = 0) -> SectionAudit:
    if value is None:
        return SectionAudit(key=key, label=LABELS[key], findings=["Not readable from this source. Run the live profile audit."])
    score = 100 if value else bad_score
    return SectionAudit(key=key, label=LABELS[key], score=score, status=_status(score, bool(value)),
                        findings=[good if value else bad])


def _count_section(key: str, count: Optional[int], target: int, what: str) -> SectionAudit:
    if count is None:
        return SectionAudit(key=key, label=LABELS[key], findings=["Not readable from this source. Run the live profile audit."])
    score = min(100, round(100 * count / target))
    findings = [] if count >= target else [f"{count} {what}; aim for at least {target}."]
    return SectionAudit(key=key, label=LABELS[key], score=score, status=_status(score, count > 0), findings=findings)


def audit_headline(headline: Optional[str], titles: List[str], keywords: List[str]) -> SectionAudit:
    s = SectionAudit(key="headline", label=LABELS["headline"])
    if not headline:
        s.score, s.status, s.findings = 0, "MISSING", ["No headline. It is the most-searched field on the profile."]
        return s
    score, findings = 0, []
    if any(_contains(headline, t) for t in titles):
        score += 35
    else:
        findings.append(f"Name a target title ({', '.join(titles[:2]) or 'set titles in the intake'}).")
    hits = [k for k in keywords if _contains(headline, k)]
    score += min(len(hits), 4) * 10
    if len(hits) < 3:
        missing = [k for k in keywords if k not in hits][:4]
        findings.append(f"Only {len(hits)} recruiter keyword(s); add {', '.join(missing)}." if missing else "Add core stack keywords.")
    if re.search(r"\bremote\b", headline, re.I):
        score += 10
    else:
        findings.append("Say you work remotely, e.g. end with 'Remote'.")
    if 60 <= len(headline) <= HEADLINE_LIMIT:
        score += 15
    else:
        findings.append(f"{len(headline)} characters; use 60 to {HEADLINE_LIMIT}.")
    s.score, s.status, s.findings = score, _status(score), findings
    return s


def audit_about(about: Optional[str], titles: List[str], keywords: List[str], email: Optional[str]) -> SectionAudit:
    s = SectionAudit(key="about", label=LABELS["about"])
    if not about:
        s.score, s.status, s.findings = 0, "MISSING", ["No About section."]
        return s
    score, findings = 0, []
    n = len(about)
    if n >= 1000:
        score += 25
    elif n >= 600:
        score += 15
        findings.append(f"{n} characters; 1,000 to {ABOUT_LIMIT} gives room for wins and stack.")
    else:
        findings.append(f"Only {n} characters; aim for 1,000 to {ABOUT_LIMIT}.")
    numbers = re.findall(r"\d+(?:[.,]\d+)?\s*(?:%|x|k|m|\+)?", about, re.I)
    if len(numbers) >= 3:
        score += 30
    elif numbers:
        score += 20
        findings.append("Add more quantified wins (aim for 3).")
    else:
        findings.append("No numbers. Add 3 quantified wins (%, users, latency, revenue).")
    hits = [k for k in keywords if _contains(about, k)]
    score += round(20 * min(len(hits), 5) / 5)
    if len(hits) < 5:
        findings.append(f"{len(hits)} recruiter keyword(s) in About; aim for 5+.")
    if (email and email.lower() in about.lower()) or re.search(r"reach (me|out)|contact me|@\w", about, re.I):
        score += 15
    else:
        findings.append("End with a call to action and your email.")
    if any(_contains(about, t) for t in titles) or re.search(r"looking for|open to|next role", about, re.I):
        score += 10
    else:
        findings.append("Say what role you want next.")
    s.score, s.status, s.findings = score, _status(score), findings
    return s


def _bullets(description: str) -> List[str]:
    lines = [l.strip(" •-*\t") for l in description.splitlines() if l.strip(" •-*\t")]
    if len(lines) <= 1:
        lines = [x.strip() for x in re.split(r"(?<=[.!?])\s+", description) if len(x.strip()) > 20]
    return lines


def audit_experience(snapshot: ProfileSnapshot, keywords: List[str]) -> SectionAudit:
    s = SectionAudit(key="experience", label=LABELS["experience"])
    roles = snapshot.experiences[:3]
    if not roles:
        s.score, s.status, s.findings = 0, "MISSING", ["No experience entries."]
        return s
    total, findings = 0, []
    for role in roles:
        bullets = _bullets(role.description)
        role_score = 50 if len(bullets) >= 3 else 15 * len(bullets)
        if re.search(r"\d", role.description):
            role_score += 30
        else:
            findings.append(f"{role.title} at {role.company}: no metrics.")
        if any(_contains(role.description, k) for k in keywords):
            role_score += 20
        if len(bullets) < 3:
            findings.append(f"{role.title} at {role.company}: {len(bullets)} bullet(s); aim for 3 to 5.")
        total += role_score
    score = round(total / len(roles))
    s.score, s.status, s.findings = score, _status(score), findings
    return s


def audit_skills(skills: List[str], keywords: List[str]) -> SectionAudit:
    s = SectionAudit(key="skills", label=LABELS["skills"])
    if not skills:
        s.score, s.status, s.findings = 0, "MISSING", ["No skills listed."]
        return s
    score, findings = 0, []
    n = len(skills)
    score += 40 if n >= 30 else 25 if n >= 15 else 10
    if n < 30:
        findings.append(f"{n} skills; LinkedIn allows up to 100, aim for 30+.")
    lowered = {x.lower() for x in skills}
    top = keywords[:10]
    covered = [k for k in top if k.lower() in lowered]
    score += round(60 * len(covered) / len(top)) if top else 30
    missing = [k for k in top if k.lower() not in lowered]
    if missing:
        findings.append(f"Missing in-demand skills (add only ones you have): {', '.join(missing[:6])}.")
    if top and not any(x.lower() in {k.lower() for k in top} for x in skills[:3]):
        findings.append("Your first 3 skills don't match what target roles ask for; reorder them.")
    s.score, s.status, s.findings = score, _status(score), findings
    return s


def audit_custom_url(url: Optional[str]) -> SectionAudit:
    if not url:
        return SectionAudit(key="custom_url", label=LABELS["custom_url"], findings=["Not readable from this source. Run the live profile audit."])
    slug = url.rstrip("/").split("/in/")[-1]
    generated = bool(re.search(r"-[0-9a-f]{6,}$|\d{3,}$", slug))
    score = 40 if generated else 100
    findings = [f"'{slug}' looks auto-generated; claim a clean firstname-lastname URL."] if generated else []
    return SectionAudit(key="custom_url", label=LABELS["custom_url"], score=score, status=_status(score), findings=findings)


def audit_location(location: Optional[str], identity: Dict[str, Any]) -> SectionAudit:
    if location is None:
        return SectionAudit(key="location", label=LABELS["location"], findings=["Not readable from this source."])
    if not location:
        return SectionAudit(key="location", label=LABELS["location"], score=0, status="MISSING", findings=["No location set."])
    country = (identity.get("country") or "").lower()
    if country and country not in location.lower():
        return SectionAudit(key="location", label=LABELS["location"], score=60, status="NEEDS_WORK",
                            findings=[f"Location '{location}' doesn't mention {identity.get('country')} from your intake."])
    return SectionAudit(key="location", label=LABELS["location"], score=100, status="GOOD")


def run_audit(snapshot: ProfileSnapshot, intake: Dict[str, Dict[str, Any]], keywords: List[str]) -> AuditReport:
    identity = intake.get("identity") or {}
    titles = (intake.get("targeting") or {}).get("target_titles") or []

    credentials_count = None
    if snapshot.education_count is not None or snapshot.certifications_count is not None:
        credentials_count = (snapshot.education_count or 0) + (snapshot.certifications_count or 0)

    sections = [
        audit_headline(snapshot.headline, titles, keywords),
        audit_about(snapshot.about, titles, keywords, identity.get("email")),
        audit_experience(snapshot, keywords),
        audit_skills(snapshot.skills, keywords),
        _bool_section("photo", snapshot.has_photo, "Photo present.", "No profile photo. Profiles with photos get far more views."),
        _bool_section("open_to_work", snapshot.open_to_work, "Open to Work is on.",
                      "Turn on Open to Work (recruiters only) with your titles and Remote."),
        _count_section("featured", snapshot.featured_count, 2, "featured item(s)"),
        _count_section("recommendations", snapshot.recommendations_count, 2, "recommendation(s)"),
        audit_custom_url(snapshot.profile_url),
        _bool_section("banner", snapshot.has_banner, "Custom banner present.",
                      "Default banner. Add one with your positioning line and stack.", bad_score=30),
        _count_section("credentials", credentials_count, 1, "education/certification entries"),
        audit_location(snapshot.location, identity),
    ]

    known = [s for s in sections if s.score is not None]
    weight = sum(WEIGHTS[s.key] for s in known)
    overall = round(sum(WEIGHTS[s.key] * s.score for s in known) / weight) if weight else 0

    profile_text = " ".join(
        [snapshot.headline or "", snapshot.about or "", " ".join(snapshot.skills)]
        + [e.description for e in snapshot.experiences]
    )
    missing_keywords = [k for k in keywords if not _contains(profile_text, k)]
    return AuditReport(
        overall_score=overall,
        sections=sections,
        keywords=keywords,
        missing_keywords=missing_keywords,
        source=snapshot.source,
    )
