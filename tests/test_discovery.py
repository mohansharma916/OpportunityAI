"""
OpportunityOS — Discovery: feed parsers, source routing, filters & scoring,
LinkedIn hiring-post parsing, and a full discovery run over a mocked network.
"""

import json
from datetime import datetime, timedelta

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import create_engine, delete, inspect, select, text

from apps.api.db import _add_missing_columns, get_db, init_db
from apps.api.models import (
    CandidateIntakeModel,
    OpportunityModel,
    ScrapingPlatformModel,
    TrackedApplicationModel,
)
from apps.api.services.discovery_service import DiscoveryService
from apps.api.services.intake_service import IntakeService
from packages.connectors.job_feeds import (
    JobPosting,
    UnsupportedSource,
    parse_ashby,
    parse_greenhouse,
    parse_himalayas,
    parse_lever,
    parse_remoteok,
    parse_remotive,
    parse_wwr,
    regions_from_location,
    resolve_source,
)
from packages.connectors.linkedin_posts import parse_age, parse_hiring_post, search_urls
from packages.matching.discovery import CandidatePrefs, evaluate, parse_role_floors, salary_floor, title_fit

NOW = datetime(2026, 10, 16, 12, 0)
DAY = timedelta(days=1)

GREENHOUSE = {"jobs": [
    {"id": 1, "title": "Senior Backend Engineer", "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/1",
     "location": {"name": "Remote, India"}, "first_published": "2026-10-14T10:00:00-04:00",
     "content": "&lt;p&gt;Python, PostgreSQL and AWS.&lt;/p&gt;", "company_name": "Acme", "departments": [{"name": "Eng"}]},
    {"id": 2, "title": "Office Manager", "absolute_url": "https://x/2", "location": {"name": "Berlin"},
     "first_published": "2026-10-14T10:00:00Z", "content": ""},
]}
LEVER = [{"id": "a", "text": "Backend Developer", "hostedUrl": "https://jobs.lever.co/acme/a", "applyUrl": "https://jobs.lever.co/acme/a/apply",
          "categories": {"location": "Remote - Worldwide", "commitment": "Full-time", "team": "Eng"}, "workplaceType": "remote",
          "descriptionPlain": "We use Django.", "lists": [{"text": "You have", "content": "<li>Python</li>"}], "createdAt": 1792000000000,
          "salaryRange": {"min": 90000, "max": 120000, "currency": "USD", "interval": "per-year-salary"}}]
ASHBY = {"jobs": [{"id": "x", "title": "Platform Engineer", "location": "Remote (APAC)", "isRemote": True, "workplaceType": "Remote",
                   "secondaryLocations": [{"location": "Singapore"}], "jobUrl": "https://jobs.ashbyhq.com/acme/x",
                   "applyUrl": "https://jobs.ashbyhq.com/acme/x/application", "descriptionPlain": "Kubernetes",
                   "publishedAt": "2026-10-10T00:00:00Z", "isListed": True,
                   "compensation": {"summaryComponents": [{"compensationType": "Salary", "interval": "1 YEAR",
                                                           "currencyCode": "USD", "minValue": 80000, "maxValue": 110000}]}},
                  {"id": "hidden", "title": "Hidden", "isListed": False}]}
WWR = """<?xml version="1.0"?><rss><channel>
<item><title>Hex: Senior Backend Engineer</title><region>Anywhere in the World</region><category>Back-End</category>
<description>&lt;p&gt;Python&lt;/p&gt;</description><pubDate>Thu, 15 Oct 2026 07:30:56 +0000</pubDate>
<link>https://weworkremotely.com/remote-jobs/hex-senior-backend-engineer</link></item></channel></rss>"""


