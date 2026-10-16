"""
OpportunityOS — Platform Service
The list of places searched for remote roles: remote job boards and verified company job boards.
Logins live only in the candidate's browser profile; sites that need one are searched by the worker.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models import ScrapingPlatformModel
from apps.api.services.activity_service import ActivityService
from packages.connectors.job_feeds import (
    COMPANY_BOARD_KINDS,
    UnsupportedSource,
    board_url,
    load_company_registry,
    resolve_source,
)

DEFAULT_BOARDS: List[Dict[str, Any]] = [
    {"name": "We Work Remotely", "url": "https://weworkremotely.com/categories/remote-programming-jobs", "crawl_frequency_hours": 12},
    {"name": "Remote OK", "url": "https://remoteok.com", "crawl_frequency_hours": 12},
    {"name": "Himalayas", "url": "https://himalayas.app/jobs", "crawl_frequency_hours": 12},
    {"name": "Remotive", "url": "https://remotive.com/remote-jobs/software-dev", "crawl_frequency_hours": 12},
    {"name": "Jobicy", "url": "https://jobicy.com/jobs", "crawl_frequency_hours": 12},
    {"name": "Wellfound", "url": "https://wellfound.com/jobs", "crawl_frequency_hours": 24,
     "auth_notes": "Needs your login. Searched in your browser by the worker in a later phase."},
    {"name": "LinkedIn hiring posts", "url": "https://www.linkedin.com/search/results/content/", "crawl_frequency_hours": 12,
     "category": "LINKEDIN_POSTS",
     "auth_notes": "Searched in your browser: python -m apps.worker.cli linkedin-posts"},
]


def _norm_url(url: str) -> str:
    return (url or "").lower().split("?")[0].rstrip("/").replace("https://", "").replace("http://", "").replace("www.", "")


def classify(url: str, category: Optional[str] = None) -> Dict[str, Any]:
    """Category and status for a platform URL, from whether we have a connector for it."""
    if category == "LINKEDIN_POSTS":
        return {"category": "LINKEDIN_POSTS", "status": "ACTIVE", "requires_auth": True}
    try:
        kind, _ = resolve_source(url)
    except UnsupportedSource as exc:
        login = "login" in str(exc).lower()
        return {"category": category or "JOB_BOARD", "status": "NEEDS_LOGIN" if login else "UNSUPPORTED",
                "requires_auth": login, "reason": str(exc)}
    return {"category": "COMPANY_BOARD" if kind in COMPANY_BOARD_KINDS else "JOB_BOARD",
            "status": "ACTIVE", "requires_auth": False}


class PlatformService:
    @staticmethod
    def to_dict(p: ScrapingPlatformModel) -> Dict[str, Any]:
        return {
            "id": p.id,
            "name": p.name,
            "url": p.url,
            "category": p.category,
            "added_by": p.added_by,
            "requires_auth": p.requires_auth,
            "auth_notes": p.auth_notes,
            "status": p.status,
            "remote_first": bool(p.remote_first),
            "crawl_frequency_hours": p.crawl_frequency_hours,
            "last_scraped_at": p.last_scraped_at.isoformat() + "Z" if p.last_scraped_at else None,
            "last_run": p.last_run,
            "total_opportunities_found": p.total_opportunities_found or 0,
            "created_at": p.created_at.isoformat() + "Z" if p.created_at else None,
        }

    @staticmethod
    async def ensure_defaults(db: AsyncSession) -> None:
        """Add any default board or verified company that is missing; re-check what each platform supports."""
        res = await db.execute(select(ScrapingPlatformModel))
        existing = list(res.scalars().all())
        known = {_norm_url(p.url) for p in existing}

        wanted = [dict(b, added_by="SYSTEM") for b in DEFAULT_BOARDS]
        for c in load_company_registry():
            wanted.append({
                "name": c["name"], "url": board_url(c["ats"].upper(), c["token"]), "crawl_frequency_hours": 12,
                "remote_first": c["remote_first"], "added_by": "SYSTEM",
            })

        changed = False
        for w in wanted:
            if _norm_url(w["url"]) in known:
                continue
            info = classify(w["url"], w.get("category"))
            db.add(ScrapingPlatformModel(
                name=w["name"], url=w["url"], category=info["category"], added_by=w["added_by"],
                requires_auth=info["requires_auth"], auth_notes=w.get("auth_notes") or info.get("reason"),
                status=info["status"], crawl_frequency_hours=w["crawl_frequency_hours"],
                remote_first=w.get("remote_first"), total_opportunities_found=0,
            ))
            known.add(_norm_url(w["url"]))
            changed = True

        # Older installs: platforms that used to be "scraped" through an unrelated connector
        for p in existing:
            if p.category == "LINKEDIN_POSTS":
                continue
            info = classify(p.url)
            if p.status == "ACTIVE" and info["status"] != "ACTIVE":
                p.status, p.requires_auth, p.auth_notes = info["status"], info["requires_auth"], info.get("reason")
                changed = True
            elif info["status"] == "ACTIVE" and p.category != info["category"]:
                p.category = info["category"]
                changed = True
        if changed:
            await db.commit()

    @staticmethod
    async def list_platforms(db: AsyncSession) -> List[ScrapingPlatformModel]:
        await PlatformService.ensure_defaults(db)
        res = await db.execute(
            select(ScrapingPlatformModel).order_by(ScrapingPlatformModel.category, ScrapingPlatformModel.name)
        )
        return list(res.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, platform_id: str) -> Optional[ScrapingPlatformModel]:
        res = await db.execute(select(ScrapingPlatformModel).where(ScrapingPlatformModel.id == platform_id))
        return res.scalar_one_or_none()

    @staticmethod
    async def create_platform(
        db: AsyncSession,
        name: str,
        url: str,
        auth_notes: Optional[str] = None,
        crawl_frequency_hours: int = 12,
        added_by: str = "USER",
    ) -> ScrapingPlatformModel:
        info = classify(url)
        if info["status"] == "UNSUPPORTED":
            raise ValueError(info["reason"])
        duplicate = [p for p in await PlatformService.list_platforms(db) if _norm_url(p.url) == _norm_url(url)]
        if duplicate:
            raise ValueError(f"Already on the list as '{duplicate[0].name}'.")
        platform = ScrapingPlatformModel(
            name=name, url=url, category=info["category"], added_by=added_by,
            requires_auth=info["requires_auth"], auth_notes=auth_notes or info.get("reason"),
            status=info["status"], crawl_frequency_hours=crawl_frequency_hours, total_opportunities_found=0,
        )
        db.add(platform)
        await db.commit()
        await db.refresh(platform)
        await ActivityService.record_event(
            db=db, entity_type="PLATFORM", entity_id=platform.id, action="PLATFORM_ADDED", actor=added_by,
            reason=f"Added '{name}' ({url}) as {platform.category}",
        )
        return platform

    @staticmethod
    async def update_platform(db: AsyncSession, platform_id: str, data: Dict[str, Any]) -> ScrapingPlatformModel:
        platform = await PlatformService.get(db, platform_id)
        if not platform:
            raise ValueError(f"Platform {platform_id} not found")
        for key in ("name", "status", "auth_notes", "crawl_frequency_hours"):
            if data.get(key) is not None:
                setattr(platform, key, data[key])
        if data.get("url") and data["url"] != platform.url:
            info = classify(data["url"])
            if info["status"] == "UNSUPPORTED":
                raise ValueError(info["reason"])
            platform.url, platform.category = data["url"], info["category"]
        platform.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(platform)
        return platform

    @staticmethod
    async def delete_platform(db: AsyncSession, platform_id: str) -> bool:
        platform = await PlatformService.get(db, platform_id)
        if not platform:
            return False
        await db.delete(platform)
        await db.commit()
        return True
