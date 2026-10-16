"""
OpportunityOS — LinkedIn hiring posts -> job postings (pivot plan, Pillar 1c).

The worker screen-reads LinkedIn post search results in the candidate's browser and hands
the raw posts here. A post becomes a JobPosting only if it is clearly hiring and names a role;
how to apply (ATS link, email, DM, comment) is read from the post text.
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from packages.connectors.job_feeds import JobPosting, regions_from_location
from packages.matching.discovery import normalize_title

SEARCH_URL = "https://www.linkedin.com/search/results/content/"

_HIRING = re.compile(
    r"\b(we(?:'| a)?re hiring|now hiring|i(?:'| a)?m hiring|is hiring|are hiring|hiring (?:for|a|an)|"
    r"looking for (?:a|an|\d+)|join (?:our|my) team|open (?:role|position)s?)\b|#hiring\b",
    re.I,
)
_ROLE = re.compile(
    r"(?:hiring|looking for|seeking|need)\s+(?:an?\s+|\d+\s+|two\s+|our next\s+)?"
    r"((?:senior|staff|lead|principal|junior|sr\.?|mid[- ]level|founding)?\s*"
    r"[A-Za-z+#./ -]{0,40}?(?:engineer|developer|architect|sre|programmer))s?\b",
    re.I,
)
_ATS = re.compile(r"https?://[^\s)]*(?:greenhouse\.io|lever\.co|ashbyhq\.com|workable\.com)[^\s)]*", re.I)
_LINK = re.compile(r"https?://[^\s)]+", re.I)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_DM = re.compile(r"\b(dm|message|inbox|ping|reach out to) me\b|\bsend me (?:a|your)\b|\bdrop me a\b", re.I)
_COMMENT = re.compile(r"\bcomment\b", re.I)
_REMOTE = re.compile(r"\b(remote|anywhere|worldwide|work from home|wfh|distributed)\b", re.I)
_ONSITE = re.compile(r"\b(on-?site|in-?office|hybrid|relocat\w+)\b", re.I)
_REGION = re.compile(r"remote\s*[\(\-–:|]\s*([A-Za-z ,/&.]{2,40}?)\s*[\)\.\n,|]", re.I)
_ONLY = re.compile(r"\b([A-Z][A-Za-z]{1,15}(?: [A-Z][A-Za-z]+)?)[- ]only\b")
_AGE = re.compile(r"(\d+)\s*(mo|m|h|d|w|y)\b")


def search_urls(target_titles: List[str], skills: List[str], limit: int = 5) -> List[str]:
    queries: List[str] = []
    for title in target_titles[:3]:
        queries += [f'hiring remote "{title}"', f'"we are hiring" {title} remote']
    for skill in skills[:2]:
        queries.append(f"#hiring remote {skill} engineer")
    seen, out = set(), []
    for q in queries:
        if q not in seen:
            seen.add(q)
            out.append(f'{SEARCH_URL}?keywords={quote(q)}&datePosted=%22past-week%22&sortBy=%22date_posted%22')
    return out[:limit]


def parse_age(label: str, now: Optional[datetime] = None) -> Optional[datetime]:
    now = now or datetime.utcnow()
    m = _AGE.search(label or "")
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    delta = {"m": timedelta(minutes=n), "h": timedelta(hours=n), "d": timedelta(days=n), "w": timedelta(weeks=n),
             "mo": timedelta(days=30 * n), "y": timedelta(days=365 * n)}[unit]
    return now - delta


def _role(text: str, target_titles: List[str]) -> Optional[str]:
    norm = normalize_title(text)
    for title in target_titles:
        if normalize_title(title).strip() and normalize_title(title).strip() in norm:
            return title
    m = _ROLE.search(text)
    if not m:
        return None
    role = re.sub(r"\s+", " ", m.group(1)).strip(" -/.")
    return role[:1].upper() + role[1:] if role else None


def _company(author: str, headline: str) -> str:
    m = re.search(r"(?:\bat\b|@)\s*([A-Z0-9][\w&.\- ]{1,40}?)(?:\s*[|·,(]|$)", headline or "")
    if m:
        return m.group(1).strip()
    if headline and re.search(r"\bfollowers\b", headline, re.I):  # a company page posted it
        return author
    return author or "Unknown"


def parse_hiring_post(post: Dict[str, Any], target_titles: List[str], now: Optional[datetime] = None) -> Optional[JobPosting]:
    """post: text, author, author_headline, author_url, post_url, age_label, links."""
    text = post.get("text") or ""
    if not _HIRING.search(text):
        return None
    role = _role(text, target_titles)
    if not role:
        return None

    links = list(post.get("links") or []) + _LINK.findall(text)
    ats = next((l for l in links if _ATS.match(l)), None)
    other = next((l for l in links if "linkedin.com/in/" not in l and "linkedin.com/company/" not in l
                  and "linkedin.com/feed" not in l and "linkedin.com/search" not in l), None)
    email = _EMAIL.search(text)
    if ats:
        method, apply_url, how = "ATS_LINK", ats, f"Apply via the link: {ats}"
    elif email:
        method, apply_url, how = "EMAIL", post.get("post_url") or "", f"Email {email.group(0)}"
    elif other:
        method, apply_url, how = "LINK", other, f"Apply via the link: {other}"
    elif _DM.search(text):
        method, apply_url, how = "LINKEDIN_DM", post.get("post_url") or "", "Message the poster on LinkedIn"
    elif _COMMENT.search(text):
        method, apply_url, how = "COMMENT", post.get("post_url") or "", "Comment on the post, then message the poster"
    else:
        method, apply_url, how = "SEE_POST", post.get("post_url") or "", "See the post for how to apply"

    if _REMOTE.search(text):
        remote: Optional[bool] = True
    elif _ONSITE.search(text):
        remote = False
    else:
        remote = None
    regions: List[str] = []
    m = _REGION.search(text)
    if m and not re.search(r"anywhere|worldwide|global", m.group(1), re.I):
        regions = regions_from_location(m.group(1))
    elif _ONLY.search(text):
        regions = [_ONLY.search(text).group(1)]

    author = (post.get("author") or "").strip()
    return JobPosting(
        source="LinkedIn post", source_kind="LINKEDIN_POST",
        external_id=(post.get("post_url") or "").rstrip("/").split("/")[-1][:120],
        title=role, company=_company(author, post.get("author_headline") or ""),
        url=post.get("post_url") or "", apply_url=apply_url,
        location="Remote" if remote else "", remote=remote, regions=regions,
        description=text, posted_at=parse_age(post.get("age_label") or "", now),
        meta={
            "apply_method": method, "how_to_apply": how, "post_url": post.get("post_url"),
            "poster": author, "poster_url": post.get("author_url"), "email": email.group(0) if email else None,
        },
    )
