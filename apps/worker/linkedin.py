"""
OpportunityOS — LinkedIn profile reader & editor (runs in the candidate's own browser profile).

Reader: screen-reads the candidate's own profile into a ProfileSnapshot.
Editor: types an approved headline / About into LinkedIn's own edit dialog.

Guardrails:
- Only the candidate's own profile (/in/me/) is read or edited; nothing else on LinkedIn is touched.
- A login wall or security check stops the run and hands it to the candidate.
- Before editing, the current text must still match what the audit saw; otherwise it stops.
- Without save=True the dialog is filled, screenshotted and discarded (dry run).
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from apps.worker.automation import EVIDENCE_DIR, HumanPacer
from packages.linkedin_optimizer import Experience, ProfileSnapshot

PROFILE_URL = "https://www.linkedin.com/in/me/"
_BLOCKED_URL = re.compile(r"/(login|checkpoint|authwall|uas/login|signup)", re.I)
_TYPE_MAX_CHARS = 120


class NeedsCandidate(Exception):
    """The candidate has to act in the browser (log in, pass a check, fix a mismatch)."""


_TOP_CARD_JS = r"""
() => {
  const vis = (el) => Array.from(el ? el.querySelectorAll('span[aria-hidden="true"]') : [])
    .map((x) => x.textContent.replace(/\s+/g, ' ').trim()).filter(Boolean);
  const sec = (id) => { const a = document.getElementById(id); return a ? a.closest('section') : null; };
  const topItems = (s) => s ? Array.from(s.querySelectorAll('li')).filter((li) => !li.parentElement.closest('li')) : [];
  const main = document.querySelector('main') || document.body;
  const card = main.querySelector('section');
  const h1 = card ? card.querySelector('h1') : null;
  const headlineEl = card ? card.querySelector('.text-body-medium') : null;
  const locEl = card ? card.querySelector('.text-body-small.inline, [data-test-location]') : null;
  const photo = card ? card.querySelector('img.pv-top-card-profile-picture__image--show, img[data-test-profile-photo], button img') : null;
  const banner = document.querySelector('#profile-background-image-target-image, img[data-test-banner]');
  const cardText = card ? card.innerText : '';
  const aboutSec = sec('about');
  const aboutTexts = vis(aboutSec).filter((t) => t !== 'About');
  const about = aboutTexts.sort((a, b) => b.length - a.length)[0] || null;
  const recSec = sec('recommendations');
  return {
    name: h1 ? h1.textContent.trim() : null,
    headline: headlineEl ? headlineEl.textContent.replace(/\s+/g, ' ').trim() : null,
    location: locEl ? locEl.textContent.replace(/\s+/g, ' ').trim() : null,
    has_photo: photo ? !/ghost|default/i.test(photo.className + ' ' + (photo.getAttribute('src') || '')) : false,
    has_banner: !!banner,
    open_to_work: /open to work/i.test(cardText) || !!document.querySelector('img[alt*="OPEN_TO_WORK" i]'),
    about,
    featured_count: sec('featured') ? topItems(sec('featured')).length : 0,
    recommendations_count: recSec ? topItems(recSec).length : 0,
    education_count: sec('education') ? topItems(sec('education')).length : 0,
    certifications_count: sec('licenses_and_certifications') ? topItems(sec('licenses_and_certifications')).length : 0,
  };
}
"""

_DETAILS_JS = r"""
(kind) => {
  const vis = (el) => Array.from(el.querySelectorAll('span[aria-hidden="true"]'))
    .map((x) => x.textContent.replace(/\s+/g, ' ').trim()).filter(Boolean);
  const main = document.querySelector('main') || document.body;
  const top = Array.from(main.querySelectorAll('li')).filter((li) => !li.parentElement.closest('li'));
  const dated = (t) => /\b(19|20)\d{2}\b|present/i.test(t);
  if (kind === 'skills') {
    return Array.from(new Set(top.map((li) => vis(li)[0]).filter((t) => t && !/endorse/i.test(t))));
  }
  const longest = (ts) => ts.filter((t) => t.length > 60 && !dated(t)).sort((a, b) => b.length - a.length)[0] || '';
  const out = [];
  for (const li of top) {
    const t = vis(li);
    if (!t.length) continue;
    const roles = Array.from(li.querySelectorAll('li')).filter((n) => vis(n).some(dated));
    if (roles.length) {
      for (const r of roles) {
        const rt = vis(r);
        out.push({ company: t[0], title: rt[0], dates: rt.find(dated) || '', description: longest(rt) });
      }
    } else {
      out.push({ title: t[0], company: (t[1] || '').split(' · ')[0], dates: t.find(dated) || '', description: longest(t) });
    }
  }
  return out;
}
"""


def _check_access(url: str) -> None:
    if _BLOCKED_URL.search(url):
        raise NeedsCandidate("LinkedIn is asking you to sign in or verify. Do it in the browser, then rerun.")


async def _settle(page: Any) -> None:
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass


async def _scroll_through(page: Any, pacer: HumanPacer) -> None:
    for _ in range(8):
        await page.mouse.wheel(0, 900)
        await pacer.between_fields()


async def read_profile(page: Any, pacer: Optional[HumanPacer] = None, base_url: str = PROFILE_URL) -> ProfileSnapshot:
    pacer = pacer or HumanPacer()
    await page.goto(base_url, wait_until="domcontentloaded", timeout=45000)
    await _settle(page)
    _check_access(page.url)
    profile_url = page.url.split("?")[0]
    await _scroll_through(page, pacer)
    top = await page.evaluate(_TOP_CARD_JS)

    root = profile_url.rstrip("/") + "/"
    details = {}
    for kind in ("experience", "skills"):
        await pacer.between_fields()
        await page.goto(f"{root}details/{kind}/", wait_until="domcontentloaded", timeout=45000)
        await _settle(page)
        _check_access(page.url)
        await _scroll_through(page, pacer)
        details[kind] = await page.evaluate(_DETAILS_JS, kind)

    experiences = []
    for e in details["experience"]:
        start, _, end = (e.get("dates") or "").split(" · ")[0].partition(" - ")
        experiences.append(Experience(
            title=e.get("title") or "", company=e.get("company") or "",
            description=e.get("description") or "", start=start.strip(), end=end.strip(),
        ))

    return ProfileSnapshot(
        source="SCREEN",
        profile_url=profile_url,
        experiences=experiences,
        skills=details["skills"],
        **{k: top.get(k) for k in (
            "name", "headline", "location", "about", "has_photo", "has_banner", "open_to_work",
            "featured_count", "recommendations_count", "education_count", "certifications_count",
        )},
    )


# ---------------------------------------------------------------------------
# Editor
# ---------------------------------------------------------------------------

_EDIT_BUTTON = {
    "headline": re.compile(r"^edit intro", re.I),
    "about": re.compile(r"^edit about", re.I),
}
_FIELD_LABEL = {
    "headline": re.compile(r"^headline", re.I),
    "about": re.compile(r"about|summary|description", re.I),
}


def _norm(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


async def apply_edit(
    page: Any,
    section: str,
    new_text: str,
    expected_current: Optional[str],
    save: bool = False,
    pacer: Optional[HumanPacer] = None,
    evidence_dir: Path = EVIDENCE_DIR,
    base_url: str = PROFILE_URL,
) -> List[str]:
    """Fill (and optionally save) one profile field. Returns screenshot paths."""
    if section not in _EDIT_BUTTON:
        raise ValueError(f"The agent only edits {', '.join(_EDIT_BUTTON)}; apply '{section}' by hand.")
    pacer = pacer or HumanPacer()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    shots: List[str] = []

    await page.goto(base_url, wait_until="domcontentloaded", timeout=45000)
    await _settle(page)
    _check_access(page.url)

    opener = page.get_by_role("link", name=_EDIT_BUTTON[section])
    if await opener.count() == 0:
        opener = page.get_by_role("button", name=_EDIT_BUTTON[section])
    if await opener.count() == 0:
        raise NeedsCandidate(f"Couldn't find the edit button for {section}. Apply this draft by hand.")
    await opener.first.click()

    dialog = page.get_by_role("dialog")
    await dialog.first.wait_for(timeout=15000)
    field = dialog.first.get_by_label(_FIELD_LABEL[section])
    if await field.count() == 0:
        field = dialog.first.get_by_role("textbox")
    if await field.count() == 0:
        raise NeedsCandidate(f"Couldn't find the {section} field in LinkedIn's dialog. Apply this draft by hand.")
    field = field.first

    current = await field.input_value()
    if expected_current is not None and _norm(current) != _norm(expected_current):
        await page.keyboard.press("Escape")
        raise NeedsCandidate(f"Your {section} changed since the audit. Re-run the audit before applying.")

    await field.click()
    await field.fill("")
    if len(new_text) <= _TYPE_MAX_CHARS:
        await field.press_sequentially(new_text, delay=pacer.typing_delay_ms())
    else:
        await field.fill(new_text)
    await pacer.between_fields()

    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    shot = evidence_dir / f"{stamp}-linkedin-{section}-{'save' if save else 'dryrun'}.png"
    await page.screenshot(path=str(shot))
    shots.append(str(shot))

    if not save:
        await page.keyboard.press("Escape")
        discard = page.get_by_role("button", name=re.compile(r"^discard", re.I))
        if await discard.count():
            await discard.first.click()
        return shots

    await dialog.first.get_by_role("button", name=re.compile(r"^save$", re.I)).click()
    await dialog.first.wait_for(state="hidden", timeout=15000)
    await _settle(page)
    body = _norm(await page.inner_text("main"))
    if _norm(new_text)[:60] not in body:
        raise NeedsCandidate(f"Saved, but the new {section} doesn't show on the profile yet. Check it in the browser.")
    return shots


# ---------------------------------------------------------------------------
# Hiring-post search (Pillar 1c)
# ---------------------------------------------------------------------------

_POSTS_JS = r"""
() => {
  const txt = (el) => el ? el.innerText.replace(/\s+\n/g, '\n').trim() : '';
  const vis = (el) => el ? (el.querySelector('span[aria-hidden="true"]') || el).innerText.trim() : '';
  const nodes = Array.from(document.querySelectorAll('[data-urn*="urn:li:activity:"], [data-chameleon-result-urn*="urn:li:activity:"]'));
  const seen = new Set();
  const out = [];
  for (const el of nodes) {
    const urn = el.getAttribute('data-urn') || el.getAttribute('data-chameleon-result-urn');
    if (!urn || seen.has(urn) || el.parentElement.closest('[data-urn*="urn:li:activity:"]')) continue;
    seen.add(urn);
    const body = el.querySelector('.update-components-text, .feed-shared-inline-show-more-text, .feed-shared-text, [data-test-post-text]');
    const authorLink = el.querySelector('a.update-components-actor__meta-link, a.update-components-actor__image, a[href*="/in/"], a[href*="/company/"]');
    out.push({
      post_url: 'https://www.linkedin.com/feed/update/' + urn + '/',
      text: txt(body) || txt(el),
      author: vis(el.querySelector('.update-components-actor__title, .update-components-actor__name, [data-test-author-name]')),
      author_headline: vis(el.querySelector('.update-components-actor__description, [data-test-author-headline]')),
      author_url: authorLink ? authorLink.href.split('?')[0] : null,
      age_label: vis(el.querySelector('.update-components-actor__sub-description, [data-test-post-age]')),
      links: Array.from((body || el).querySelectorAll('a[href^="http"]')).map((a) => a.href),
    });
  }
  return out;
}
"""


async def search_posts(page: Any, urls: List[str], pacer: Optional[HumanPacer] = None) -> List[dict]:
    """Open each LinkedIn post search, expand truncated posts, and return the raw posts."""
    pacer = pacer or HumanPacer()
    posts: dict = {}
    for i, url in enumerate(urls):
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await _settle(page)
        _check_access(page.url)
        await _scroll_through(page, pacer)
        more = page.get_by_role("button", name=re.compile(r"see more", re.I))
        for j in range(min(await more.count(), 20)):
            try:
                await more.nth(j).click(timeout=2000)
            except Exception:
                pass
        for post in await page.evaluate(_POSTS_JS):
            posts.setdefault(post["post_url"], post)
        if i < len(urls) - 1:
            await pacer.between_applications()
    return list(posts.values())
