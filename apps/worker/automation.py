"""
OpportunityOS — Playwright Browser Automation Worker
Drives the candidate's own persistent Chrome profile, so logins live in the browser and
never in our database.

Guardrails:
- Every answer comes from the AnswerBank; a required field with no answer pauses the run.
- CAPTCHAs, bot checks and login walls are never bypassed; they are handed to the candidate.
  A CAPTCHA that appears on submit is left in the open window for the candidate to solve.
- Nothing is submitted unless the caller passes submit=True (the candidate's approval), and
  then only if the refilled answers match the ones that were approved (fingerprint).
- Human pacing between fields and between applications; a screenshot is kept for every run.
"""

import asyncio
import hashlib
import json
import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Protocol

from pydantic import BaseModel, Field

from apps.worker.adapters import AtsAdapter, detect_adapter
from packages.answer_bank import AnswerBank, FieldAnswer, FormField, canonical_question

OOS_HOME = Path(os.getenv("OPPORTUNITY_OS_HOME", Path.home() / ".opportunity-os"))
BROWSER_PROFILE_DIR = OOS_HOME / "browser-profile"
EVIDENCE_DIR = OOS_HOME / "evidence"

# Long answers are pasted, the way a person pastes a prepared cover note.
_TYPE_MAX_CHARS = 120


class AutomationResult(BaseModel):
    url: str
    status: str  # FILLED, SUBMITTED, NEEDS_CANDIDATE, FAILED
    step_reached: str
    needs_captcha_solved: bool = False
    details: str
    adapter: str = "GENERIC"
    fields_detected: int = 0
    fields_filled: int = 0
    unanswered: List[str] = Field(default_factory=list)
    unanswered_fields: List[Dict[str, Any]] = Field(default_factory=list)
    fields: List[Dict[str, Any]] = Field(default_factory=list)  # what was filled, for the candidate's review
    fingerprint: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)


class HumanPacer:
    """Random, human-scale delays. `sleep` is injectable so tests run instantly."""

    def __init__(
        self,
        min_gap_s: float = 30,
        max_gap_s: float = 120,
        field_gap_s: tuple = (0.6, 2.0),
        typing_delay_ms: tuple = (40, 120),
        sleep: Callable[[float], Awaitable[Any]] = asyncio.sleep,
        rng: Optional[random.Random] = None,
    ):
        self.min_gap_s = min_gap_s
        self.max_gap_s = max_gap_s
        self.field_gap_s = field_gap_s
        self.typing_delay = typing_delay_ms
        self.sleep = sleep
        self.rng = rng or random.Random()

    async def between_applications(self) -> float:
        gap = self.rng.uniform(self.min_gap_s, self.max_gap_s)
        await self.sleep(gap)
        return gap

    async def between_fields(self) -> None:
        await self.sleep(self.rng.uniform(*self.field_gap_s))

    def typing_delay_ms(self) -> int:
        return self.rng.randint(*self.typing_delay)


class DetectedField(FormField):
    """A form control found on the page; `ref` lets the driver find it again."""

    def __init__(self, ref: str, frame_index: int, **kwargs: Any):
        super().__init__(**kwargs)
        self.ref = ref
        self.frame_index = frame_index


class PageDriver(Protocol):
    async def goto(self, url: str) -> None: ...
    async def detect_blockers(self) -> List[str]: ...
    async def list_fields(self) -> List[DetectedField]: ...
    async def open_application_form(self) -> bool: ...
    async def fill(self, field: DetectedField, answer: FieldAnswer, typing_delay_ms: int) -> None: ...
    async def screenshot(self, path: Path) -> None: ...
    async def click_submit(self) -> bool: ...
    async def confirmation_detected(self) -> bool: ...


def answers_fingerprint(fields: List[Dict[str, Any]]) -> str:
    """Stable hash of what would be submitted, so a submit can be checked against the approved fill."""
    items = sorted((f["label"], str(f.get("value"))) for f in fields if f.get("value") is not None)
    return hashlib.sha256(json.dumps(items).encode()).hexdigest()[:16]


