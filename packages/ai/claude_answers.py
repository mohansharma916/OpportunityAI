"""
OpportunityOS — Claude suggestions for application questions the answer bank can't answer.

Suggestions are drafts for the candidate to accept or edit; they are never submitted on
their own. Each suggestion is checked: a choice must be one of the form's options, and a
free-text answer may not contain numbers that are not in the candidate's facts.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import anthropic

from packages.ai.claude_drafter import MODEL, is_grounded
from packages.answer_bank import pick_option

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You help a job seeker answer application-form questions. Answer only from the facts in <facts> "
    "and the job in <job>. If the facts don't settle a question (legal agreements, visa details, "
    "anything personal you cannot see), return an empty answer with confidence \"low\" instead of guessing. "
    "For a question with options, the answer must be exactly one of the options. Free-text answers are "
    "first person, specific and under 120 words, with no numbers that are not in the facts. "
    "In `basis`, name the fact you relied on."
)

OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "canonical": {"type": "string"},
                    "answer": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "basis": {"type": "string"},
                },
                "required": ["canonical", "answer", "confidence", "basis"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["answers"],
    "additionalProperties": False,
}


def _validate(question: Dict[str, Any], raw: Dict[str, Any], facts_text: str) -> Optional[Dict[str, Any]]:
    answer = (raw.get("answer") or "").strip()
    if not answer or raw.get("confidence") == "low":
        return None
    if question.get("options"):
        option = pick_option(answer, question["options"])
        if not option:
            return None
        answer = option
    elif len(answer) > 1500 or not is_grounded(answer, facts_text):
        return None
    return {"answer": answer, "confidence": raw.get("confidence"), "basis": (raw.get("basis") or "")[:300],
            "generated_by": "CLAUDE"}


async def suggest_answers(
    questions: List[Dict[str, Any]],
    facts: Dict[str, Any],
    job: Dict[str, Any],
    client: Optional[anthropic.AsyncAnthropic] = None,
) -> Dict[str, Dict[str, Any]]:
    """Return {canonical: suggestion} for the questions Claude could answer from the facts."""
    if not questions:
        return {}
    client = client or anthropic.AsyncAnthropic()
    facts_text = json.dumps(facts, default=str)
    prompt = (
        f"<facts>\n{facts_text}\n</facts>\n\n"
        f"<job>\n{json.dumps({k: job.get(k) for k in ('company', 'title', 'description')}, default=str)[:6000]}\n</job>\n\n"
        f"<questions>\n{json.dumps([{k: q.get(k) for k in ('canonical', 'label', 'type', 'options')} for q in questions])}\n</questions>\n\n"
        "Answer each question by its canonical id."
    )
    try:
        response = await client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.RateLimitError:
        logger.warning("Claude rate limited; no suggestions")
        return {}
    except anthropic.APIStatusError as exc:
        logger.warning("Claude API error %s; no suggestions", exc.status_code)
        return {}
    except anthropic.APIConnectionError:
        logger.warning("Could not reach Claude; no suggestions")
        return {}

    if response.stop_reason in ("refusal", "max_tokens"):
        return {}
    text = next((b.text for b in response.content if b.type == "text"), None)
    try:
        raw_answers = json.loads(text or "").get("answers") or []
    except (json.JSONDecodeError, AttributeError):
        return {}

    by_canonical = {q["canonical"]: q for q in questions}
    out: Dict[str, Dict[str, Any]] = {}
    for raw in raw_answers:
        q = by_canonical.get(raw.get("canonical"))
        if q:
            ok = _validate(q, raw, facts_text)
            if ok:
                out[q["canonical"]] = ok
    return out
