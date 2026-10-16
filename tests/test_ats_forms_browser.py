"""
OpportunityOS — ATS adapters in a real headless browser, against mock pages modelled on live
Greenhouse and Lever forms (2026-10): react-select style comboboxes with hidden "required"
inputs, two "Attach" file inputs, an invisible hCaptcha enclave, Lever's named fields and /apply URL.
Skipped when no Chrome is available.
"""

import functools
import http.server
import threading
from pathlib import Path

import pytest
import pytest_asyncio

playwright_api = pytest.importorskip("playwright.async_api")

from apps.worker.adapters import GreenhouseAdapter, LeverAdapter  # noqa: E402
from apps.worker.automation import FormAutomationWorker, HumanPacer, PlaywrightDriver  # noqa: E402
from packages.answer_bank import AnswerBank  # noqa: E402

HEAD = '<!doctype html><html><head><meta charset="utf-8"></head><body>'


def _combobox(qid: str, label: str, options, required=True) -> str:
    opts = "".join(f'<li role="option">{o}</li>' for o in options)
    return f"""
<div class="field"><label id="{qid}-label" for="{qid}">{label}</label>
  <input id="{qid}" role="combobox" class="select__input" aria-labelledby="{qid}-label"
         aria-required="{'true' if required else 'false'}" style="width:4px">
  <input aria-hidden="true" tabindex="-1" {'required' if required else ''} class="requiredInput" style="width:300px;opacity:0">
  <ul role="listbox" id="{qid}-list" hidden>{opts}</ul><span id="{qid}-value"></span></div>"""


GREENHOUSE = HEAD + f"""
<form action="../../confirmation/" method="get">
  <label for="first_name">First Name*</label><input id="first_name" name="first_name" required>
  <label for="last_name">Last Name*</label><input id="last_name" name="last_name" required>
  <label for="email">Email*</label><input id="email" name="email" required>
  <div class="field"><label>Resume/CV</label><label for="resume">Attach</label>
       <input type="file" id="resume" style="display:none"></div>
  <div class="field"><label>Cover Letter</label><label for="cover_letter">Attach</label>
       <input type="file" id="cover_letter" style="display:none"></div>
  {_combobox("question_1", "Will you now or in the future require sponsorship for a visa?*", ["No", "Yes, EU Blue Card"])}
  {_combobox("question_2", "What is your current country of residence?*", ["British Indian Ocean Territory", "India", "Indonesia"])}
  {_combobox("gender", "Gender", ["Male", "Female", "Decline To Self Identify"], required=False)}
  <iframe src="/hcaptcha/static/hcaptcha-enclave.html#frame=enclave" style="width:300px;height:100px"></iframe>
  <button type="submit">Submit application</button>
</form>
<script>
document.querySelectorAll('[role=combobox]').forEach((cb) => {{
  const list = document.getElementById(cb.id + '-list');
  cb.addEventListener('click', () => {{ list.hidden = false; }});
  cb.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') list.hidden = true; }});
  list.querySelectorAll('[role=option]').forEach((o) => o.addEventListener('click', () => {{
    document.getElementById(cb.id + '-value').textContent = o.textContent;
    cb.parentElement.querySelector('.requiredInput').value = o.textContent;  // like react-select
    list.hidden = true; }}));
}});
document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') document.querySelectorAll('[role=listbox]').forEach(l => l.hidden = true); }});
</script></body></html>"""

LEVER = HEAD + """
<form action="/lever/acme/abc/thanks/" method="get">
  <label>Resume/CV ✱ <input type="file" name="resume"></label>
  <label>Full name ✱ <input name="name" required></label>
  <label>Email ✱ <input type="email" name="email" required></label>
  <label>Current location ✱ <input name="location" required></label>
  <label>Current company <input name="org"></label>
  <label>LinkedIn URL ✱ <input name="urls[LinkedIn]" required></label>
  <label>Twitter URL <input name="urls[Twitter]"></label>
  <button type="submit">SUBMIT APPLICATION</button>
</form></body></html>"""