class FormAutomationWorker:
    def __init__(
        self,
        driver: PageDriver,
        pacer: Optional[HumanPacer] = None,
        evidence_dir: Optional[Path] = None,
        confirm_wait_s: float = 15,
        captcha_wait_s: float = 300,
        on_captcha: Optional[Callable[[], Awaitable[None]]] = None,
    ):
        self.driver = driver
        self.pacer = pacer or HumanPacer()
        self.evidence_dir = evidence_dir or EVIDENCE_DIR  # looked up at run time so tests can redirect it
        self.confirm_wait_s = confirm_wait_s
        self.captcha_wait_s = captcha_wait_s
        self.on_captcha = on_captcha

    async def _shot(self, label: str, result: AutomationResult) -> None:
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        slug = re.sub(r"[^a-z0-9]+", "-", result.url.lower())[-60:].strip("-")
        path = self.evidence_dir / f"{stamp}-{slug}-{label}.png"
        try:
            await self.driver.screenshot(path)
            result.screenshots.append(str(path))
        except Exception:
            pass  # evidence is best-effort; never fail an application over a screenshot

    async def _blocked(self, result: AutomationResult, step: str) -> bool:
        blockers = await self.driver.detect_blockers()
        if not blockers:
            return False
        result.status = "NEEDS_CANDIDATE"
        result.step_reached = step
        result.needs_captcha_solved = "captcha" in blockers
        result.details = f"Paused for the candidate: {', '.join(blockers)} detected. Solve it in the browser, then resume."
        await self._shot("blocked", result)
        return True

    async def _await_confirmation(self, result: AutomationResult) -> bool:
        waited, announced = 0.0, False
        while True:
            if await self.driver.confirmation_detected():
                return True
            captcha = "captcha" in await self.driver.detect_blockers()
            if captcha and not announced:
                announced, result.needs_captcha_solved = True, True
                if self.on_captcha:
                    await self.on_captcha()
            if waited >= (self.captcha_wait_s if captcha else self.confirm_wait_s):
                return False
            await self.pacer.sleep(2)
            waited += 2

    async def inspect(self, url: str, bank: AnswerBank) -> AutomationResult:
        """Read the form and report what would be filled and what is missing. Types nothing."""
        result = AutomationResult(url=url, status="INSPECTED", step_reached="START", details="")
        await self.driver.goto(url)
        result.adapter = getattr(self.driver, "adapter_name", "GENERIC")
        blockers = await self.driver.detect_blockers()
        fields = await self.driver.list_fields()
        if not fields and not blockers and await self.driver.open_application_form():
            fields = await self.driver.list_fields()
        result.fields_detected = len(fields)
        for f in fields:
            answer = bank.match(f)
            if answer:
                result.fields.append({
                    "label": f.label or f.name, "type": f.input_type, "required": f.required, "key": answer.key,
                    "value": Path(answer.value).name if answer.kind == "file" else answer.value, "source": answer.source,
                })
            elif f.required:
                result.unanswered.append(f.label or f.name)
                result.unanswered_fields.append({"label": f.label or f.name, "type": f.input_type, "options": f.options,
                                                 "canonical": canonical_question(f.label or f.name)})
        result.fields_filled = len(result.fields)
        result.details = (f"{len(fields)} fields: {result.fields_filled} answerable, {len(result.unanswered)} required "
                          f"without an answer" + (f"; blockers: {', '.join(blockers)}" if blockers else ""))
        return result

    async def apply(
        self,
        url: str,
        bank: AnswerBank,
        submit: bool = False,
        expected_fingerprint: Optional[str] = None,
    ) -> AutomationResult:
        result = AutomationResult(url=url, status="FAILED", step_reached="START", details="")
        if not url.startswith(("http://", "https://")):
            result.step_reached = "URL_VALIDATION"
            result.details = "Invalid URL provided."
            return result

        try:
            await self.driver.goto(url)
            result.adapter = getattr(self.driver, "adapter_name", "GENERIC")
            result.step_reached = "PAGE_LOADED"
            if await self._blocked(result, "SECURITY_GATE"):
                return result

            fields = await self.driver.list_fields()
            if not fields and await self.driver.open_application_form():
                if await self._blocked(result, "SECURITY_GATE"):
                    return result
                fields = await self.driver.list_fields()
            result.fields_detected = len(fields)
            if not fields:
                result.status = "NEEDS_CANDIDATE"
                result.step_reached = "FORM_DETECTION"
                result.details = "No application form found on the page."
                await self._shot("no-form", result)
                return result

            for f in fields:
                answer = bank.match(f)
                if answer is None:
                    if f.required:
                        result.unanswered.append(f.label or f.name or f.input_type)
                        result.unanswered_fields.append({
                            "label": f.label or f.name or f.input_type, "type": f.input_type,
                            "options": f.options, "canonical": canonical_question(f.label or f.name),
                        })
                    continue
                await self.driver.fill(f, answer, self.pacer.typing_delay_ms())
                result.fields_filled += 1
                result.fields.append({
                    "label": f.label or f.name, "type": f.input_type, "required": f.required, "key": answer.key,
                    "value": Path(answer.value).name if answer.kind == "file" else answer.value, "source": answer.source,
                })
                await self.pacer.between_fields()

            result.fingerprint = answers_fingerprint(result.fields)
            result.step_reached = "FORM_FILLED"
            await self._shot("filled", result)

            if result.unanswered:
                result.status = "NEEDS_CANDIDATE"
                result.step_reached = "UNKNOWN_QUESTIONS"
                result.details = (
                    f"Filled {result.fields_filled}/{result.fields_detected} fields. "
                    f"No approved answer for: {'; '.join(result.unanswered)}. Add them to the answer bank or answer in the browser."
                )
                return result

            if not submit:
                result.status = "FILLED"
                result.step_reached = "AWAITING_APPROVAL"
                result.details = f"Filled {result.fields_filled}/{result.fields_detected} fields. Not submitted (dry run)."
                return result

            if expected_fingerprint and result.fingerprint != expected_fingerprint:
                result.status = "NEEDS_CANDIDATE"
                result.step_reached = "FORM_CHANGED"
                result.details = "The form or the answers changed since you approved them. Review the new fill before submitting."
                return result
            if await self._blocked(result, "PRE_SUBMIT_SECURITY_GATE"):
                return result
            if not await self.driver.click_submit():
                result.status = "NEEDS_CANDIDATE"
                result.step_reached = "SUBMIT_BUTTON"
                result.details = "Could not identify a single submit button. Submit it in the browser."
                return result

            result.step_reached = "SUBMITTED_CLICK"
            confirmed = await self._await_confirmation(result)
            await self._shot("after-submit", result)
            if confirmed:
                result.status = "SUBMITTED"
                result.step_reached = "CONFIRMED"
                result.details = "Application submitted and confirmation page detected."
            else:
                result.status = "NEEDS_CANDIDATE"
                result.details = (
                    "Submit was clicked but a CAPTCHA was not solved in time. Check the browser."
                    if result.needs_captcha_solved
                    else "Submit was clicked but no confirmation was detected. Check the browser."
                )
            return result
        except Exception as exc:  # surface browser errors as a tracked failure, not a crash
            result.status = "FAILED"
            result.details = f"{type(exc).__name__}: {exc}"
            await self._shot("error", result)
            return result


