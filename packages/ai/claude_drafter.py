"""
OpportunityOS — Claude polish for LinkedIn profile drafts.

Takes the grounded template drafts and asks Claude to rewrite the headline options,
About section and experience bullets from the same facts. Every Claude output is
checked before use: length limits, and no number that is not in the candidate's facts.
Anything that fails the check, errors, or is refused keeps the template text.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Set

import anthropic

from packages.linkedin_optimizer.audit import ABOUT_LIMIT, HEADLINE_LIMIT
from packages.linkedin_optimizer.drafts import CandidateFacts, Draft

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = (
    "You rewrite sections of a job seeker's LinkedIn profile so recruiters hiring for their target "
    "roles find and shortlist them. Use only the facts given in <facts>: do not add employers, job "
    "titles, dates, tools, metrics or any number that is not in the facts. Keep each metric exactly "
    "as written. Write in the first person, plainly and specifically, with no emojis or hashtags and "
    "no filler such as 'passionate', 'results-driven' or 'synergy'. Work the recruiter keywords in "
    "only where the facts support them.\n\n"
    f"Headline options: three distinct options, each at most {HEADLINE_LIMIT} characters, naming the "
    "target title, core stack and that the candidate works remotely.\n"
    f"About: at most {ABOUT_LIMIT} characters. Open with a two-line hook, then quantified results, "
    "stack, the roles wanted next, and end with the contact email if one is given.\n"
    "Experience: for each role listed, 3 to 5 bullets, each starting with a past-tense verb."
)

OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "headline_options": {"type": "array", "items": {"type": "string"}},
        "about": {"type": "string"},
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "bullets": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["company", "bullets"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["headline_options", "about", "experience"],
    "additionalProperties": False,
}


def claude_available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


def numbers_in(text: str) -> Set[str]:
    """Numbers normalised so '6', '6.0' and '1,000' compare equal to their facts."""
    out = set()
    for n in re.findall(r"\d+(?:[.,]\d+)*", text or ""):
        n = n.replace(",", "")
        try:
            out.add(f"{float(n):g}")
        except ValueError:
            out.add(n)
    return out


def is_grounded(text: str, facts_text: str) -> bool:
    """True when every number in `text` also appears in the facts."""
    return numbers_in(text) <= numbers_in(facts_text)


def _company_of(draft: Draft) -> str:
    return draft.title.split(" at ", 1)[-1].strip().lower()


def _build_prompt(facts: CandidateFacts, keywords: List[str], drafts: List[Draft]) -> str:
    current = {d.section: d.current for d in drafts if d.section in ("headline", "about") and d.current}
    roles = [d.title for d in drafts if d.section == "experience"]
    return (
        f"<facts>\n{facts.model_dump_json(indent=2)}\n</facts>\n\n"
        f"<recruiter_keywords>{', '.join(keywords)}</recruiter_keywords>\n\n"
        f"<current_profile>\n{json.dumps(current, indent=2)}\n</current_profile>\n\n"
        f"<experience_roles>\n{json.dumps(roles)}\n</experience_roles>\n\n"
        "Write the headline options, the About section, and bullets for each experience role "
        "(use the company name exactly as it appears after ' at ')."
    )


async def polish_drafts(
    facts: CandidateFacts,
    keywords: List[str],
    drafts: List[Draft],
    client: Optional[anthropic.AsyncAnthropic] = None,
) -> List[Draft]:
    """Return drafts with Claude's grounded rewrites applied; unchanged on any failure."""
    client = client or anthropic.AsyncAnthropic()
    try:
        response = await client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={
                "effort": "medium",
                "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
            },
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_prompt(facts, keywords, drafts)}],
        )
    except anthropic.RateLimitError:
        logger.warning("Claude rate limited; keeping template drafts")
        return drafts
    except anthropic.APIStatusError as exc:
        logger.warning("Claude API error %s; keeping template drafts", exc.status_code)
        return drafts
    except anthropic.APIConnectionError:
        logger.warning("Could not reach Claude; keeping template drafts")
        return drafts

    if response.stop_reason in ("refusal", "max_tokens"):
        logger.warning("Claude stopped with %s; keeping template drafts", response.stop_reason)
        return drafts
    text = next((b.text for b in response.content if b.type == "text"), None)
    try:
        out = json.loads(text or "")
    except json.JSONDecodeError:
        return drafts

    facts_text = facts.model_dump_json() + " ".join(d.current or "" for d in drafts)
    result: List[Draft] = []
    for draft in drafts:
        d = draft.model_copy(deep=True)
        if d.section == "headline":
            options = [
                o.strip() for o in out.get("headline_options") or []
                if o and len(o.strip()) <= HEADLINE_LIMIT and is_grounded(o, facts_text)
            ]
            if options:
                d.alternatives = options[1:] + [draft.proposed] + draft.alternatives
                d.proposed, d.generated_by = options[0], "CLAUDE"
        elif d.section == "about":
            about = (out.get("about") or "").strip()
            if about and len(about) <= ABOUT_LIMIT and is_grounded(about, facts_text):
                d.alternatives = [draft.proposed]
                d.proposed, d.generated_by = about, "CLAUDE"
        elif d.section == "experience":
            match = next(
                (e for e in out.get("experience") or [] if e.get("company", "").strip().lower() == _company_of(d)),
                None,
            )
            bullets = [b.strip().lstrip("•- ") for b in (match or {}).get("bullets") or [] if b.strip()]
            body = "\n".join(f"• {b}" for b in bullets)
            if bullets and is_grounded(body, facts_text):
                d.alternatives = [draft.proposed]
                d.proposed, d.generated_by = body, "CLAUDE"
        result.append(d)
    return result
