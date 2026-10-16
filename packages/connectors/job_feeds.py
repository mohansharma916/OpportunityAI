"""
OpportunityOS — Job feed connectors (official public JSON APIs and RSS feeds only).

Company job boards: Greenhouse, Lever, Ashby (public posting APIs).
Remote job boards: We Work Remotely (RSS), Remote OK, Himalayas, Remotive, Jobicy, Arbeitnow (public APIs).

Each source is identified from its URL (`resolve_source`). A URL we have no connector for
is reported as unsupported instead of silently returning some other site's jobs.
Remote OK and Remotive ask for attribution: listings keep their link back to the board.
"""

import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field

USER_AGENT = "OpportunityOS/1.0 (personal remote job search)"
REGISTRY_PATH = Path(__file__).with_name("remote_companies.json")

COMPANY_BOARD_KINDS = {"GREENHOUSE", "LEVER", "ASHBY"}
NEEDS_LOGIN_HOSTS = ("wellfound.com", "angel.co", "workatastartup.com", "linkedin.com", "otta.com", "welcometothejungle.com")


class JobPosting(BaseModel):
    source: str
    source_kind: str
    external_id: str
    title: str
    company: str
    url: str
    apply_url: str
    location: str = ""
    remote: Optional[bool] = None
    regions: List[str] = Field(default_factory=list)  # [] = not stated
    description: str = ""
    posted_at: Optional[datetime] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None  # year, hour
    employment_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_company_board(self) -> bool:
        return self.source_kind in COMPANY_BOARD_KINDS


class UnsupportedSource(Exception):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def strip_html(text: Optional[str]) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<(br|/p|/li|/h\d)\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n\n", text)).strip()


def _dt(value: Any) -> Optional[datetime]:
    if value in (None, "", 0, "0"):
        return None
    try:
        if isinstance(value, (int, float)) or str(value).isdigit():
            v = float(value)
            return datetime.fromtimestamp(v / 1000 if v > 1e11 else v, tz=timezone.utc).replace(tzinfo=None)
        s = str(value)
        if re.match(r"^[A-Z][a-z]{2}, ", s):
            return parsedate_to_datetime(s).astimezone(timezone.utc).replace(tzinfo=None)
        parsed = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc).replace(tzinfo=None) if parsed.tzinfo else parsed
    except (ValueError, TypeError, OverflowError):
        return None


def _num(value: Any) -> Optional[float]:
    try:
        v = float(value)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


_REMOTE_RE = re.compile(r"\b(remote|anywhere|worldwide|distributed|work from home|wfh)\b", re.I)


def regions_from_location(location: str) -> List[str]:
    """'Remote, France' -> ['France']; 'Remote (EMEA)' -> ['EMEA']; 'Remote' -> []."""
    text = re.sub(r"\b(remote|fully|hybrid|only|based)\b|100%", " ", location or "", flags=re.I)
    parts = [p.strip(" ()[],;/|-–:") for p in re.split(r"[,;/|()]|\s[-–]\s|\bor\b", text)]
    return [p for p in parts if len(p) > 1]


# ---------------------------------------------------------------------------
# Parsers (pure: payload -> postings)
# ---------------------------------------------------------------------------

def parse_greenhouse(data: Dict[str, Any], company: str, source: str) -> List[JobPosting]:
    out = []
    for j in data.get("jobs") or []:
        location = (j.get("location") or {}).get("name") or ""
        out.append(JobPosting(
            source=source, source_kind="GREENHOUSE", external_id=str(j.get("id")),
            title=j.get("title") or "", company=j.get("company_name") or company,
            url=j.get("absolute_url") or "", apply_url=j.get("absolute_url") or "",
            location=location, remote=bool(_REMOTE_RE.search(location)),
            regions=regions_from_location(location) if _REMOTE_RE.search(location) else [location],
            description=strip_html(j.get("content")),
            posted_at=_dt(j.get("first_published") or j.get("updated_at")),
            tags=[d.get("name") for d in j.get("departments") or [] if d.get("name")],
        ))
    return out