# ---------------------------------------------------------------------------
# Playwright implementation
# ---------------------------------------------------------------------------

_SCAN_FIELDS_JS = r"""
(frameIndex) => {
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
  };
  const text = (el) => (el ? (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim() : '');
  const labelFor = (el) => {
    if (el.id) {
      const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (l && text(l)) return text(l);
    }
    const by = el.getAttribute('aria-labelledby');
    if (by) {
      const t = by.split(' ').map((id) => text(document.getElementById(id))).join(' ').trim();
      if (t) return t;
    }
    const wrap = el.closest('label');
    if (wrap && text(wrap)) return text(wrap);
    if (el.getAttribute('aria-label')) return el.getAttribute('aria-label');
    const group = el.closest('fieldset, [role="group"], .field, .form-group, .application-question');
    if (group) {
      const head = group.querySelector('legend, label, .label, .application-label');
      if (head && text(head)) return text(head);
    }
    return el.getAttribute('placeholder') || el.getAttribute('name') || '';
  };
  const out = [];
  const seenRadio = new Set();
  let n = 0;
  document.querySelectorAll('input, textarea, select').forEach((el) => {
    let type = (el.tagName === 'SELECT') ? 'select' : (el.tagName === 'TEXTAREA') ? 'textarea' : (el.type || 'text').toLowerCase();
    if (['hidden', 'submit', 'button', 'reset', 'image', 'search', 'password'].includes(type)) return;
    if (el.getAttribute('aria-hidden') === 'true') return;  // e.g. react-select's shadow "required" input
    if (type !== 'file' && !visible(el)) return;
    if (el.disabled || el.readOnly) return;
    if (el.getAttribute('role') === 'combobox') type = 'combobox';
    if (type === 'checkbox' && !el.required) return;  // required consent boxes need the candidate
    const ref = `oos-${frameIndex}-${n++}`;
    if (type === 'radio') {
      if (!el.name || seenRadio.has(el.name)) return;
      seenRadio.add(el.name);
      const radios = Array.from(document.querySelectorAll(`input[type="radio"][name="${CSS.escape(el.name)}"]`));
      radios.forEach((r, i) => r.setAttribute('data-oos-ref', `${ref}-opt${i}`));
      const group = el.closest('fieldset, [role="radiogroup"], .field, .form-group, .application-question');
      const legend = group ? text(group.querySelector('legend, label, .label')) : '';
      out.push({ ref, type, name: el.name, id: el.id || '', label: legend || el.name,
                 required: radios.some((r) => r.required), options: radios.map((r) => labelFor(r)) });
      return;
    }
    el.setAttribute('data-oos-ref', ref);
    const options = type === 'select' ? Array.from(el.options).map((o) => o.text.trim()).filter(Boolean) : [];
    const label = labelFor(el);
    const required = el.required || el.getAttribute('aria-required') === 'true' || /[*✱]\s*$/.test(label);
    out.push({ ref, type, name: el.getAttribute('name') || '', id: el.id || '', label, required, options });
  });
  return out;
}
"""

