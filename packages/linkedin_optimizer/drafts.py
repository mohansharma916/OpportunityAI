"""
Grounded profile drafts. Every draft is built only from facts the candidate gave us
(intake, work history, skills); nothing is invented. Claude can polish the text
(packages/ai/claude_drafter.py), but these templates always work offline.

apply_mode AGENT  = the worker types it into LinkedIn after approval (headline, About)
apply_mode MANUAL = copy-ready text plus where to paste it; the candidate applies it
"""

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from packages.linkedin_optimizer.audit import ABOUT_LIMIT, HEADLINE_LIMIT
from packages.linkedin_optimizer.snapshot import ProfileSnapshot


class Draft(BaseModel):
    section: str
    title: str
    current: Optional[str] = None
    proposed: str
    alternatives: List[str] = Field(default_factory=list)
    rationale: str = ""
    apply_mode: str = "MANUAL"
    char_limit: Optional[int] = None
    instructions: Optional[str] = None
    generated_by: str = "TEMPLATE"


class CandidateFacts(BaseModel):
    """The only material drafts may draw on."""
    full_name: str = ""
    email: Optional[str] = None
    target_titles: List[str] = Field(default_factory=list)
    positioning: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    years_experience: Optional[float] = None
    wins: List[str] = Field(default_factory=list)  # quantified achievements, verbatim
    experiences: List[Dict[str, Any]] = Field(default_factory=list)  # company, role, achievements, technologies
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None


def _clip(text: str, limit: int) -> str:
    text = re.sub(r"\s+\|\s+$", "", text.strip())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" |·,-")


def _ranked_skills(facts: CandidateFacts, keywords: List[str]) -> List[str]:
    """Candidate's own skills, ordered by how often target roles ask for them."""
    have = {s.lower(): s for s in facts.skills}
    ranked = [have[k.lower()] for k in keywords if k.lower() in have]
    return ranked + [s for s in facts.skills if s not in ranked]


def headline_options(facts: CandidateFacts, keywords: List[str]) -> List[str]:
    title = facts.target_titles[0] if facts.target_titles else "Software Engineer"
    stack = _ranked_skills(facts, keywords)[:4]
    options = []
    if stack:
        options.append(f"{title} | {', '.join(stack[:3])} | {facts.positioning or 'Building reliable software'} | Remote")
        options.append(f"{title} · {' · '.join(stack)} · Open to remote roles")
    if facts.positioning:
        options.append(f"{title} | {facts.positioning} | Remote")
    if len(facts.target_titles) > 1 and stack:
        options.append(f"{facts.target_titles[0]} / {facts.target_titles[1]} | {', '.join(stack[:3])} | Remote")
    seen, out = set(), []
    for o in options:
        o = _clip(o, HEADLINE_LIMIT)
        if o not in seen:
            seen.add(o)
            out.append(o)
    return out[:3]


def about_draft(facts: CandidateFacts, keywords: List[str]) -> Optional[str]:
    stack = _ranked_skills(facts, keywords)[:8]
    if not (facts.positioning or facts.wins or stack):
        return None
    title = facts.target_titles[0] if facts.target_titles else None
    parts = []
    hook = facts.positioning or (f"I'm a {title}" if title else "")
    if hook:
        years = f" {facts.years_experience:g} years of experience." if facts.years_experience else ""
        parts.append(f"{hook.rstrip('.')}.{years}")
    if facts.wins:
        parts.append("Recent results:\n" + "\n".join(f"• {w.rstrip('.')}" for w in facts.wins[:4]))
    if stack:
        parts.append("Stack: " + ", ".join(stack) + ".")
    if facts.topics:
        parts.append("I write about " + ", ".join(facts.topics[:3]) + ".")
    if facts.target_titles:
        parts.append(f"Looking for: {', '.join(facts.target_titles[:3])} roles, fully remote.")
    if facts.email:
        parts.append(f"Reach me at {facts.email}.")
    return _clip("\n\n".join(parts), ABOUT_LIMIT)


def experience_drafts(snapshot: ProfileSnapshot, facts: CandidateFacts) -> List[Draft]:
    drafts = []
    by_company = {(e.get("company") or "").lower(): e for e in facts.experiences}
    for role in snapshot.experiences[:5]:
        source = by_company.get(role.company.lower())
        achievements = [a for a in (source or {}).get("achievements") or [] if a]
        if not achievements:
            continue
        bullets = "\n".join(f"• {a.rstrip('.')}" for a in achievements[:5])
        tech = (source or {}).get("technologies") or []
        if tech:
            bullets += f"\n\nSkills: {', '.join(tech[:8])}"
        drafts.append(Draft(
            section="experience",
            title=f"{role.title} at {role.company}",
            current=role.description or None,
            proposed=bullets,
            rationale="Achievement bullets from your work history; recruiters skim for verb + metric + tool.",
            instructions="Profile > Experience > pencil on this role > Description. Paste, then Save.",
        ))
    return drafts


