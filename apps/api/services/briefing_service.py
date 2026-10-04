"""
OpportunityOS — Daily AI Briefing Service
Generates the executive daily intelligence briefing for the candidate.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from apps.api.models import UserModel, CandidateProfileModel
from apps.api.services.analytics_service import AnalyticsService
from apps.api.services.opportunity_service import OpportunityService
from apps.api.services.profile_service import ProfileService
from packages.domain.models import DailyBriefing


class BriefingService:
    @staticmethod
    async def generate_daily_briefing(
        db: AsyncSession,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> DailyBriefing:
        metrics = await AnalyticsService.get_dashboard_metrics(db)
        opp_svc = OpportunityService()
        top_opps = await opp_svc.get_opportunities(db, min_score=75.0, limit=3)

        top_opp_summaries = []
        for opp in top_opps:
            top_opp_summaries.append({
                "id": opp.id,
                "company": opp.company_name,
                "title": opp.title,
                "score": opp.matching_score.overall_match_score if opp.matching_score else 80.0,
                "location": opp.location,
                "rationale": opp.matching_score.match_rationale if opp.matching_score else "High technical overlap",
            })

        best_company = top_opp_summaries[0]["company"] if top_opp_summaries else "Leading Tech Teams"
        best_title = top_opp_summaries[0]["title"] if top_opp_summaries else "Software Architect"

        # Dynamically resolve user's actual candidate name
        resolved_name = None
        if user_name and user_name.strip():
            resolved_name = user_name.strip()
        elif user_id:
            u_stmt = select(UserModel).where(UserModel.id == user_id)
            u_res = await db.execute(u_stmt)
            user_rec = u_res.scalar_one_or_none()
            if user_rec and user_rec.full_name and user_rec.full_name.strip():
                resolved_name = user_rec.full_name.strip()

        # Query candidate profile for name & actual skills
        profile_model = None
        if user_id:
            p_stmt = (
                select(CandidateProfileModel)
                .options(selectinload(CandidateProfileModel.skills))
                .where(CandidateProfileModel.user_id == user_id)
                .limit(1)
            )
            p_res = await db.execute(p_stmt)
            profile_model = p_res.scalar_one_or_none()

        if not profile_model:
            p_stmt = (
                select(CandidateProfileModel)
                .options(selectinload(CandidateProfileModel.skills))
                .order_by(CandidateProfileModel.updated_at.desc(), CandidateProfileModel.created_at.desc())
                .limit(1)
            )
            p_res = await db.execute(p_stmt)
            profile_model = p_res.scalar_one_or_none()

        if not resolved_name and profile_model and profile_model.full_name and profile_model.full_name.strip():
            resolved_name = profile_model.full_name.strip()

        if not resolved_name:
            latest_u_stmt = select(UserModel).order_by(UserModel.created_at.desc()).limit(1)
            latest_u_res = await db.execute(latest_u_stmt)
            latest_u = latest_u_res.scalar_one_or_none()
            if latest_u and latest_u.full_name and latest_u.full_name.strip():
                resolved_name = latest_u.full_name.strip()

        # Format greeting dynamically
        if resolved_name:
            first_name = resolved_name.split()[0]
            greeting = f"Good morning {first_name}."
        else:
            greeting = "Good morning."

        # Dynamically tailor focus area based on user's real skills or headline
        focus_domain = "software architecture & distributed systems"
        if profile_model:
            if profile_model.skills:
                skill_names = [s.skill_name for s in profile_model.skills[:2]]
                focus_domain = " & ".join(skill_names)
            elif profile_model.headline:
                focus_domain = profile_model.headline.lower()

        summary_text = (
            f"{greeting} Today OpportunityOS discovered {metrics['total_discovered']} new opportunities worldwide. "
            f"{metrics['strong_matches']} scored as high-confidence matches (≥85%), and {metrics['applications_prepared']} "
            f"applications have been tailored and staged for your review.\n\n"
            f"{best_company} ({best_title}) is particularly high-yield today with strong architectural alignment and "
            f"direct overlap with your {focus_domain} background. "
            f"{metrics['needs_attention_count']} items currently await your review in the Needs Attention queue."
        )

        return DailyBriefing(
            date=datetime.utcnow().strftime("%A, %B %d, %Y"),
            summary_text=summary_text,
            opportunities_discovered_count=metrics["total_discovered"],
            strong_matches_count=metrics["strong_matches"],
            applications_prepared_count=metrics["applications_prepared"],
            applications_submitted_count=metrics["applications_submitted"],
            interviews_detected_count=1,
            contacts_identified_count=metrics["total_contacts"],
            needs_attention_count=metrics["needs_attention_count"],
            top_recommended_opportunities=top_opp_summaries,
        )