_BLOCKERS_JS = r"""
() => {
  const found = new Set();
  const box = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return (r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none') ? r : null;
  };
  for (const f of document.querySelectorAll('iframe')) {
    const src = f.getAttribute('src') || '';
    const b = box(f);
    if (!b) continue;
    // Invisible bot checks (reCAPTCHA v3 badge, hCaptcha enclave) are not challenges.
    if (/hcaptcha/i.test(src)) { if (/frame=(challenge|checkbox)/i.test(src) && b.height >= 60) found.add('captcha'); }
    else if (/recaptcha/i.test(src)) {
      if ((/bframe/i.test(src) && b.height >= 100) || (/anchor/i.test(src) && !/size=invisible/i.test(src) && b.height >= 70)) found.add('captcha');
    }
    else if (/challenges\.cloudflare|turnstile/i.test(src)) found.add('captcha');
    else if (/arkoselabs|funcaptcha/i.test(src) && b.height >= 70) found.add('captcha');
  }
  if (document.querySelector('#challenge-form, #cf-challenge-running')) found.add('captcha');
  for (const p of document.querySelectorAll('input[type="password"]')) {
    if (box(p)) { found.add('login'); break; }
  }
  return Array.from(found);
}
"""


class PlaywrightDriver:
    def __init__(self, page: Any, adapter: Optional[AtsAdapter] = None):
        self.page = page
        self.adapter = adapter
        self._form_frame_index = 0

    @property
    def adapter_name(self) -> str:
        return self.adapter.name if self.adapter else "GENERIC"

    def _frames(self) -> List[Any]:
        return list(self.page.frames)

    async def goto(self, url: str) -> None:
        self.adapter = self.adapter or detect_adapter(url)
        await self.page.goto(self.adapter.form_url(url), wait_until="domcontentloaded", timeout=45000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

    async def detect_blockers(self) -> List[str]:
        found: List[str] = []
        for frame in self._frames():
            try:
                found.extend(await frame.evaluate(_BLOCKERS_JS))
            except Exception:
                continue
        return sorted(set(found))

    async def _combobox_options(self, frame: Any, field: DetectedField) -> List[str]:
        loc = frame.locator(f'[data-oos-ref="{field.ref}"]')
        texts: List[str] = []
        try:
            await loc.click(timeout=3000)
            await asyncio.sleep(0.4)
            opts = frame.get_by_role("option")
            for i in range(min(await opts.count(), 400)):
                t = (await opts.nth(i).inner_text()).strip()
                if t:
                    texts.append(t)
        except Exception:
            pass
        finally:
            await self.page.keyboard.press("Escape")
        return texts

    async def list_fields(self) -> List[DetectedField]:
        best: List[DetectedField] = []
        for i, frame in enumerate(self._frames()):
            try:
                raw = await frame.evaluate(_SCAN_FIELDS_JS, i)
            except Exception:
                continue
            fields = [
                DetectedField(
                    ref=r["ref"], frame_index=i, label=r["label"], input_type=r["type"],
                    name=r["name"], required=bool(r["required"]), options=r["options"], element_id=r.get("id", ""),
                )
                for r in raw
            ]
            # The application form is the frame with the most fields (ATS forms are often embedded iframes).
            if len(fields) > len(best):
                best, self._form_frame_index = fields, i
        frame = self._frames()[self._form_frame_index] if best else None
        for f in best:
            if self.adapter:
                f.key_hint = self.adapter.key_hint(f)
            if f.input_type == "combobox" and frame is not None:
                f.options = await self._combobox_options(frame, f)
        return best

    async def open_application_form(self) -> bool:
        name = re.compile(r"^apply( now| for this (job|position|role))?$", re.I)
        button = self.page.get_by_role("link", name=name)
        if await button.count() == 0:
            button = self.page.get_by_role("button", name=name)
        if await button.count() == 0:
            return False
        await button.first.click()
        await self.page.wait_for_load_state("domcontentloaded")
        return True

    async def _fill_combobox(self, frame: Any, loc: Any, answer: FieldAnswer, typing_delay_ms: int) -> None:
        await loc.click()
        if answer.kind == "choice":
            option = frame.get_by_role("option", name=answer.value, exact=True)
            if await option.count() == 0:
                await loc.press_sequentially(answer.value[:40], delay=typing_delay_ms)
                await asyncio.sleep(0.5)
                option = frame.get_by_role("option", name=answer.value, exact=True)
            await option.first.click()
            return
        await loc.press_sequentially(answer.value[:60], delay=typing_delay_ms)  # async search (e.g. location)
        await asyncio.sleep(1.0)
        options = frame.get_by_role("option")
        if await options.count():
            await options.first.click()
        else:
            await loc.press("Enter")

    async def fill(self, field: DetectedField, answer: FieldAnswer, typing_delay_ms: int) -> None:
        frame = self._frames()[field.frame_index]
        if field.input_type == "radio":
            idx = field.options.index(answer.value)
            await frame.locator(f'[data-oos-ref="{field.ref}-opt{idx}"]').check()
            return
        loc = frame.locator(f'[data-oos-ref="{field.ref}"]')
        if answer.kind == "file":
            await loc.set_input_files(answer.value)
        elif field.input_type == "combobox":
            await self._fill_combobox(frame, loc, answer, typing_delay_ms)
        elif field.input_type == "select":
            await loc.select_option(label=answer.value)
        elif field.input_type == "checkbox":
            await loc.check()
        else:
            await loc.click()
            await loc.fill("")
            if len(answer.value) <= _TYPE_MAX_CHARS:
                await loc.press_sequentially(answer.value, delay=typing_delay_ms)
            else:
                await loc.fill(answer.value)

    async def screenshot(self, path: Path) -> None:
        await self.page.screenshot(path=str(path), full_page=True)

    async def click_submit(self) -> bool:
        frame = self._frames()[self._form_frame_index]
        candidates = frame.locator(
            'button[type="submit"], input[type="submit"], button:has-text("Submit application"), button:has-text("Submit")'
        )
        visible = [candidates.nth(i) for i in range(await candidates.count())]
        visible = [c for c in visible if await c.is_visible()]
        if len(visible) != 1:
            return False
        await visible[0].click()
        try:
            await self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        return True

    async def confirmation_detected(self) -> bool:
        adapter = self.adapter or AtsAdapter()
        for frame in self._frames():
            try:
                body = await frame.inner_text("body", timeout=5000)
            except Exception:
                continue
            if adapter.is_confirmed(self.page.url, body):
                return True
        return False


class BrowserSession:
    """
    Opens the candidate's persistent Chrome profile (headed), so existing logins are reused.
    Usage: `async with BrowserSession() as session: page = await session.new_page()`
    """

    def __init__(self, profile_dir: Path = BROWSER_PROFILE_DIR, headless: bool = False, channel: Optional[str] = "chrome"):
        self.profile_dir = profile_dir
        self.headless = headless
        self.channel = channel
        self._pw = None
        self.context = None

    async def __aenter__(self) -> "BrowserSession":
        from playwright.async_api import async_playwright  # imported lazily: API and tests don't need a browser

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self._pw = await async_playwright().start()
        kwargs: Dict[str, Any] = {"headless": self.headless, "no_viewport": True}
        if self.channel:
            kwargs["channel"] = self.channel
        self.context = await self._pw.chromium.launch_persistent_context(str(self.profile_dir), **kwargs)
        return self

    async def new_page(self) -> Any:
        return await self.context.new_page()

    async def wait_until_closed(self) -> None:
        closed = asyncio.Event()
        self.context.on("close", lambda *_: closed.set())
        await closed.wait()

    async def __aexit__(self, *exc: Any) -> None:
        try:
            if self.context:
                await self.context.close()
        finally:
            if self._pw:
                await self._pw.stop()
