"""
OpportunityOS — One structured-output call for every AI feature, on OpenAI or Claude.

Provider: LLM_PROVIDER=openai|anthropic, otherwise OpenAI when OPENAI_API_KEY is set, else Claude
when ANTHROPIC_API_KEY is set, else none (features fall back to templates or pause for the candidate).
OpenAI model: OPENAI_MODEL (default below). The callers check every output against the candidate's
facts, so the provider only changes who writes the draft, not what is allowed through.
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

OPENAI_DEFAULT_MODEL = "gpt-5.4-mini"
CLAUDE_MODEL = "claude-opus-5-5"
LABELS = {"openai": "OpenAI", "anthropic": "Claude"}


def provider() -> Optional[str]:
    """'openai', 'anthropic', or None when no key is configured."""
    chosen = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))
    if chosen in ("openai", "anthropic"):
        return chosen if (has_openai if chosen == "openai" else has_anthropic) else None
    if has_openai:
        return "openai"
    return "anthropic" if has_anthropic else None


def llm_available() -> bool:
    return provider() is not None


def provider_label() -> Optional[str]:
    p = provider()
    return LABELS.get(p) if p else None


async def structured_json(
    system: str,
    prompt: str,
    schema: Dict[str, Any],
    name: str,
    max_tokens: int = 8000,
    client: Any = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """(parsed JSON, generated_by label such as 'OPENAI') or (None, None) on any failure or refusal.

    `client` is an injected client (tests): one with `.chat` is used as OpenAI, otherwise as Anthropic.
    """
    which = ("openai" if hasattr(client, "chat") else "anthropic") if client is not None else provider()
    if which == "openai":
        return await _openai(system, prompt, schema, name, max_tokens, client)
    if which == "anthropic":
        return await _anthropic(system, prompt, schema, max_tokens, client)
    return None, None


def _parse(text: Optional[str]) -> Optional[Dict[str, Any]]:
    try:
        out = json.loads(text or "")
    except json.JSONDecodeError:
        return None
    return out if isinstance(out, dict) else None


async def _openai(system, prompt, schema, name, max_tokens, client) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    import openai

    client = client or openai.AsyncOpenAI()
    try:
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL") or OPENAI_DEFAULT_MODEL,
            max_completion_tokens=max_tokens,
            response_format={"type": "json_schema", "json_schema": {"name": name, "schema": schema, "strict": True}},
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
    except openai.APIStatusError as exc:
        logger.warning("OpenAI API error %s: %s", exc.status_code, exc.message)
        return None, None
    except openai.APIConnectionError:
        logger.warning("Could not reach OpenAI")
        return None, None
    choice = response.choices[0]
    if choice.finish_reason != "stop" or choice.message.refusal:
        logger.warning("OpenAI stopped with %s", choice.message.refusal and "refusal" or choice.finish_reason)
        return None, None
    out = _parse(choice.message.content)
    return (out, "OPENAI") if out is not None else (None, None)


async def _anthropic(system, prompt, schema, max_tokens, client) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    import anthropic

    client = client or anthropic.AsyncAnthropic()
    try:
        response = await client.beta.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}},
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIStatusError as exc:
        logger.warning("Claude API error %s", exc.status_code)
        return None, None
    except anthropic.APIConnectionError:
        logger.warning("Could not reach Claude")
        return None, None
    if response.stop_reason in ("refusal", "max_tokens"):
        logger.warning("Claude stopped with %s", response.stop_reason)
        return None, None
    out = _parse(next((b.text for b in response.content if b.type == "text"), None))
    return (out, "CLAUDE") if out is not None else (None, None)
