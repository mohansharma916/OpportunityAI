"""
OpportunityOS — Drafting the intake's "about you" and "why this company" answers, and filling the
{company}/{role} placeholders per application.
"""

import json
from types import SimpleNamespace

import pytest

from packages.ai.intake_writer import template_texts, write_intake_texts
from packages.answer_bank import AnswerBank, FormField, fill_placeholders

FACTS = {
    "full_name": "Priya Raman", "target_titles": ["Backend Engineer", "Platform Engineer"],
    "skills": ["Python", "PostgreSQL", "AWS", "Django"], "years_experience": 6,
    "wins": ["Cut API latency by 40%"],
    "experiences": [{"company": "Globex", "role": "Senior Backend Engineer",
                     "achievements": ["Cut API latency by 40%", "Led 5 engineers"], "technologies": ["Python", "AWS"]}],
}


class FakeClaude:
    def __init__(self, payload):
        self.payload = payload
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    async def _create(self, **kwargs):
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(self.payload))])


def test_templates_use_only_the_facts():
    t = template_texts(FACTS)
    assert t["about_short"].startswith("I'm a Senior Backend Engineer at Globex with 6 years of experience")
    assert "40%" in t["about_short"] and "Globex" in t["about_long"]
    assert "{company}" in t["why_company_template"] and "{role}" in t["why_company_template"]
    assert template_texts({})["about_short"]  # an empty profile still gives a starting point


@pytest.mark.asyncio
async def test_claude_drafts_are_checked():
    words = lambda n: " ".join(["word"] * n)
    fake = FakeClaude({
        "about_short": "I'm a backend engineer with 6 years of experience. " + words(70),        # ok
        "about_long": "I led 12 engineers at Globex. " + words(220),                               # 12 is invented
        "why_company_template": "I want to join because " + words(60),                             # no {company}
    })
    out = await write_intake_texts(FACTS, resume_text="", client=fake)
    assert out["about_short"]["generated_by"] == "CLAUDE"
    assert out["about_long"]["generated_by"] == "TEMPLATE"
    assert out["why_company_template"]["generated_by"] == "TEMPLATE"
    # Without Claude: templates only
    assert {v["generated_by"] for v in (await write_intake_texts(FACTS, use_ai=False)).values()} == {"TEMPLATE"}


def test_why_company_placeholders_are_filled_per_application():
    assert fill_placeholders("Join {company} as {role}", "Acme", "SRE") == "Join Acme as SRE"
    assert fill_placeholders("Join {company}", None, None) is None  # can't be filled -> pause, never send "{company}"
    intake = {"screening": {"why_company_template": "I'd like to build at {company} as a {role}."}}
    question = FormField(label="Why do you want to join us?")
    assert AnswerBank.from_intake(intake, company="Acme", role="Backend Engineer").match(question).value == \
        "I'd like to build at Acme as a Backend Engineer."
    assert AnswerBank.from_intake(intake).match(question) is None


class FakeOpenAI:
    """Stands in for openai.AsyncOpenAI: chat.completions.create returning one choice."""

    def __init__(self, payload, finish_reason="stop", refusal=None):
        self.payload, self.finish_reason, self.refusal = payload, finish_reason, refusal
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    async def _create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=json.dumps(self.payload), refusal=self.refusal)
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason=self.finish_reason, message=message)])


@pytest.mark.asyncio
async def test_openai_writes_drafts_with_strict_schema(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    words = lambda n: " ".join(["word"] * n)
    fake = FakeOpenAI({"about_short": "I'm a backend engineer. " + words(70), "about_long": words(250),
                       "why_company_template": "I want to join {company} as {role}. " + words(50)})
    out = await write_intake_texts(FACTS, client=fake)
    assert {v["generated_by"] for v in out.values()} == {"OPENAI"}
    call = fake.calls[0]
    assert call["model"] == "gpt-test"
    assert call["response_format"]["type"] == "json_schema" and call["response_format"]["json_schema"]["strict"] is True
    assert call["messages"][0]["role"] == "system"

    # A refusal or a cut-off answer falls back to the templates
    for bad in (FakeOpenAI({}, refusal="no"), FakeOpenAI({}, finish_reason="length")):
        assert {v["generated_by"] for v in (await write_intake_texts(FACTS, client=bad)).values()} == {"TEMPLATE"}


def test_provider_choice(monkeypatch):
    from packages.ai.llm import provider

    assert provider() is None
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    assert provider() == "anthropic"
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    assert provider() == "openai"  # OpenAI first when both are set
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    assert provider() == "anthropic"
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert provider() is None  # the chosen provider has no key
