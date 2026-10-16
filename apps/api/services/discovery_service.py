"""
OpportunityOS — Discovery Service (pivot plan, Pillar 1a)

fetch (job boards + company boards, or LinkedIn posts from the worker)
  -> hard filters from the intake -> score 0-100
  -> 70+: MATCH, moved into the application tracker up to the daily cap (QUEUED)
  -> 50-69: MAYBE list for the candidate
  -> below 50 or ineligible: dropped (counted, not stored)
"""

import asyncio
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.models import MatchingScoreModel, OpportunityModel, ScrapingPlatformModel, TrackedApplicationModel
from apps.api.services.activity_service import ActivityService
from apps.api.services.intake_service import DEFAULT_DAILY_CAP, IntakeService
from apps.api.services.platform_service import PlatformService
from apps.api.services.profile_service import ProfileService
from apps.api.services.tracker_service import DuplicateApplicationError, TrackerService
from packages.connectors.job_feeds import JobPosting, UnsupportedSource, fetch_postings, load_company_registry
from packages.matching.discovery import CandidatePrefs, evaluate

FETCH_CONCURRENCY = 4


def _drop_reason(reason: str) -> str:
    for prefix, label in (("Posted", "Too old"), ("Restricted", "Region restricted"), ("Pays", "Below salary floor"),
                          ("Title", "Title doesn't match"), ("Not remote", "Not remote"), ("Excluded", "Excluded company")):
        if reason.startswith(prefix):
            return label
    return reason[:40]