PAGES = {
    "gh/jobs/1/index.html": GREENHOUSE,
    "gh/confirmation/index.html": HEAD + "<h1>Thank you for applying!</h1></body></html>",
    "hcaptcha/static/hcaptcha-enclave.html": "<html><body></body></html>",
    "lever/acme/abc/apply/index.html": LEVER,
    "lever/acme/abc/thanks/index.html": HEAD + "<h2>Application submitted!</h2></body></html>",
}


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    root = tmp_path_factory.mktemp("ats")
    for rel, html in PAGES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    handler.log_message = lambda *a, **k: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest_asyncio.fixture
async def browser():
    async with playwright_api.async_playwright() as p:
        try:
            b = await p.chromium.launch(channel="chrome", headless=True)
        except Exception as exc:
            pytest.skip(f"No Chrome available: {exc}")
        yield b
        await b.close()


async def _no_sleep(_):
    return None


PACER = HumanPacer(sleep=_no_sleep, typing_delay_ms=(1, 2))


@pytest.fixture
def bank(tmp_path):
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"%PDF-1.4 test")
    return AnswerBank.from_intake({
        "identity": {"full_name": "Priya Raman", "email": "priya@example.com", "city": "Bengaluru", "country": "India",
                     "linkedin_url": "https://linkedin.com/in/priya"},
        "documents": {"master_resume_path": str(resume)},
        "screening": {"needs_sponsorship": False},
    }, profile={"current_company": "Acme"})


@pytest.mark.asyncio
async def test_greenhouse_fill_approve_submit(site, browser, bank, tmp_path):
    url = f"{site}/gh/jobs/1/"
    page = await browser.new_page()
    driver = PlaywrightDriver(page, adapter=GreenhouseAdapter())
    dry = await FormAutomationWorker(driver, pacer=PACER, evidence_dir=tmp_path).apply(url, bank)

    assert dry.status == "FILLED", dry.details
    assert await driver.detect_blockers() == []  # the invisible hCaptcha enclave is not a challenge
    assert dry.adapter == "GREENHOUSE"
    by_label = {f["label"]: f["value"] for f in dry.fields}
    assert by_label["Will you now or in the future require sponsorship for a visa?*"] == "No"
    assert by_label["What is your current country of residence?*"] == "India"
    assert by_label["Gender"] == "Decline To Self Identify"
    assert await page.inner_text("#question_1-value") == "No"
    assert await page.inner_text("#question_2-value") == "India"
    assert await page.locator("#resume").evaluate("e => e.files.length") == 1
    assert await page.locator("#cover_letter").evaluate("e => e.files.length") == 0
    assert dry.fields_detected == 8  # hidden "required" shadow inputs are not counted

    page2 = await browser.new_page()
    sent = await FormAutomationWorker(PlaywrightDriver(page2, adapter=GreenhouseAdapter()), pacer=PACER,
                                      evidence_dir=tmp_path).apply(url, bank, submit=True, expected_fingerprint=dry.fingerprint)
    assert sent.status == "SUBMITTED", sent.details
    assert "/confirmation/" in page2.url and "first_name=Priya" in page2.url


@pytest.mark.asyncio
async def test_lever_named_fields_and_apply_url(site, browser, bank, tmp_path):
    page = await browser.new_page()
    driver = PlaywrightDriver(page, adapter=LeverAdapter())
    res = await FormAutomationWorker(driver, pacer=PACER, evidence_dir=tmp_path).apply(f"{site}/lever/acme/abc", bank)
    assert res.status == "FILLED", res.details
    assert page.url.endswith("/lever/acme/abc/apply/")
    assert await page.input_value('[name="name"]') == "Priya Raman"
    assert await page.input_value('[name="org"]') == "Acme"
    assert await page.input_value('[name="location"]') == "Bengaluru, India"
    assert await page.input_value('[name="urls[Twitter]"]') == ""

    sent = await FormAutomationWorker(PlaywrightDriver(await browser.new_page(), adapter=LeverAdapter()), pacer=PACER,
                                      evidence_dir=tmp_path).apply(f"{site}/lever/acme/abc", bank, submit=True,
                                                                   expected_fingerprint=res.fingerprint)
    assert sent.status == "SUBMITTED", sent.details