def test_parsers():
    gh = parse_greenhouse(GREENHOUSE, "Acme", "Acme")
    assert gh[0].remote and gh[0].regions == ["India"] and gh[0].description == "Python, PostgreSQL and AWS."
    assert gh[0].posted_at == datetime(2026, 10, 14, 14, 0)
    assert gh[1].remote is False and gh[1].regions == ["Berlin"]

    lv = parse_lever(LEVER, "Acme", "Acme")[0]
    assert lv.remote and lv.regions == ["Worldwide"] and "Python" in lv.description
    assert (lv.salary_min, lv.salary_max, lv.salary_period) == (90000, 120000, "year")
    assert lv.apply_url.endswith("/apply")

    ab = parse_ashby(ASHBY, "Acme", "Acme")
    assert len(ab) == 1 and ab[0].regions == ["APAC", "Singapore"] and ab[0].salary_max == 110000

    wwr = parse_wwr(WWR, "WWR")[0]
    assert (wwr.company, wwr.title, wwr.regions) == ("Hex", "Senior Backend Engineer", [])

    rok = parse_remoteok([{"legal": "link back"}, {"id": 5, "position": "Python Dev", "company": "Z", "url": "https://remoteok.com/x",
                                                    "location": "", "date": "2026-10-15T00:00:00+00:00", "salary_min": 0, "salary_max": 0}], "Remote OK")
    assert len(rok) == 1 and rok[0].salary_max is None and rok[0].meta["attribution"] == "via Remote OK"

    him = parse_himalayas({"jobs": [{"title": "Backend Engineer", "companyName": "Y", "guid": "g", "applicationLink": "a",
                                     "locationRestrictions": ["United States"], "pubDate": 1792000000, "minSalary": 40,
                                     "maxSalary": 60, "salaryPeriod": "hourly", "currency": "USD"}]}, "Himalayas")[0]
    assert him.regions == ["United States"] and him.salary_period == "hour"

    rem = parse_remotive({"jobs": [{"id": 1, "title": "Backend Engineer", "company_name": "M", "url": "u",
                                    "candidate_required_location": "Worldwide", "salary": "$170k - $200k",
                                    "publication_date": "2026-10-14T20:33:44"}]}, "Remotive")[0]
    assert rem.regions == [] and (rem.salary_min, rem.salary_max) == (170000, 200000)


def test_resolve_source_and_regions():
    assert resolve_source("https://job-boards.greenhouse.io/gitlab") == ("GREENHOUSE", "gitlab")
    assert resolve_source("https://boards-api.greenhouse.io/v1/boards/gitlab/jobs") == ("GREENHOUSE", "gitlab")
    assert resolve_source("https://jobs.lever.co/metabase/abc") == ("LEVER", "metabase")
    assert resolve_source("https://jobs.ashbyhq.com/posthog") == ("ASHBY", "posthog")
    assert resolve_source("https://weworkremotely.com/categories/x")[0] == "WWR"
    with pytest.raises(UnsupportedSource, match="login"):
        resolve_source("https://wellfound.com/jobs")
    with pytest.raises(UnsupportedSource, match="No connector"):
        resolve_source("https://example.com/careers")
    assert regions_from_location("Remote, France") == ["France"]
    assert regions_from_location("Remote (EMEA)") == ["EMEA"]
    assert regions_from_location("Remote") == []


PREFS = CandidatePrefs(target_titles=["Backend Engineer"], seniority="Senior",
                       skills=["Python", "PostgreSQL", "AWS", "Django"], country="India",
                       min_salary=60000, salary_currency="USD", excluded_companies=["Evil Corp"])


def _p(**kw):
    base = dict(source="Board", source_kind="WWR", external_id="1", title="Senior Backend Engineer", company="Acme",
                url="u", apply_url="u", remote=True, regions=[], description="Python, PostgreSQL, AWS", posted_at=NOW - DAY)
    base.update(kw)
    return JobPosting(**base)


@pytest.mark.parametrize("kw,reason", [
    (dict(company="Evil Corp"), "Excluded company"),
    (dict(remote=False), "Not remote"),
    (dict(regions=["United States"]), "Restricted to United States"),
    (dict(regions=["USA", "Canada"]), "Restricted"),
    (dict(posted_at=NOW - 20 * DAY), "Posted 20 days ago"),
    (dict(title="Account Executive"), "Title doesn't match"),
    (dict(salary_max=40000, salary_currency="USD", salary_period="year"), "below your floor"),
])
def test_hard_filters(kw, reason):
    ev = evaluate(_p(**kw), PREFS, now=NOW)
    assert not ev.eligible and reason in ev.reason


def test_eligible_regions_and_company_board_age():
    for regions in ([], ["India"], ["APAC"], ["Worldwide"], ["Asia Pacific", "EMEA"]):
        assert evaluate(_p(regions=regions), PREFS, now=NOW).eligible, regions
    assert "Region not stated" in evaluate(_p(), PREFS, now=NOW).notes
    # Company pages keep long-open roles: 40 days is fine there, not on a job board
    assert evaluate(_p(source_kind="GREENHOUSE", posted_at=NOW - 40 * DAY), PREFS, now=NOW).eligible
    assert not evaluate(_p(posted_at=NOW - 40 * DAY), PREFS, now=NOW).eligible
    # Salary in another currency is not compared
    assert evaluate(_p(salary_max=30000, salary_currency="EUR", salary_period="year"), PREFS, now=NOW).eligible