def build_drafts(
    snapshot: ProfileSnapshot,
    facts: CandidateFacts,
    keywords: List[str],
    missing_keywords: List[str],
) -> List[Draft]:
    drafts: List[Draft] = []

    options = headline_options(facts, keywords)
    if options:
        drafts.append(Draft(
            section="headline", title="Headline", current=snapshot.headline,
            proposed=options[0], alternatives=options[1:], apply_mode="AGENT", char_limit=HEADLINE_LIMIT,
            rationale="Target title + the skills target roles ask for most + Remote, within 220 characters.",
        ))

    about = about_draft(facts, keywords)
    if about:
        drafts.append(Draft(
            section="about", title="About", current=snapshot.about, proposed=about,
            apply_mode="AGENT", char_limit=ABOUT_LIMIT,
            rationale="Hook, quantified wins, stack, what you want next, and a call to action.",
        ))

    drafts.extend(experience_drafts(snapshot, facts))

    ranked = _ranked_skills(facts, keywords)
    if ranked:
        listed = {s.lower() for s in snapshot.skills}
        to_add = [s for s in ranked if s.lower() not in listed]
        text = "Pin as top 3: " + ", ".join(ranked[:3])
        if to_add:
            text += "\nAdd (you have these, they're not on LinkedIn yet): " + ", ".join(to_add[:20])
        drafts.append(Draft(
            section="skills", title="Skills", current=", ".join(snapshot.skills[:10]) or None, proposed=text,
            rationale="Ordered by how often your target roles ask for them. Only skills you already have.",
            instructions="Profile > Skills > + to add; use the pencil > reorder to pin the top 3.",
        ))

    if facts.target_titles and snapshot.open_to_work is not True:
        drafts.append(Draft(
            section="open_to_work", title="Open to Work",
            proposed=f"Job titles: {', '.join(facts.target_titles[:5])}\nLocation type: Remote\n"
                     f"Visibility: Recruiters only",
            rationale="Recruiter-only visibility keeps it off your public photo frame.",
            instructions="Profile > Open to > Finding a new job. Enter these values.",
        ))

    first_last = re.sub(r"[^a-z0-9]+", "-", facts.full_name.lower()).strip("-")
    if first_last and snapshot.profile_url and first_last not in snapshot.profile_url:
        drafts.append(Draft(
            section="custom_url", title="Custom URL", current=snapshot.profile_url,
            proposed=f"linkedin.com/in/{first_last}",
            rationale="Clean URL for resumes and email signatures.",
            instructions="Profile > Edit public profile & URL > Edit your custom URL. Add a suffix if taken.",
        ))

    if snapshot.has_banner is not True and (facts.positioning or ranked):
        line = " · ".join(x for x in [facts.positioning, ", ".join(ranked[:4]), "Open to remote"] if x)
        drafts.append(Draft(
            section="banner", title="Banner text", proposed=line,
            rationale="One line of positioning and stack on a plain background (1584 x 396 px).",
            instructions="Create the image, then Profile > camera icon on the banner > Upload.",
        ))

    featured = [u for u in (facts.github_url, facts.portfolio_url) if u]
    if featured and (snapshot.featured_count or 0) < 2:
        drafts.append(Draft(
            section="featured", title="Featured", proposed="\n".join(featured),
            rationale="Two to four proof-of-work links near the top of the profile.",
            instructions="Profile > Add profile section > Recommended > Add featured > Add a link.",
        ))

    if (snapshot.recommendations_count or 0) < 2 and facts.experiences:
        latest = facts.experiences[0]
        drafts.append(Draft(
            section="recommendations", title="Recommendation request",
            proposed=(
                f"Hi <name>, I'm updating my LinkedIn while I look for {facts.target_titles[0] if facts.target_titles else 'my next'} "
                f"roles. Would you be open to writing a short recommendation about our work together at "
                f"{latest.get('company')}? Happy to return the favour. Thanks!"
            ),
            rationale="Ask 2 to 3 managers or peers; each recommendation adds credibility.",
            instructions="Their profile > More > Request a recommendation. Personalise <name> before sending.",
        ))

    return drafts
