"""
OpportunityOS — Analytics & Performance Funnel Service
"""

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from apps.api.models import (
    OpportunityModel,
    ApplicationModel,
    ContactModel,
    MatchingScoreModel,
    AuditEventModel,
)


class AnalyticsService:
    @staticmethod
    async def get_dashboard_metrics(db: AsyncSession) -> Dict[str, Any]:
        # Count opportunities by status
        stmt_opps = select(OpportunityModel.status, func.count(OpportunityModel.id)).group_by(OpportunityModel.status)
        opp_counts_res = await db.execute(stmt_opps)
        opp_status_map = {status: count for status, count in opp_counts_res.all()}

        total_discovered = sum(opp_status_map.values())
        strong_matches = opp_status_map.get("STRONG_MATCH", 0)

        # Count applications
        stmt_apps = select(ApplicationModel.status, func.count(ApplicationModel.id)).group_by(ApplicationModel.status)
        app_res = await db.execute(stmt_apps)
        app_status_map = {status: count for status, count in app_res.all()}

        applications_prepared = app_status_map.get("PREPARED", 0) + app_status_map.get("NEEDS_APPROVAL", 0)
        applications_submitted = app_status_map.get("SUBMITTED", 0)

        # Total contacts
        contact_count_res = await db.execute(select(func.count(ContactModel.id)))
        total_contacts = contact_count_res.scalar() or 0

        # Average match score
        avg_score_res = await db.execute(select(func.avg(MatchingScoreModel.overall_match_score)))
        avg_score = avg_score_res.scalar() or 0.0

        # Sources breakdown
        stmt_sources = select(OpportunityModel.source, func.count(OpportunityModel.id)).group_by(OpportunityModel.source)
        sources_res = await db.execute(stmt_sources)
        sources_breakdown = [{"source": s, "count": c} for s, c in sources_res.all()]

        # Funnel stages
        funnel = [
            {"stage": "Discovered", "count": total_discovered, "color": "#6366f1"},
            {"stage": "Strong Match", "count": strong_matches, "color": "#3b82f6"},
            {"stage": "Prepared", "count": applications_prepared + applications_submitted, "color": "#06b6d4"},
            {"stage": "Submitted", "count": applications_submitted, "color": "#10b981"},
            {"stage": "Interviewing", "count": opp_status_map.get("INTERVIEW", 1), "color": "#8b5cf6"},
            {"stage": "Offer", "count": opp_status_map.get("OFFER", 0), "color": "#f59e0b"},
        ]

        # Success rate
        conversion_rate = 0.0
        if applications_submitted > 0:
            conversion_rate = round((opp_status_map.get("INTERVIEW", 1) / applications_submitted) * 100, 1)

        return {
            "total_discovered": total_discovered,
            "strong_matches": strong_matches,
            "applications_prepared": applications_prepared,
            "applications_submitted": applications_submitted,
            "total_contacts": total_contacts,
            "average_match_score": round(float(avg_score), 1),
            "conversion_rate": conversion_rate,
            "funnel": funnel,
            "sources": sources_breakdown,
            "needs_attention_count": app_status_map.get("NEEDS_APPROVAL", 0),
        }
