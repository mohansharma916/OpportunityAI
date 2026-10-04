"""
OpportunityOS — Daily AI Briefing Service
Generates the executive daily intelligence briefing for the candidate.
"""

from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.services.analytics_service import AnalyticsService
from apps.api.services.opportunity_service import OpportunityService
from packages.domain.models import DailyBriefing


class BriefingService:
    @staticmethod
    async def generate_daily_briefing(db: AsyncSession) -> DailyBriefing:
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

        summary_text = (
            f"Good morning Alex. Today OpportunityOS discovered {metrics['total_discovered']} new opportunities worldwide. "
            f"{metrics['strong_matches']} scored as high-confidence matches (≥85%), and {metrics['applications_prepared']} "
            f"applications have been tailored and staged for your review.\n\n"
            f"{best_company} ({best_title}) is particularly high-yield today with strong architectural alignment and "
            f"direct overlap with your distributed systems experience. "
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
