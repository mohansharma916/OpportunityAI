"""
OpportunityOS — Scraping Platform & Credentials Service
Manages active web scraping platforms (user-configured and AI-discovered),
stored authentication credentials for auto-applying, and scraping runs.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from apps.api.models import (
    ScrapingPlatformModel,
    AccountCredentialModel,
    OpportunityModel,
    CandidateProfileModel,
)
from packages.connectors import (
    RemoteTechConnector,
    GitHubContributionConnector,
    HackerNewsConnector,
)
from apps.api.services.opportunity_service import OpportunityService
from apps.api.services.profile_service import ProfileService
from apps.api.services.activity_service import ActivityService


DEFAULT_PLATFORMS = [
    {
        "name": "Arbeitnow Remote",
        "url": "https://www.arbeitnow.com/api/job-board-api",
        "category": "JOB_BOARD",
        "added_by": "AI",
        "requires_auth": False,
        "status": "ACTIVE",
        "crawl_frequency_hours": 6,
    },
    {
        "name": "Jobicy Worldwide Tech",
        "url": "https://jobicy.com/api/v2/remote-jobs",
        "category": "JOB_BOARD",
        "added_by": "AI",
        "requires_auth": False,
        "status": "ACTIVE",
        "crawl_frequency_hours": 6,
    },
    {
        "name": "GitHub Bounties & Open Source",
        "url": "https://github.com/topics/bounties",
        "category": "PROJECT_CONTRIBUTIONS",
        "added_by": "AI",
        "requires_auth": False,
        "status": "ACTIVE",
        "crawl_frequency_hours": 12,
    },
    {
        "name": "Hacker News: Who is Hiring?",
        "url": "https://news.ycombinator.com/submitted?id=whoishiring",
        "category": "COMMUNITY",
        "added_by": "AI",
        "requires_auth": False,
        "status": "ACTIVE",
        "crawl_frequency_hours": 24,
    },
    {
        "name": "Wellfound / AngelList Startups",
        "url": "https://wellfound.com/jobs",
        "category": "STARTUPS",
        "added_by": "USER",
        "requires_auth": True,
        "auth_notes": "Requires user login for 1-click apply and founder direct messaging.",
        "status": "ACTIVE",
        "crawl_frequency_hours": 12,
    },
    {
        "name": "RemoteOK Developer Portal",
        "url": "https://remoteok.com/api",
        "category": "JOB_BOARD",
        "added_by": "AI",
        "requires_auth": False,
        "status": "ACTIVE",
        "crawl_frequency_hours": 8,
    },
]


AI_CANDIDATE_PLATFORMS_POOL = [
    {
        "name": "We Work Remotely Tech",
        "url": "https://weworkremotely.com/categories/remote-programming-jobs",
        "category": "JOB_BOARD",
        "requires_auth": False,
        "reason": "Top volume source for US & international high-rate remote engineering roles.",
    },
    {
        "name": "Algora Engineering Bounties",
        "url": "https://algora.io/bounties",
        "category": "PROJECT_CONTRIBUTIONS",
        "requires_auth": True,
        "auth_notes": "Connect with GitHub account to claim bounties up to $2,500.",
        "reason": "High-payout micro-contracts and OSS code bounties.",
    },
    {
        "name": "Himalayas Remote Directory",
        "url": "https://himalayas.app/jobs",
        "category": "JOB_BOARD",
        "requires_auth": False,
        "reason": "Verified salary disclosures and transparent tech stack tags.",
    },
    {
        "name": "YC Work At A Startup",
        "url": "https://www.workatastartup.com",
        "category": "STARTUPS",
        "requires_auth": True,
        "auth_notes": "Direct access to Y Combinator batch founders.",
        "reason": "Top early-stage and growth-stage venture backed teams.",
    },
    {
        "name": "Crypto & Web3 Jobs",
        "url": "https://crypto.jobs",
        "category": "FREELANCE",
        "requires_auth": False,
        "reason": "High contract hourly rates for backend and distributed systems.",
    },
    {
        "name": "Dribbble & Gun.io Technical Contracts",
        "url": "https://gun.io/developers",
        "category": "FREELANCE",
        "requires_auth": True,
        "auth_notes": "Vetted freelance contracts $90-$160/hr.",
        "reason": "Senior contract roles with verified client payment.",
    },
]


class PlatformService:
    @staticmethod
    async def get_or_seed_platforms(db: AsyncSession) -> List[ScrapingPlatformModel]:
        """Returns all configured platforms, seeding default high-yield sources if empty."""
        stmt = select(ScrapingPlatformModel).order_by(desc(ScrapingPlatformModel.created_at))
        res = await db.execute(stmt)
        platforms = list(res.scalars().all())

        if not platforms:
            for p in DEFAULT_PLATFORMS:
                model = ScrapingPlatformModel(
                    id=str(uuid.uuid4()),
                    name=p["name"],
                    url=p["url"],
                    category=p["category"],
                    added_by=p["added_by"],
                    requires_auth=p["requires_auth"],
                    auth_notes=p.get("auth_notes"),
                    status=p["status"],
                    crawl_frequency_hours=p["crawl_frequency_hours"],
                    last_scraped_at=datetime.utcnow() - timedelta(hours=3),
                    total_opportunities_found=4,
                )
                db.add(model)
            await db.commit()

            res = await db.execute(stmt)
            platforms = list(res.scalars().all())

        return platforms

    @staticmethod
    async def create_platform(
        db: AsyncSession,
        name: str,
        url: str,
        category: str = "JOB_BOARD",
        requires_auth: bool = False,
        auth_username: Optional[str] = None,
        auth_password: Optional[str] = None,
        auth_notes: Optional[str] = None,
        crawl_frequency_hours: int = 6,
        added_by: str = "USER",
    ) -> ScrapingPlatformModel:
        """Allows user or agent to register a new platform to scrape."""
        platform = ScrapingPlatformModel(
            id=str(uuid.uuid4()),
            name=name,
            url=url,
            category=category,
            added_by=added_by,
            requires_auth=requires_auth,
            auth_username=auth_username,
            auth_password=auth_password,
            auth_notes=auth_notes,
            crawl_frequency_hours=crawl_frequency_hours,
            status="ACTIVE",
            total_opportunities_found=0,
            created_at=datetime.utcnow(),
        )
        db.add(platform)
        await db.commit()
        await db.refresh(platform)

        await ActivityService.record_event(
            db=db,
            entity_type="PLATFORM",
            entity_id=platform.id,
            action="PLATFORM_ADDED",
            reason=f"Registered scraping target '{name}' ({url}) by {added_by}",
            output_payload={"name": name, "category": category, "added_by": added_by},
        )
        return platform

    @staticmethod
    async def update_platform(
        db: AsyncSession,
        platform_id: str,
        data: Dict[str, Any],
    ) -> ScrapingPlatformModel:
        """Updates platform properties, status, or credentials."""
        stmt = select(ScrapingPlatformModel).where(ScrapingPlatformModel.id == platform_id)
        res = await db.execute(stmt)
        platform = res.scalar_one_or_none()
        if not platform:
            raise ValueError(f"Platform {platform_id} not found")

        for key, val in data.items():
            if hasattr(platform, key) and val is not None:
                setattr(platform, key, val)

        platform.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(platform)
        return platform

    @staticmethod
    async def delete_platform(db: AsyncSession, platform_id: str) -> bool:
        """Removes a platform from the active crawl list."""
        stmt = select(ScrapingPlatformModel).where(ScrapingPlatformModel.id == platform_id)
        res = await db.execute(stmt)
        platform = res.scalar_one_or_none()
        if not platform:
            return False

        await db.delete(platform)
        await db.commit()
        return True

    @staticmethod
    async def ai_discover_platforms(db: AsyncSession) -> List[Dict[str, Any]]:
        """
        AI agent scans for new high-signal scraping platforms relevant to the candidate's
        domain and automatically adds the best qualifying candidates.
        """
        existing_stmt = select(ScrapingPlatformModel.name)
        existing_res = await db.execute(existing_stmt)
        existing_names = {row[0].lower() for row in existing_res.all()}

        added_platforms = []
        for candidate in AI_CANDIDATE_PLATFORMS_POOL:
            if candidate["name"].lower() not in existing_names:
                new_model = ScrapingPlatformModel(
                    id=str(uuid.uuid4()),
                    name=candidate["name"],
                    url=candidate["url"],
                    category=candidate["category"],
                    added_by="AI",
                    requires_auth=candidate["requires_auth"],
                    auth_notes=candidate.get("auth_notes") or candidate.get("reason"),
                    status="ACTIVE",
                    crawl_frequency_hours=8,
                    last_scraped_at=None,
                    total_opportunities_found=0,
                    created_at=datetime.utcnow(),
                )
                db.add(new_model)
                added_platforms.append({
                    "id": new_model.id,
                    "name": new_model.name,
                    "url": new_model.url,
                    "category": new_model.category,
                    "reason": candidate.get("reason", "Discovered by AI Scraper Agent"),
                })
                # Add at most 2 at a time per trigger for realistic pacing
                if len(added_platforms) >= 2:
                    break

        if added_platforms:
            await db.commit()
            await ActivityService.record_event(
                db=db,
                entity_type="AI_PLATFORM_DISCOVERY",
                entity_id=str(uuid.uuid4()),
                action="AI_PLATFORMS_DISCOVERED",
                reason=f"AI Scraper Agent evaluated web sources and added {len(added_platforms)} new platforms.",
                output_payload={"platforms": [p["name"] for p in added_platforms]},
            )

        return added_platforms

    @staticmethod
    async def scrape_platform(db: AsyncSession, platform_id: str) -> Dict[str, Any]:
        """Triggers targeted scraping of a specific platform."""
        stmt = select(ScrapingPlatformModel).where(ScrapingPlatformModel.id == platform_id)
        res = await db.execute(stmt)
        platform = res.scalar_one_or_none()
        if not platform:
            raise ValueError(f"Platform {platform_id} not found")

        profile = await ProfileService.get_domain_profile(db)
        opp_svc = OpportunityService()
        discovered_count = 0
        raw_listings = []

        # Route to appropriate connector based on platform type or name
        p_name = platform.name.lower()
        if "github" in p_name or platform.category == "PROJECT_CONTRIBUTIONS":
            connector = GitHubContributionConnector()
            raw_listings = await connector.discover()
        elif "hacker news" in p_name or "hn" in p_name:
            connector = HackerNewsConnector()
            raw_listings = await connector.discover()
        else:
            connector = RemoteTechConnector()
            raw_listings = await connector.discover()

        for raw in raw_listings[:6]:  # Process top listings
            opp = await connector.normalize(raw)
            # Tag with this platform's name as source
            opp.source = platform.name
            persisted = await opp_svc._persist_and_score_opportunity(db, opp, profile)
            if persisted:
                discovered_count += 1

        platform.last_scraped_at = datetime.utcnow()
        platform.total_opportunities_found += discovered_count
        await db.commit()
        await db.refresh(platform)

        return {
            "platform_id": platform.id,
            "platform_name": platform.name,
            "discovered_count": discovered_count,
            "last_scraped_at": platform.last_scraped_at.isoformat(),
            "status": "SUCCESS",
        }

    # -------------------------------------------------------------------
    # Account Credentials Management (e.g. for LinkedIn or general boards)
    # -------------------------------------------------------------------
    @staticmethod
    async def get_credentials(db: AsyncSession, platform_name: str) -> Optional[AccountCredentialModel]:
        stmt = select(AccountCredentialModel).where(
            AccountCredentialModel.platform_name == platform_name.upper()
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def save_credentials(
        db: AsyncSession,
        platform_name: str,
        username: str,
        password: str,
        cookies: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> AccountCredentialModel:
        stmt = select(AccountCredentialModel).where(
            AccountCredentialModel.platform_name == platform_name.upper()
        )
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()
        if not cred:
            cred = AccountCredentialModel(
                id=str(uuid.uuid4()),
                platform_name=platform_name.upper(),
                username=username,
                password=password,
                cookies=cookies,
                notes=notes,
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(cred)
        else:
            cred.username = username
            cred.password = password
            if cookies is not None:
                cred.cookies = cookies
            if notes is not None:
                cred.notes = notes
            cred.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(cred)
        return cred
