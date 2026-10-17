"""
OpportunityOS — AI suggestions (OpenAI or Claude) for application questions the answer bank can't answer.

Suggestions are drafts for the candidate to accept or edit; they are never submitted on
their own. Each suggestion is checked: a choice must be one of the form's options, and a
free-text answer may not contain numbers that are not in the candidate's facts.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from packages.ai.llm import structured_json
from packages.ai.claude_drafter import is_grounded
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


def _validate(question: Dict[str, Any], raw: Dict[str, Any], facts_text: str, by: str) -> Optional[Dict[str, Any]]:
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
            "generated_by": by}


async def suggest_answers(
    questions: List[Dict[str, Any]],
    facts: Dict[str, Any],
    job: Dict[str, Any],
    client: Any = None,
) -> Dict[str, Dict[str, Any]]:
    """Return {canonical: suggestion} for the questions the AI could answer from the facts."""
    if not questions:
        return {}
    facts_text = json.dumps(facts, default=str)
    prompt = (
        f"<facts>\n{facts_text}\n</facts>\n\n"
        f"<job>\n{json.dumps({k: job.get(k) for k in ('company', 'title', 'description')}, default=str)[:6000]}\n</job>\n\n"
        f"<questions>\n{json.dumps([{k: q.get(k) for k in ('canonical', 'label', 'type', 'options')} for q in questions])}\n</questions>\n\n"
        "Answer each question by its canonical id."
    )
    out_json, by = await structured_json(SYSTEM_PROMPT, prompt, OUTPUT_SCHEMA, "form_answers", max_tokens=16000,
                                         client=client)
    if out_json is None:
        return {}
    raw_answers = out_json.get("answers") or []

    by_canonical = {q["canonical"]: q for q in questions}
    out: Dict[str, Dict[str, Any]] = {}
    for raw in raw_answers:
        q = by_canonical.get(raw.get("canonical"))
        if q:
            ok = _validate(q, raw, facts_text, by)
            if ok:
                out[q["canonical"]] = ok
    return out