def parse_lever(data: List[Dict[str, Any]], company: str, source: str) -> List[JobPosting]:
    out = []
    for j in data or []:
        cats = j.get("categories") or {}
        location = cats.get("location") or ""
        remote = (j.get("workplaceType") == "remote") or bool(_REMOTE_RE.search(location + " " + (cats.get("commitment") or "")))
        lists = "\n".join(
            f"{l.get('text', '')}\n{strip_html(l.get('content'))}" for l in j.get("lists") or []
        )
        salary = j.get("salaryRange") or {}
        out.append(JobPosting(
            source=source, source_kind="LEVER", external_id=str(j.get("id")),
            title=j.get("text") or "", company=company,
            url=j.get("hostedUrl") or "", apply_url=j.get("applyUrl") or j.get("hostedUrl") or "",
            location=location, remote=remote,
            regions=regions_from_location(location) if remote else [location],
            description="\n\n".join(x for x in (j.get("descriptionPlain"), lists, j.get("additionalPlain")) if x),
            posted_at=_dt(j.get("createdAt")),
            salary_min=_num(salary.get("min")), salary_max=_num(salary.get("max")),
            salary_currency=salary.get("currency"),
            salary_period="hour" if "hour" in str(salary.get("interval", "")).lower() else ("year" if salary else None),
            employment_type=cats.get("commitment"), tags=[cats.get("team")] if cats.get("team") else [],
        ))
    return out


def parse_ashby(data: Dict[str, Any], company: str, source: str) -> List[JobPosting]:
    out = []
    for j in data.get("jobs") or []:
        if j.get("isListed") is False:
            continue
        location = j.get("location") or ""
        secondary = [s.get("location") for s in j.get("secondaryLocations") or [] if s.get("location")]
        remote = bool(j.get("isRemote")) or j.get("workplaceType") == "Remote"
        regions = []
        for loc in [location] + secondary:
            regions.extend(regions_from_location(loc) if remote else [loc])
        salary_min = salary_max = currency = period = None
        for comp in ((j.get("compensation") or {}).get("summaryComponents") or []):
            if comp.get("compensationType") == "Salary":
                salary_min, salary_max = _num(comp.get("minValue")), _num(comp.get("maxValue"))
                currency = comp.get("currencyCode")
                period = "hour" if "HOUR" in str(comp.get("interval", "")).upper() else "year"
                break
        out.append(JobPosting(
            source=source, source_kind="ASHBY", external_id=str(j.get("id")),
            title=j.get("title") or "", company=company,
            url=j.get("jobUrl") or "", apply_url=j.get("applyUrl") or j.get("jobUrl") or "",
            location=location, remote=remote, regions=[r for r in regions if r],
            description=j.get("descriptionPlain") or strip_html(j.get("descriptionHtml")),
            posted_at=_dt(j.get("publishedAt")),
            salary_min=salary_min, salary_max=salary_max, salary_currency=currency, salary_period=period,
            employment_type=j.get("employmentType"), tags=[t for t in (j.get("department"), j.get("team")) if t],
        ))
    return out


def parse_wwr(xml_text: str, source: str) -> List[JobPosting]:
    out = []
    root = ET.fromstring(xml_text)
    for item in root.iter("item"):
        raw_title = item.findtext("title") or ""
        company, _, title = raw_title.partition(": ")
        if not title:
            company, title = "", raw_title
        region = item.findtext("region") or ""
        link = item.findtext("link") or item.findtext("guid") or ""
        out.append(JobPosting(
            source=source, source_kind="WWR", external_id=link.rstrip("/").split("/")[-1],
            title=title.strip(), company=company.strip(), url=link, apply_url=link,
            location=region or "Remote", remote=True,
            regions=[] if re.search(r"anywhere|worldwide", region, re.I) else regions_from_location(region),
            description=strip_html(item.findtext("description")),
            posted_at=_dt(item.findtext("pubDate")),
            employment_type=item.findtext("type"), tags=[item.findtext("category") or ""],
        ))
    return out


def parse_remoteok(data: List[Dict[str, Any]], source: str) -> List[JobPosting]:
    out = []
    for j in data or []:
        if "position" not in j:  # first element is the API legal notice
            continue
        location = j.get("location") or ""
        out.append(JobPosting(
            source=source, source_kind="REMOTEOK", external_id=str(j.get("id")),
            title=j.get("position") or "", company=j.get("company") or "",
            url=j.get("url") or "", apply_url=j.get("apply_url") or j.get("url") or "",
            location=location or "Remote", remote=True,
            regions=[] if not location or re.search(r"worldwide|anywhere", location, re.I) else regions_from_location(location),
            description=strip_html(j.get("description")), posted_at=_dt(j.get("date") or j.get("epoch")),
            salary_min=_num(j.get("salary_min")), salary_max=_num(j.get("salary_max")),
            salary_currency="USD" if _num(j.get("salary_max")) else None,
            salary_period="year" if _num(j.get("salary_max")) else None,
            tags=j.get("tags") or [], meta={"attribution": "via Remote OK"},
        ))
    return out