class DiscoveryService:
    @staticmethod
    async def prefs(db: AsyncSession) -> CandidatePrefs:
        intake = await IntakeService.get_or_create(db)
        identity, targeting = intake.identity or {}, intake.targeting or {}
        profile = await ProfileService.get_or_create_profile(db)
        titles = targeting.get("target_titles") or (profile.target_roles if profile else []) or []
        return CandidatePrefs(
            target_titles=titles,
            seniority=targeting.get("seniority"),
            skills=[s.skill_name for s in profile.skills] if profile else [],
            country=identity.get("country"),
            remote_scope=targeting.get("remote_scope") or "WORLDWIDE",
            allowed_regions=targeting.get("allowed_regions") or [],
            min_salary=targeting.get("min_salary"),
            salary_currency=targeting.get("salary_currency"),
            excluded_companies=targeting.get("excluded_companies") or [],
        )

    # ------------------------------------------------------------------
    # Ingest
    # ------------------------------------------------------------------
    @staticmethod
    async def ingest(
        db: AsyncSession,
        postings: List[JobPosting],
        prefs: CandidatePrefs,
        remote_first_default: bool = False,
    ) -> Dict[str, Any]:
        remote_first_names = {c["name"].lower() for c in load_company_registry() if c["remote_first"]}
        stats: Dict[str, Any] = {"fetched": len(postings), "eligible": 0, "new": 0, "match": 0, "maybe": 0}
        dropped: Counter = Counter()
        now = datetime.utcnow()

        for p in postings:
            remote_first = remote_first_default or (p.company or "").lower() in remote_first_names
            ev = evaluate(p, prefs, remote_first=remote_first, now=now)
            if not ev.eligible:
                dropped[_drop_reason(ev.reason)] += 1
                continue
            stats["eligible"] += 1
            if ev.bucket == "DROP":
                dropped["Score below 50"] += 1
                continue

            res = await db.execute(select(OpportunityModel.id).where(
                func.lower(OpportunityModel.company_name) == (p.company or "unknown").lower(),
                func.lower(OpportunityModel.title) == p.title.lower(),
            ))
            if res.first():
                continue

            status = "MATCH" if ev.bucket == "QUEUE" else "MAYBE"
            opp = OpportunityModel(
                source=p.source, external_id=p.external_id[:255], url=p.apply_url or p.url,
                company_name=p.company or "Unknown", title=p.title, description=p.description[:8000],
                location=p.location or "Remote", remote_type="REMOTE",
                country=", ".join(p.regions)[:100] if p.regions else "Not stated",
                employment_type=(p.employment_type or "FULL_TIME")[:50],
                salary_min=p.salary_min, salary_max=p.salary_max, salary_currency=p.salary_currency or "USD",
                hourly_rate=p.salary_max if p.salary_period == "hour" else None,
                required_skills=ev.matched_skills, preferred_skills=[],
                status=status, date_posted=p.posted_at or now,
                raw_metadata={
                    "source_kind": p.source_kind, "listing_url": p.url, "regions": p.regions,
                    "score_breakdown": ev.breakdown, "notes": ev.notes, **p.meta,
                },
            )
            db.add(opp)
            await db.flush()
            b = ev.breakdown
            db.add(MatchingScoreModel(
                opportunity_id=opp.id, overall_match_score=float(ev.score), confidence_score=80.0,
                technical_match=round(b["skills"] / 40 * 100, 1), role_match=round(b["title"] / 25 * 100, 1),
                compensation_match=round(b["salary"] / 15 * 100, 1), industry_match=round(b["employer"] / 10 * 100, 1),
                experience_match=round(b["freshness"] / 10 * 100, 1), remote_match=100.0,
                timezone_match=70.0 if "Region not stated" in ev.notes else 100.0,
                transferable_skills={}, primary_strengths=ev.matched_skills[:6], primary_gaps=[],
                match_rationale=(
                    f"{ev.score}/100 — skills {b['skills']}/40, title {b['title']}/25, salary {b['salary']}/15, "
                    f"employer {b['employer']}/10, freshness {b['freshness']}/10. " + " ".join(ev.notes)
                ).strip(),
            ))
            stats["new"] += 1
            stats["match" if status == "MATCH" else "maybe"] += 1

        await db.commit()
        stats["dropped"] = dict(dropped.most_common(4))
        return stats

    # ------------------------------------------------------------------
    # Queue
    # ------------------------------------------------------------------
    @staticmethod
    async def queued_today(db: AsyncSession) -> int:
        start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        res = await db.execute(select(func.count(TrackedApplicationModel.id)).where(
            TrackedApplicationModel.created_at >= start, TrackedApplicationModel.opportunity_id.isnot(None)
        ))
        return int(res.scalar() or 0)

    @staticmethod
    async def fill_queue(db: AsyncSession) -> int:
        """Move the best MATCH opportunities into the tracker, up to today's cap."""
        intake = await IntakeService.get_or_create(db)
        cap = int((intake.targeting or {}).get("daily_cap") or DEFAULT_DAILY_CAP)
        room = cap - await DiscoveryService.queued_today(db)
        if room <= 0:
            return 0
        res = await db.execute(
            select(OpportunityModel).options(selectinload(OpportunityModel.matching_score))
            .where(OpportunityModel.status == "MATCH")
        )
        matches = sorted(res.scalars().all(),
                         key=lambda o: o.matching_score.overall_match_score if o.matching_score else 0, reverse=True)
        queued = 0
        for opp in matches[:room]:
            meta = opp.raw_metadata or {}
            data = {
                "company": opp.company_name, "role": opp.title, "job_url": opp.url,
                "source_platform": opp.source, "opportunity_id": opp.id,
                "apply_channel": meta.get("apply_method") or meta.get("source_kind"),
                "match_score": opp.matching_score.overall_match_score if opp.matching_score else None,
                "post_url": meta.get("post_url"), "contact_name": meta.get("poster"), "contact_url": meta.get("poster_url"),
                "notes": meta.get("how_to_apply"),
            }
            try:
                await TrackerService.create(db, {k: v for k, v in data.items() if v is not None})
                queued += 1
            except DuplicateApplicationError:
                pass
            opp.status = "QUEUED"
            await db.commit()
        return queued

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------
    @staticmethod
    def _due(p: ScrapingPlatformModel, now: datetime) -> bool:
        return not p.last_scraped_at or now - p.last_scraped_at >= timedelta(hours=p.crawl_frequency_hours or 12)

    @staticmethod
    async def run(
        db: AsyncSession,
        platform_ids: Optional[List[str]] = None,
        force: bool = False,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        platforms = await PlatformService.list_platforms(db)
        now = datetime.utcnow()
        targets = [
            p for p in platforms
            if p.status == "ACTIVE" and p.category != "LINKEDIN_POSTS"
            and (platform_ids is None or p.id in platform_ids)
            and (force or platform_ids is not None or DiscoveryService._due(p, now))
        ]
        prefs = await DiscoveryService.prefs(db)

        own_client = client is None
        client = client or httpx.AsyncClient(follow_redirects=True)
        sem = asyncio.Semaphore(FETCH_CONCURRENCY)

        async def fetch(p: ScrapingPlatformModel):
            async with sem:
                try:
                    company = p.name if p.category == "COMPANY_BOARD" else None
                    return p, await fetch_postings(client, p.url, p.name, company=company), None
                except UnsupportedSource as exc:
                    return p, [], str(exc)
                except (httpx.HTTPError, ValueError) as exc:
                    return p, [], f"{type(exc).__name__}: {str(exc)[:160]}"

        try:
            results = await asyncio.gather(*[fetch(p) for p in targets])
        finally:
            if own_client:
                await client.aclose()

        per_platform = []
        totals = Counter()
        for platform, postings, error in results:
            stats = {"fetched": 0, "eligible": 0, "new": 0, "match": 0, "maybe": 0, "error": error}
            if not error:
                stats.update(await DiscoveryService.ingest(db, postings, prefs, bool(platform.remote_first)))
            platform.last_scraped_at = datetime.utcnow()
            platform.last_run = stats
            platform.total_opportunities_found = (platform.total_opportunities_found or 0) + stats["new"]
            await db.commit()
            for k in ("fetched", "eligible", "new", "match", "maybe"):
                totals[k] += stats[k]
            totals["errors"] += 1 if error else 0
            per_platform.append({"platform": platform.name, **stats})

        queued = await DiscoveryService.fill_queue(db)
        summary = {**dict(totals), "queued": queued, "platforms_run": len(targets), "platforms": per_platform}
        await ActivityService.record_event(
            db=db, entity_type="DISCOVERY", entity_id=now.isoformat(), action="DISCOVERY_RUN",
            reason=(f"{len(targets)} sources: {totals['fetched']} fetched, {totals['eligible']} eligible, "
                    f"{totals['new']} new, {queued} queued"),
            output_payload={k: v for k, v in summary.items() if k != "platforms"},
        )
        return summary

    @staticmethod
    async def ingest_linkedin_posts(db: AsyncSession, postings: List[JobPosting]) -> Dict[str, Any]:
        prefs = await DiscoveryService.prefs(db)
        stats = await DiscoveryService.ingest(db, postings, prefs)
        res = await db.execute(select(ScrapingPlatformModel).where(ScrapingPlatformModel.category == "LINKEDIN_POSTS"))
        platform = res.scalars().first()
        if platform:
            platform.last_scraped_at, platform.last_run = datetime.utcnow(), stats
            platform.total_opportunities_found = (platform.total_opportunities_found or 0) + stats["new"]
            await db.commit()
        stats["queued"] = await DiscoveryService.fill_queue(db)
        return stats
