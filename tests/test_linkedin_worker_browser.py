"""
OpportunityOS — LinkedIn reader/editor in a real headless browser against mock profile pages.
The mock mirrors the DOM landmarks the worker relies on (section anchors, aria-hidden spans,
'Edit intro' / 'Edit about' controls, a role=dialog editor). Skipped when no Chrome is available.
"""

import functools
import http.server
import threading
from pathlib import Path

import pytest
import pytest_asyncio

playwright_api = pytest.importorskip("playwright.async_api")

from apps.worker.automation import HumanPacer  # noqa: E402
from apps.worker.linkedin import NeedsCandidate, apply_edit, read_profile  # noqa: E402

PROFILE = """<!doctype html><html><head><meta charset="utf-8"></head><body><main>
<section>
  <img class="pv-top-card-profile-picture__image--show" src="data:," alt="Priya Raman">
  <h1>Priya Raman</h1>
  <div class="text-body-medium" id="headline">Software Engineer at Acme</div>
  <span class="text-body-small inline">Bengaluru, Karnataka, India</span>
  <a href="#" aria-label="Edit intro" id="edit-intro">edit</a>
</section>
<section><div id="about"></div><h2><span aria-hidden="true">About</span></h2>
  <div><span aria-hidden="true" id="about-text">I build backend systems for payments teams and care about reliability.</span></div>
  <button aria-label="Edit about" id="edit-about">edit</button></section>
<section><div id="featured"></div><ul><li>Post</li><li>Repo</li></ul></section>
<section><div id="education"></div><ul><li><span aria-hidden="true">IIT</span></li></ul></section>
</main>
<div role="dialog" id="intro-dlg" aria-label="Edit intro" hidden>
  <label for="hl">Headline*</label><input id="hl"><button id="intro-save">Save</button></div>
<div role="dialog" id="about-dlg" aria-label="Edit about" hidden>
  <label for="ab">About</label><textarea id="ab"></textarea><button id="about-save">Save</button></div>
<script>
const $ = (id) => document.getElementById(id);
$('edit-intro').onclick = (e) => { e.preventDefault(); $('hl').value = $('headline').textContent; $('intro-dlg').hidden = false; };
$('intro-save').onclick = () => { $('headline').textContent = $('hl').value; $('intro-dlg').hidden = true; };
$('edit-about').onclick = () => { $('ab').value = $('about-text').textContent; $('about-dlg').hidden = false; };
$('about-save').onclick = () => { $('about-text').textContent = $('ab').value; $('about-dlg').hidden = true; };
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { $('intro-dlg').hidden = true; $('about-dlg').hidden = true; } });
</script></body></html>"""

EXPERIENCE = """<!doctype html><html><head><meta charset="utf-8"></head><body><main><ul>
<li><span aria-hidden="true">Backend Engineer</span><span aria-hidden="true">Acme · Full-time</span>
    <span aria-hidden="true">Jan 2022 - Present · 2 yrs 10 mos</span><span aria-hidden="true">Bengaluru</span>
    <span aria-hidden="true">Built payment APIs handling 2M requests per day with Python and PostgreSQL.</span></li>
<li><span aria-hidden="true">Globex</span><span aria-hidden="true">3 yrs</span>
  <ul><li><span aria-hidden="true">Software Engineer</span><span aria-hidden="true">Jun 2019 - Dec 2021 · 2 yrs 7 mos</span>
          <span aria-hidden="true">Owned the ingestion pipeline and cut processing time from hours to minutes.</span></li></ul></li>
</ul></main></body></html>"""

SKILLS = """<!doctype html><html><head><meta charset="utf-8"></head><body><main><ul>
<li><span aria-hidden="true">Python</span><span aria-hidden="true">12 endorsements</span></li>
<li><span aria-hidden="true">PostgreSQL</span></li>
<li><span aria-hidden="true">Python</span></li>
</ul></main></body></html>"""


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    root = tmp_path_factory.mktemp("linkedin")
    for rel, html in {
        "in/me/index.html": PROFILE,
        "in/me/details/experience/index.html": EXPERIENCE,
        "in/me/details/skills/index.html": SKILLS,
        "login/index.html": "<html><body>Sign in</body></html>",
    }.items():
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
async def page():
    async with playwright_api.async_playwright() as p:
        try:
            browser = await p.chromium.launch(channel="chrome", headless=True)
        except Exception as exc:
            pytest.skip(f"No Chrome available: {exc}")
        pg = await browser.new_page()
        yield pg
        await browser.close()


async def _no_sleep(_):
    return None


PACER = HumanPacer(sleep=_no_sleep, typing_delay_ms=(1, 2))


@pytest.mark.asyncio
async def test_read_profile(site, page):
    snap = await read_profile(page, pacer=PACER, base_url=f"{site}/in/me/")
    assert snap.source == "SCREEN"
    assert snap.name == "Priya Raman"
    assert snap.headline == "Software Engineer at Acme"
    assert snap.location == "Bengaluru, Karnataka, India"
    assert snap.about.startswith("I build backend systems")
    assert snap.has_photo is True and snap.has_banner is False and snap.open_to_work is False
    assert snap.featured_count == 2 and snap.education_count == 1 and snap.recommendations_count == 0
    assert [(e.title, e.company) for e in snap.experiences] == [("Backend Engineer", "Acme"), ("Software Engineer", "Globex")]
    assert snap.experiences[0].start == "Jan 2022" and snap.experiences[0].end == "Present"
    assert "2M requests" in snap.experiences[0].description
    assert snap.skills == ["Python", "PostgreSQL"]


@pytest.mark.asyncio
async def test_login_wall_stops(site, page):
    with pytest.raises(NeedsCandidate):
        await read_profile(page, pacer=PACER, base_url=f"{site}/login/")


@pytest.mark.asyncio
async def test_apply_edit_dry_run_save_and_mismatch(site, page, tmp_path):
    url = f"{site}/in/me/"
    new = "Backend Engineer | Python, PostgreSQL | Remote"

    shots = await apply_edit(page, "headline", new, "Software Engineer at Acme", save=False,
                             pacer=PACER, evidence_dir=tmp_path, base_url=url)
    assert Path(shots[0]).exists()
    assert await page.inner_text("#headline") == "Software Engineer at Acme"  # dry run discarded

    with pytest.raises(NeedsCandidate, match="changed since the audit"):
        await apply_edit(page, "headline", new, "Something else", save=True,
                         pacer=PACER, evidence_dir=tmp_path, base_url=url)

    await apply_edit(page, "headline", new, "Software Engineer at Acme", save=True,
                     pacer=PACER, evidence_dir=tmp_path, base_url=url)
    assert await page.inner_text("#headline") == new

    about = "I help fintech teams ship reliable APIs. " * 10
    await apply_edit(page, "about", about.strip(),
                     "I build backend systems for payments teams and care about reliability.",
                     save=True, pacer=PACER, evidence_dir=tmp_path, base_url=url)
    assert (await page.inner_text("#about-text")).startswith("I help fintech teams")

    with pytest.raises(ValueError):
        await apply_edit(page, "skills", "x", None, pacer=PACER, evidence_dir=tmp_path, base_url=url)