def parse_himalayas(data: Dict[str, Any], source: str) -> List[JobPosting]:
    out = []
    for j in data.get("jobs") or []:
        restrictions = j.get("locationRestrictions") or []
        period = (j.get("salaryPeriod") or "").lower()
        out.append(JobPosting(
            source=source, source_kind="HIMALAYAS", external_id=j.get("guid") or j.get("applicationLink") or "",
            title=j.get("title") or "", company=j.get("companyName") or "",
            url=j.get("guid") or j.get("applicationLink") or "", apply_url=j.get("applicationLink") or j.get("guid") or "",
            location=", ".join(restrictions) or "Worldwide", remote=True, regions=list(restrictions),
            description=strip_html(j.get("description") or j.get("excerpt")), posted_at=_dt(j.get("pubDate")),
            salary_min=_num(j.get("minSalary")), salary_max=_num(j.get("maxSalary")), salary_currency=j.get("currency"),
            salary_period="hour" if "hour" in period else ("year" if period else None),
            employment_type=j.get("employmentType"), tags=j.get("categories") or [],
            meta={"seniority": j.get("seniority") or []},
        ))
    return out


def _salary_from_text(text: str) -> Tuple[Optional[float], Optional[float]]:
    nums = [float(n.replace(",", "")) * (1000 if k else 1)
            for n, k in re.findall(r"\$?\s?(\d{2,3}(?:,\d{3})?)\s?(k)?", text or "", re.I)]
    nums = [n for n in nums if n >= 10000]
    return (min(nums), max(nums)) if nums else (None, None)


def parse_remotive(data: Dict[str, Any], source: str) -> List[JobPosting]:
    out = []
    for j in data.get("jobs") or []:
        loc = j.get("candidate_required_location") or ""
        smin, smax = _salary_from_text(j.get("salary") or "")
        out.append(JobPosting(
            source=source, source_kind="REMOTIVE", external_id=str(j.get("id")),
            title=j.get("title") or "", company=j.get("company_name") or "",
            url=j.get("url") or "", apply_url=j.get("url") or "",
            location=loc or "Worldwide", remote=True,
            regions=[] if not loc or re.search(r"worldwide|anywhere", loc, re.I) else regions_from_location(loc),
            description=strip_html(j.get("description")), posted_at=_dt(j.get("publication_date")),
            salary_min=smin, salary_max=smax, salary_currency="USD" if smax else None, salary_period="year" if smax else None,
            employment_type=j.get("job_type"), tags=j.get("tags") or [], meta={"attribution": "via Remotive"},
        ))
    return out


def parse_jobicy(data: Dict[str, Any], source: str) -> List[JobPosting]:
    out = []
    for j in data.get("jobs") or []:
        geo = j.get("jobGeo") or ""
        out.append(JobPosting(
            source=source, source_kind="JOBICY", external_id=str(j.get("id")),
            title=html.unescape(j.get("jobTitle") or ""), company=j.get("companyName") or "",
            url=j.get("url") or "", apply_url=j.get("url") or "",
            location=geo or "Remote", remote=True,
            regions=[] if not geo or re.search(r"anywhere|worldwide", geo, re.I) else regions_from_location(geo),
            description=strip_html(j.get("jobDescription") or j.get("jobExcerpt")), posted_at=_dt(j.get("pubDate")),
            salary_min=_num(j.get("annualSalaryMin")), salary_max=_num(j.get("annualSalaryMax")),
            salary_currency=j.get("salaryCurrency"), salary_period="year" if _num(j.get("annualSalaryMax")) else None,
            employment_type=", ".join(j.get("jobType") or []) or None, tags=j.get("jobIndustry") or [],
        ))
    return out


