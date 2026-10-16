"""
OpportunityOS — Opportunity Ingestion, Deduplication & Management Service
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_
from sqlalchemy.orm import selectinload

from apps.api.models import (
    OpportunityModel,
    MatchingScoreModel,
    ApplicationModel,
)
from packages.domain.models import (
    Opportunity,
    AuditEventType,
    PipelineStatus,
    SearchCriteria,
)
from packages.connectors import (
    HackerNewsConnector,
    GitHubContributionConnector,
    RemoteTechConnector,
    ManualImportConnector,
    RawListing,
)
from packages.matching.engine import MatchingEngine
from apps.api.services.profile_service import ProfileService
from apps.api.services.activity_service import ActivityService


class OpportunityService:
    def __init__(self):
        self.matcher = MatchingEngine()
        self.connectors = [
            HackerNewsConnector(),
            GitHubContributionConnector(),
            RemoteTechConnector(),
        ]
        self.manual_connector = ManualImportConnector()

    async def run_discovery(self, db: AsyncSession, criteria: Optional[SearchCriteria] = None) -> List[OpportunityModel]:
        """Discover listings from all external feeds, normalize, score, and persist."""
        all_created: List[OpportunityModel] = []
        domain_profile = await ProfileService.get_domain_profile(db)

        for connector in self.connectors:
            try:
                raw_listings = await connector.discover(criteria)
                for raw in raw_listings:
                    opp = await connector.normalize(raw)
                    persisted = await self._persist_and_score_opportunity(db, opp, domain_profile)
                    if persisted:
                        all_created.append(persisted)
            except Exception as e:
                await ActivityService.record_event(
                    db=db,
                    entity_type="CONNECTOR",
                    entity_id=connector.source_name,
                    action="CONNECTOR_ERROR",
                    reason=str(e),
                    status="FAILED",
                )

        return all_created

    async def import_manual_opportunity(
        self,
        db: AsyncSession,
        url: Optional[str],
        title: Optional[str],
        company: Optional[str],
        body: str,
    ) -> OpportunityModel:
        """User paste import: URL, raw text, or email."""
        raw = RawListing(
            source="MANUAL_IMPORT",
            external_id=str(uuid.uuid4())[:8],
            url=url or "https://manual-import.local",
            raw_title=title or "Software Engineering Position",
            raw_company=company or "Target Company",
            raw_body=body,
            raw_metadata={"imported_by": "user"},
        )
        opp = await self.manual_connector.normalize(raw)
        domain_profile = await ProfileService.get_domain_profile(db)
        persisted = await self._persist_and_score_opportunity(db, opp, domain_profile)
        return persisted

    async def _persist_and_score_opportunity(
        self,
        db: AsyncSession,
        opp: Opportunity,
        profile: Any,
    ) -> OpportunityModel:
        # Deduplication check: same company & title
        stmt = select(OpportunityModel).where(
            OpportunityModel.company_name.ilike(opp.company_name),
            OpportunityModel.title.ilike(opp.title),
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        # Create Opportunity DB Model
        opp_model = OpportunityModel(
            id=opp.id or str(uuid.uuid4()),
            source=opp.source,
            external_id=opp.external_id,
            url=opp.url,
            company_name=opp.company_name,
            company_domain=opp.company_domain,
            title=opp.title,
            description=opp.description,
            location=opp.location or "Remote",
            remote_type=opp.remote_type.value if hasattr(opp.remote_type, "value") else str(opp.remote_type),
            country=opp.country or "Worldwide",
            timezone=opp.timezone,
            employment_type=opp.employment_type.value if hasattr(opp.employment_type, "value") else str(opp.employment_type),
            salary_min=opp.salary_min,
            salary_max=opp.salary_max,
            salary_currency=opp.salary_currency,
            hourly_rate=opp.hourly_rate,
            required_skills=opp.required_skills,
            preferred_skills=opp.preferred_skills,
            experience_required_years=opp.experience_required_years or 3.0,
            status=PipelineStatus.DISCOVERED.value,
            date_posted=opp.date_posted or datetime.utcnow(),
            raw_metadata=opp.raw_metadata,
        )
        db.add(opp_model)
        await db.flush()

        # Score opportunity against CandidateProfile
        score = self.matcher.evaluate(profile, opp)

        # Set pipeline state based on match score
        pipeline_status = PipelineStatus.DISCOVERED.value
        if score.overall_match_score >= 85.0:
            pipeline_status = PipelineStatus.STRONG_MATCH.value
        elif score.overall_match_score >= 70.0:
            pipeline_status = PipelineStatus.AI_REVIEWING.value
        else:
            pipeline_status = PipelineStatus.DISCOVERED.value

        opp_model.status = pipeline_status

        # Create matching score record
        score_model = MatchingScoreModel(
            id=str(uuid.uuid4()),
            opportunity_id=opp_model.id,
            overall_match_score=score.overall_match_score,
            confidence_score=score.confidence_score,
            technical_match=score.technical_match,
            experience_match=score.experience_match,
            remote_match=score.remote_match,
            timezone_match=score.timezone_match,
            compensation_match=score.compensation_match,
            industry_match=score.industry_match,
            role_match=score.role_match,
            transferable_skills=score.transferable_skills,
            primary_strengths=score.primary_strengths,
            primary_gaps=score.primary_gaps,
            match_rationale=score.match_rationale,
            scored_at=datetime.utcnow(),
        )
        db.add(score_model)

        await db.commit()

        # Audit log
        await ActivityService.record_event(
            db=db,
            entity_type="OPPORTUNITY",
            entity_id=opp_model.id,
            action=AuditEventType.DISCOVERED_JOB,
            reason=f"Discovered from {opp_model.source}. Match score: {score.overall_match_score}%.",
            input_payload={"title": opp_model.title, "company": opp_model.company_name},
            output_payload={"score": score.overall_match_score, "status": opp_model.status},
        )

        return await self.get_opportunity_by_id(db, opp_model.id)

    async def get_opportunities(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        search: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 100,
    ) -> List[OpportunityModel]:
        stmt = (
            select(OpportunityModel)
            .options(
                selectinload(OpportunityModel.matching_score),
                selectinload(OpportunityModel.application),
                selectinload(OpportunityModel.contacts),
            )
            .order_by(desc(OpportunityModel.created_at))
            .limit(limit)
        )
        if status and status != "ALL":
            stmt = stmt.where(OpportunityModel.status == status)
        if search:
            kw = f"%{search}%"
            stmt = stmt.where(
                or_(
                    OpportunityModel.title.ilike(kw),
                    OpportunityModel.company_name.ilike(kw),
                    OpportunityModel.description.ilike(kw),
                )
            )

        res = await db.execute(stmt)
        items = list(res.scalars().all())

        if min_score is not None:
            items = [
                i for i in items
                if i.matching_score and i.matching_score.overall_match_score >= min_score
            ]

        return items

    async def get_opportunity_by_id(
        self, db: AsyncSession, opportunity_id: str
    ) -> Optional[OpportunityModel]:
        stmt = (
            select(OpportunityModel)
            .options(
                selectinload(OpportunityModel.matching_score),
                selectinload(OpportunityModel.application),
                selectinload(OpportunityModel.contacts),
            )
            .where(OpportunityModel.id == opportunity_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def update_opportunity_status(
        self, db: AsyncSession, opportunity_id: str, new_status: str, reason: Optional[str] = None
    ) -> Optional[OpportunityModel]:
        opp = await self.get_opportunity_by_id(db, opportunity_id)
        if not opp:
            return None
        old_status = opp.status
        opp.status = new_status
        await db.commit()
        await db.refresh(opp)

        await ActivityService.record_event(
            db=db,
            entity_type="OPPORTUNITY",
            entity_id=opportunity_id,
            action=AuditEventType.STATUS_CHANGED,
            reason=reason or f"Status changed from {old_status} to {new_status}",
            input_payload={"old_status": old_status},
            output_payload={"new_status": new_status},
        )
        return opp

    async def get_opportunities_grouped_by_date(
        self, db: AsyncSession, search: Optional[str] = None, status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Groups all opportunities by Date (Today, Yesterday, This Week, Earlier) with status counters."""
        opps = await self.get_opportunities(db, status=status, search=search, limit=250)

        now = datetime.utcnow()
        today_date = now.date()
        from datetime import timedelta
        yesterday_date = today_date - timedelta(days=1)
        seven_days_ago = today_date - timedelta(days=7)

        grouped: Dict[str, List[Any]] = {
            "today": [],
            "yesterday": [],
            "this_week": [],
            "earlier": [],
        }

        status_counts: Dict[str, int] = {
            "DISCOVERED": 0,
            "REVIEWING": 0,
            "APPLIED": 0,
            "INTERVIEWING": 0,
            "OFFER": 0,
            "REJECTED": 0,
            "ARCHIVED": 0,
        }

        for opp in opps:
            # Update status counts
            st = opp.status or "DISCOVERED"
            if st in status_counts:
                status_counts[st] += 1
            else:
                status_counts[st] = 1

            # Determine date bucket
            opp_date = (opp.date_posted or opp.created_at or now).date()
            if opp_date == today_date:
                grouped["today"].append(opp)
            elif opp_date == yesterday_date:
                grouped["yesterday"].append(opp)
            elif opp_date >= seven_days_ago:
                grouped["this_week"].append(opp)
            else:
                grouped["earlier"].append(opp)

        return {
            "total": len(opps),
            "groups": grouped,
            "status_counts": status_counts,
        }