def test_scoring_and_buckets():
    strong = evaluate(_p(source_kind="GREENHOUSE", salary_max=100000, salary_currency="USD", salary_period="year"),
                      PREFS, remote_first=True, now=NOW)
    assert strong.breakdown == {"skills": 40, "title": 25, "salary": 15, "employer": 10, "freshness": 10}
    assert strong.bucket == "QUEUE" and strong.matched_skills == ["Python", "PostgreSQL", "AWS"]

    weak = evaluate(_p(title="Junior Backend Engineer", description="Rust, Elixir, Kafka, Go", posted_at=NOW - 12 * DAY),
                    PREFS, now=NOW)
    assert weak.breakdown["skills"] == 0 and weak.breakdown["title"] == 12  # junior role for a senior candidate
    assert weak.bucket == "DROP"

    assert title_fit("Back-End Developer (Python)", PREFS)[0] == 1.0
    assert title_fit("Backend Lead", PREFS)[0] < 0.5  # no role noun -> penalised


POSTS = [
    {"text": "We're hiring a Senior Backend Engineer! Fully remote (India). Apply: https://jobs.lever.co/acme/123",
     "author": "Ravi K", "author_headline": "Engineering Manager at Acme Labs | Hiring", "author_url": "https://linkedin.com/in/ravi",
     "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:1/", "age_label": "2d •", "links": []},
    {"text": "Looking for a backend engineer to join our team. Remote, anywhere. Send your CV to jobs@beta.io",
     "author": "Beta Inc", "author_headline": "12,345 followers", "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:2/",
     "age_label": "5h"},
    {"text": "#hiring Python Developer, hybrid in Pune. DM me if interested!", "author": "Sam", "author_headline": "CTO @ Gamma",
     "post_url": "p3", "age_label": "1w"},
    {"text": "Great talk on distributed systems today!", "author": "X", "post_url": "p4"},
]


def test_parse_hiring_posts():
    titles = ["Backend Engineer", "Python Developer"]
    a, b, c, d = [parse_hiring_post(p, titles, now=NOW) for p in POSTS]
    assert (a.title, a.company, a.meta["apply_method"]) == ("Backend Engineer", "Acme Labs", "ATS_LINK")
    assert a.apply_url == "https://jobs.lever.co/acme/123" and a.regions == ["India"] and a.remote
    assert a.posted_at == NOW - 2 * DAY and a.meta["poster"] == "Ravi K"
    assert (b.company, b.meta["apply_method"], b.meta["email"]) == ("Beta Inc", "EMAIL", "jobs@beta.io")
    assert b.regions == [] and b.posted_at == NOW - timedelta(hours=5)
    assert (c.company, c.meta["apply_method"], c.remote) == ("Gamma", "LINKEDIN_DM", False)
    assert d is None
    assert parse_age("3mo", NOW) == NOW - timedelta(days=90)
    urls = search_urls(titles, ["Python"], limit=3)
    assert len(urls) == 3 and all("datePosted=%22past-week%22" in u for u in urls)