def parse_arbeitnow(data: Dict[str, Any], source: str) -> List[JobPosting]:
    out = []
    for j in data.get("data") or []:
        out.append(JobPosting(
            source=source, source_kind="ARBEITNOW", external_id=j.get("slug") or "",
            title=j.get("title") or "", company=j.get("company_name") or "",
            url=j.get("url") or "", apply_url=j.get("url") or "",
            location=j.get("location") or "", remote=bool(j.get("remote")),
            regions=[j.get("location")] if j.get("location") else [],
            description=strip_html(j.get("description")), posted_at=_dt(j.get("created_at")),
            employment_type=", ".join(j.get("job_types") or []) or None, tags=j.get("tags") or [],
        ))
    return out


# ---------------------------------------------------------------------------
# Routing & fetching
# ---------------------------------------------------------------------------

def resolve_source(url: str) -> Tuple[str, Optional[str]]:
    """Return (kind, token) for a platform URL, or raise UnsupportedSource."""
    u = (url or "").strip().lower()
    patterns = [
        ("GREENHOUSE", r"greenhouse\.io/(?:v1/boards/)?([a-z0-9_-]+)"),
        ("LEVER", r"(?:jobs\.lever\.co|api\.lever\.co/v0/postings)/([a-z0-9_.-]+)"),
        ("ASHBY", r"(?:jobs\.ashbyhq\.com|api\.ashbyhq\.com/posting-api/job-board)/([a-z0-9_.-]+)"),
    ]
    for kind, pattern in patterns:
        m = re.search(pattern, u)
        if m:
            return kind, m.group(1)
    for host, kind in (("weworkremotely.com", "WWR"), ("remoteok.com", "REMOTEOK"), ("himalayas.app", "HIMALAYAS"),
                       ("remotive.com", "REMOTIVE"), ("jobicy.com", "JOBICY"), ("arbeitnow.com", "ARBEITNOW")):
        if host in u:
            return kind, None
    if any(h in u for h in NEEDS_LOGIN_HOSTS):
        raise UnsupportedSource("Needs your login; it will be searched in your browser by the worker (not via API).")
    raise UnsupportedSource("No connector for this site yet. Add the company's Greenhouse, Lever or Ashby board URL instead.")


def board_url(kind: str, token: str) -> str:
    return {
        "GREENHOUSE": f"https://job-boards.greenhouse.io/{token}",
        "LEVER": f"https://jobs.lever.co/{token}",
        "ASHBY": f"https://jobs.ashbyhq.com/{token}",
    }[kind]


def _wwr_feed(url: str) -> str:
    u = url.split("?")[0].rstrip("/")
    if u.endswith(".rss"):
        return u
    if "/categories/" in u:
        return u + ".rss"
    return "https://weworkremotely.com/categories/remote-programming-jobs.rss"


async def fetch_postings(client: httpx.AsyncClient, url: str, source: str, company: Optional[str] = None) -> List[JobPosting]:
    kind, token = resolve_source(url)
    company = company or source

    async def get(u: str, **params: Any) -> httpx.Response:
        r = await client.get(u, params=params or None, headers={"User-Agent": USER_AGENT}, timeout=25)
        r.raise_for_status()
        return r

    if kind == "GREENHOUSE":
        return parse_greenhouse((await get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs", content="true")).json(), company, source)
    if kind == "LEVER":
        return parse_lever((await get(f"https://api.lever.co/v0/postings/{token}", mode="json")).json(), company, source)
    if kind == "ASHBY":
        return parse_ashby((await get(f"https://api.ashbyhq.com/posting-api/job-board/{token}", includeCompensation="true")).json(), company, source)
    if kind == "WWR":
        return parse_wwr((await get(_wwr_feed(url))).text, source)
    if kind == "REMOTEOK":
        return parse_remoteok((await get("https://remoteok.com/api")).json(), source)
    if kind == "HIMALAYAS":
        return parse_himalayas((await get("https://himalayas.app/jobs/api", limit=100)).json(), source)
    if kind == "REMOTIVE":
        return parse_remotive((await get("https://remotive.com/api/remote-jobs", category="software-dev")).json(), source)
    if kind == "JOBICY":
        return parse_jobicy((await get("https://jobicy.com/api/v2/remote-jobs", count=50, industry="engineering")).json(), source)
    if kind == "ARBEITNOW":
        return parse_arbeitnow((await get("https://www.arbeitnow.com/api/job-board-api")).json(), source)
    raise UnsupportedSource(kind)


def load_company_registry() -> List[Dict[str, Any]]:
    return json.loads(REGISTRY_PATH.read_text())["companies"]
