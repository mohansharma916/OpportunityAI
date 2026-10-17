"""
OpportunityOS — Drafts the reusable intake answers from the candidate's profile and resume:
"Tell us about yourself" (about 100 and about 300 words) and a "Why this company" template.

Drafts go back to the intake form for the candidate to edit and save; nothing is saved here.
With OPENAI_API_KEY (or ANTHROPIC_API_KEY) set the AI writes them; every AI draft must stay within its length,
use no number that isn't in the facts or resume, and (for the template) keep the {company}
placeholder. Otherwise, or when a check fails, a plain template built from the same facts is used.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from packages.ai.claude_drafter import is_grounded
from packages.ai.llm import structured_json

logger = logging.getLogger(__name__)

FIELDS = ("about_short", "about_long", "why_company_template")
WORD_RANGES = {"about_short": (60, 150), "about_long": (180, 380), "why_company_template": (40, 160)}

SYSTEM_PROMPT = (
    "You write a job seeker's reusable answers for remote job applications. Use only the facts in "
    "<facts> and the resume in <resume>: do not add employers, titles, dates, tools, metrics or any number "
    "that is not there, and keep metrics exactly as written. Write in the first person, plainly and "
    "specifically, with no emojis, no hashtags and no filler such as 'passionate', 'results-driven' or "
    "'synergy'.\n\n"
    "about_short: \"Tell us about yourself\" in about 100 words: current role and focus, years of experience "
    "if given, core stack, one or two concrete results, and the roles wanted next.\n"
    "about_long: the same question in about 300 words, in short paragraphs: background, the most relevant "
    "work and results per role, how the candidate works remotely (async communication, ownership), and "
    "what they want next.\n"
    "why_company_template: \"Why do you want to join us?\" in about 80 words, reusable for any company. "
    "Write the literal placeholders {company} and {role} where the company name and job title go; they are "
    "filled in per application. Tie the candidate's strengths to the role; do not invent anything about the "
    "company."
)

OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {field: {"type": "string"} for field in FIELDS},
    "required": list(FIELDS),
    "additionalProperties": False,
}


def _words(text: str) -> int:
    return len((text or "").split())


def _join(items: List[str], limit: int) -> str:
    items = [i for i in items if i][:limit]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def template_texts(facts: Dict[str, Any]) -> Dict[str, str]:
    """Plain drafts from the facts alone, used without an AI key or when an AI draft fails its checks."""
    experiences = facts.get("experiences") or []
    current = experiences[0] if experiences else {}
    titles = facts.get("target_titles") or []
    skills = _join(facts.get("skills") or [], 6)
    years = facts.get("years_experience")
    wins = facts.get("wins") or []
    target = titles[0] if titles else (current.get("role") or "engineer")

    opener = f"I'm a {current['role']} at {current['company']}" if current.get("role") and current.get("company") \
        else f"I'm a {target}"
    if years:
        opener += f" with {years:g} years of experience" if isinstance(years, (int, float)) else f" with {years} years of experience"
    intro = opener + (f", working mainly with {skills}." if skills else ".")
    win = f"One result I'm proud of: {wins[0].rstrip('.')}." if wins else ""
    positioning = facts["positioning"].rstrip(".") + "." if facts.get("positioning") else ""
    wanted = (f"I'm looking for a remote role as a {_join(titles, 3).replace(' and ', ' or ') or target}, where I can own "
              "work end to end and keep shipping steadily with a distributed team.")
    short = [p for p in (intro, win, positioning, wanted) if p]

    long = [" ".join(p for p in (intro, positioning) if p)]
    for e in experiences[:3]:
        line = f"At {e.get('company')}, as {e.get('role')}, "
        achievements = [a.rstrip(".") for a in e.get("achievements") or []][:3]
        tech = _join(e.get("technologies") or [], 5)
        if achievements:
            line += "I " + "; ".join(a[0].lower() + a[1:] for a in achievements) + "."
        else:
            line += "I worked on the product end to end."
        if tech:
            line += f" The stack included {tech}."
        long.append(line)
    if win and not experiences:
        long.append(win)
    long.append("I work well remotely: I write things down, keep updates async and clear, overlap with other "
                "time zones when needed, and take ownership of what I ship.")
    long.append(wanted)

    why = (f"The {{role}} role at {{company}} matches what I do best: {skills or 'building and shipping reliable software'}. "
           "I want to work on a product people depend on, with a team that writes things down and moves "
           "quickly. I'd bring ownership from design to production, clear async communication, and a habit of "
           "measuring results, and I'd like to grow with {company} as the work gets harder.")
    return {"about_short": " ".join(short), "about_long": "\n\n".join(long), "why_company_template": why}


def _valid(field: str, text: str, facts_text: str) -> bool:
    low, high = WORD_RANGES[field]
    if not low <= _words(text) <= high:
        return False
    if field == "why_company_template" and "{company}" not in text:
        return False
    # Placeholders aside, every number must come from the facts or resume
    return is_grounded(text.replace("{company}", "").replace("{role}", ""), facts_text)


async def write_intake_texts(
    facts: Dict[str, Any],
    resume_text: str = "",
    use_ai: bool = True,
    client: Any = None,
) -> Dict[str, Dict[str, str]]:
    """Return {field: {"text", "generated_by"}} for the three intake answers."""
    templates = template_texts(facts)
    out = {f: {"text": templates[f], "generated_by": "TEMPLATE"} for f in FIELDS}
    if not use_ai:
        return out

    facts_text = json.dumps(facts, default=str) + "\n" + resume_text
    drafted, by = await structured_json(SYSTEM_PROMPT, (
        f"<facts>\n{json.dumps(facts, default=str, indent=2)}\n</facts>\n\n"
        f"<resume>\n{resume_text[:15000]}\n</resume>\n\n"
        "Write about_short, about_long and why_company_template."
    ), OUTPUT_SCHEMA, "intake_answers", client=client)
    if drafted is None:
        return out
    for field in FIELDS:
        candidate = (drafted.get(field) or "").strip()
        if candidate and _valid(field, candidate, facts_text):
            out[field] = {"text": candidate, "generated_by": by}
        else:
            logger.info("AI draft for %s failed its checks; using the template", field)
    return out