def test_add_missing_columns(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE scraping_platforms (id TEXT PRIMARY KEY, name TEXT, url TEXT)"))
        _add_missing_columns(conn)
    cols = {c["name"] for c in inspect(engine).get_columns("scraping_platforms")}
    assert {"remote_first", "last_run", "status"} <= cols


# ---------------------------------------------------------------------------
# Full run with a mocked network
# ---------------------------------------------------------------------------

def _transport(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if "boards-api.greenhouse.io/v1/boards/acme-disc" in url:
        jobs = [dict(GREENHOUSE["jobs"][0], id=i, title=f"Senior Backend Engineer {i}",
                     first_published=(datetime.utcnow() - timedelta(days=1)).isoformat() + "Z") for i in range(4)]
        return httpx.Response(200, json={"jobs": jobs})
    if "api.lever.co/v0/postings/broken-disc" in url:
        return httpx.Response(404, json={"ok": False})
    return httpx.Response(404)


@pytest_asyncio.fixture
async def disc_db(monkeypatch):
    async def fixed_prefs(db):
        return CandidatePrefs(target_titles=["Backend Engineer"], skills=["Python", "PostgreSQL", "AWS"], country="India")

    # Other suites leave a profile behind; pin the candidate so scores are deterministic
    monkeypatch.setattr(DiscoveryService, "prefs", staticmethod(fixed_prefs))
    await init_db()
    async for db in get_db():
        for m in (TrackedApplicationModel, OpportunityModel, CandidateIntakeModel):
            await db.execute(delete(m))
        await db.commit()
        await IntakeService.update(db, {"identity": {"country": "India"},
                                        "targeting": {"target_titles": ["Backend Engineer"], "daily_cap": 2}})
        for name, url in (("Acme Disc", "https://job-boards.greenhouse.io/acme-disc"),
                          ("Broken Disc", "https://jobs.lever.co/broken-disc")):
            db.add(ScrapingPlatformModel(name=name, url=url, category="COMPANY_BOARD", status="ACTIVE",
                                         crawl_frequency_hours=12, remote_first=True, total_opportunities_found=0))
        await db.commit()
        yield db
        await db.execute(delete(ScrapingPlatformModel).where(ScrapingPlatformModel.name.like("% Disc")))
        await db.commit()
        break


@pytest.mark.asyncio
async def test_discovery_run_scores_queues_to_cap_and_records_errors(disc_db):
    db = disc_db
    ids = [p.id for p in (await db.execute(select(ScrapingPlatformModel).where(
        ScrapingPlatformModel.name.like("% Disc")))).scalars()]
    async with httpx.AsyncClient(transport=httpx.MockTransport(_transport)) as client:
        summary = await DiscoveryService.run(db, platform_ids=ids, client=client)

    assert summary["platforms_run"] == 2 and summary["fetched"] == 4 and summary["errors"] == 1
    broken = next(p for p in summary["platforms"] if p["platform"] == "Broken Disc")
    assert "404" in broken["error"]
    assert summary["queued"] == 2  # daily cap
    statuses = sorted(o.status for o in (await db.execute(select(OpportunityModel))).scalars())
    assert statuses.count("QUEUED") == 2 and statuses.count("MATCH") == 2

    tracked = (await db.execute(select(TrackedApplicationModel))).scalars().all()
    assert len(tracked) == 2 and all(t.status == "QUEUED" and t.apply_channel == "GREENHOUSE" for t in tracked)
    assert all(t.match_score >= 70 for t in tracked)

    acme = (await db.execute(select(ScrapingPlatformModel).where(ScrapingPlatformModel.name == "Acme Disc"))).scalar_one()
    assert acme.last_run["new"] == 4 and acme.last_scraped_at is not None

    # Not due again for 12 hours; with the cap used up nothing more is queued today
    again = await DiscoveryService.run(db)
    assert all(p["platform"] not in ("Acme Disc", "Broken Disc") for p in again["platforms"])
    assert again["queued"] == 0


@pytest.mark.asyncio
async def test_linkedin_posts_ingest(disc_db):
    postings = [parse_hiring_post(POSTS[0], ["Backend Engineer"]), parse_hiring_post(POSTS[2], ["Backend Engineer"])]
    stats = await DiscoveryService.ingest_linkedin_posts(disc_db, [p for p in postings if p])
    assert stats["fetched"] == 2 and stats["eligible"] == 1
    assert stats["dropped"] == {"Not remote": 1}  # the hybrid Pune post
    opp = (await disc_db.execute(select(OpportunityModel).where(OpportunityModel.source == "LinkedIn post"))).scalar_one()
    assert opp.raw_metadata["apply_method"] == "ATS_LINK" and opp.raw_metadata["poster"] == "Ravi K"
    if stats["queued"]:
        row = (await disc_db.execute(select(TrackedApplicationModel))).scalars().first()
        assert row.post_url and row.apply_channel == "ATS_LINK" and row.contact_name == "Ravi K"


def test_salary_floor_depends_on_role():
    prefs = CandidatePrefs(target_titles=["Backend Engineer", "DevOps Engineer"], country="India",
                           salary_currency="USD", role_min_salary=parse_role_floors(
                               {"Backend Engineer": "50,000", "DevOps Engineer": "", "x": "abc"}))
    assert prefs.role_min_salary == {"Backend Engineer": 50000.0}
    low = dict(salary_max=40000, salary_currency="USD", salary_period="year")
    assert "below your floor of 50,000" in evaluate(_p(**low), prefs, now=NOW).reason
    # A role with no floor of its own, and no general minimum: any pay is fine
    assert evaluate(_p(title="DevOps Engineer", **low), prefs, now=NOW).eligible
    prefs.min_salary = 45000
    assert not evaluate(_p(title="DevOps Engineer", **low), prefs, now=NOW).eligible
    assert salary_floor("Senior Backend Engineer", prefs) == 50000
