"""
OpportunityOS — Autonomous Application Decision & Execution Engine
Implements Automation Level 4 & Level 5 autonomous execution with strict safety guardrails.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.api.models import OpportunityModel, ApplicationModel
from packages.domain.models import PipelineStatus, AuditEventType
from packages.adapters import (
    EmailApplicationAdapter,
    ATSFormApplicationAdapter,
    GitHubContributionAdapter,
    ApplicationAdapter,
    SubmissionResult,
)
from apps.api.services.profile_service import ProfileService
from apps.api.services.application_service import ApplicationService
from apps.api.services.activity_service import ActivityService


class AutoApplyService:
    def __init__(self):
        self.adapters: List[ApplicationAdapter] = [
            EmailApplicationAdapter(),
            GitHubContributionAdapter(),
            ATSFormApplicationAdapter(),  # Fallback for ATS forms
        ]
        self.app_service = ApplicationService()

    async def get_adapter_for(self, url: str, method: str) -> ApplicationAdapter:
        for adapter in self.adapters:
            if await adapter.can_handle(url, method):
                return adapter
        return self.adapters[-1]

    async def auto_apply_opportunity(
        self,
        db: AsyncSession,
        opportunity_id: str,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes autonomous application flow for a single opportunity.
        Enforces Automation Level 4/5 policies and safety circuit breakers.
        """
        stmt = (
            select(OpportunityModel)
            .options(
                selectinload(OpportunityModel.matching_score),
                selectinload(OpportunityModel.application),
            )
            .where(OpportunityModel.id == opportunity_id)
        )
        res = await db.execute(stmt)
        opp = res.scalar_one_or_none()
        if not opp:
            raise ValueError(f"Opportunity {opportunity_id} not found")

        profile = await ProfileService.get_domain_profile(db)
        verified_answers = await ProfileService.get_verified_answers(db)
        score = opp.matching_score.overall_match_score if opp.matching_score else 0.0

        # Check Automation Policy
        # Level 4: Auto-submit high-confidence (Score >= 88.0)
        # Level 5: Autonomous agent
        auto_threshold = 88.0
        if not force:
            if profile.automation_level < 4:
                return {
                    "applied": False,
                    "reason": f"Automation Level is {profile.automation_level} (< 4). Human approval required.",
                    "status": "APPROVAL_REQUIRED",
                }

            if score < auto_threshold:
                return {
                    "applied": False,
                    "reason": f"Score {score}% is below autonomous threshold ({auto_threshold}%). Staged for approval.",
                    "status": "THRESHOLD_NOT_MET",
                }

        # 1. Prepare application package (Tailored resume variant & cover letter)
        app_model = await self.app_service.prepare_application(db, opportunity_id, style="TECHNICAL")

        # Re-fetch application with relationships
        app_stmt = (
            select(ApplicationModel)
            .options(
                selectinload(ApplicationModel.resume_variant),
                selectinload(ApplicationModel.cover_letter),
            )
            .where(ApplicationModel.id == app_model.id)
        )
        app_res = await db.execute(app_stmt)
        application = app_res.scalar_one()

        # 2. Select matching adapter
        method = "EMAIL" if opp.source == "HACKER_NEWS" else ("GITHUB_ISSUE" if "GITHUB" in opp.source else "ATS_FORM")
        adapter = await self.get_adapter_for(opp.url, method)

        # 3. Pre-flight inspection
        inspection = await adapter.inspect(opp.url, opp)

        # Safety Circuit Breaker Check: CAPTCHA, unknown legal question, or anti-bot
        if not inspection.can_auto_submit:
            application.status = "NEEDS_ATTENTION"
            opp.status = "NEEDS_ATTENTION"
            await db.commit()

            await ActivityService.record_event(
                db=db,
                entity_type="APPLICATION",
                entity_id=application.id,
                action=AuditEventType.NEEDS_ATTENTION_TRIGGERED,
                actor="CIRCUIT_BREAKER",
                reason=inspection.reason or "Security or legal challenge detected. Diverted to user review.",
                status="HALTED_HUMAN_ATTENTION",
            )

            return {
                "applied": False,
                "status": "NEEDS_ATTENTION",
                "circuit_breaker": True,
                "reason": inspection.reason,
            }

        # 4. Execute Submission via Adapter
        result: SubmissionResult = await adapter.submit(
            opportunity=opp,
            candidate_profile=profile,
            resume_variant=application.resume_variant,
            cover_letter=application.cover_letter,
            verified_answers=verified_answers,
        )

        if result.circuit_breaker_triggered or not result.success:
            application.status = "NEEDS_ATTENTION"
            opp.status = "NEEDS_ATTENTION"
            await db.commit()

            await ActivityService.record_event(
                db=db,
                entity_type="APPLICATION",
                entity_id=application.id,
                action=AuditEventType.NEEDS_ATTENTION_TRIGGERED,
                actor="CIRCUIT_BREAKER",
                reason=result.reason,
                status="HALTED_HUMAN_ATTENTION",
            )

            return {
                "applied": False,
                "status": "NEEDS_ATTENTION",
                "circuit_breaker": True,
                "reason": result.reason,
            }

        # 5. Successful Autonomous Application
        application.status = "SUBMITTED"
        application.submitted_at = datetime.utcnow()
        application.submission_mode = "AUTO"
        application.notes = f"Autonomous Submission ({adapter.adapter_name}) Ref: {result.confirmation_reference}"
        opp.status = PipelineStatus.APPLIED.value

        await db.commit()

        # Record immutable audit event
        await ActivityService.record_event(
            db=db,
            entity_type="APPLICATION",
            entity_id=application.id,
            action=AuditEventType.APPLICATION_SUBMITTED,
            actor="AUTO_AGENT",
            reason=f"Autonomously applied under Level {profile.automation_level} policy. Score: {score}%.",
            input_payload={"opportunity_id": opp.id, "score": score, "adapter": adapter.adapter_name},
            output_payload={"confirmation_reference": result.confirmation_reference, "fields": result.fields_filled},
            status="SUCCESS",
        )

        return {
            "applied": True,
            "status": "SUBMITTED",
            "confirmation_reference": result.confirmation_reference,
            "reason": result.reason,
            "adapter": adapter.adapter_name,
        }

    async def run_batch_auto_apply(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Scans all opportunities and auto-submits any that meet Automation Level 4/5 criteria.
        """
        profile = await ProfileService.get_domain_profile(db)
        if profile.automation_level < 4:
            return {
                "total_checked": 0,
                "applied_count": 0,
                "needs_attention_count": 0,
                "message": f"Automation Level is {profile.automation_level} (< 4). Auto-apply is inactive.",
            }

        # Find candidate opportunities
        stmt = (
            select(OpportunityModel)
            .options(
                selectinload(OpportunityModel.matching_score),
                selectinload(OpportunityModel.application),
            )
            .where(OpportunityModel.status.in_(["DISCOVERED", "STRONG_MATCH", "PREPARED"]))
        )
        res = await db.execute(stmt)
        candidates = list(res.scalars().all())

        applied = 0
        attention = 0

        for opp in candidates:
            score = opp.matching_score.overall_match_score if opp.matching_score else 0.0
            if score >= 88.0:
                outcome = await self.auto_apply_opportunity(db, opp.id)
                if outcome.get("applied"):
                    applied += 1
                elif outcome.get("status") == "NEEDS_ATTENTION":
                    attention += 1

        return {
            "total_checked": len(candidates),
            "applied_count": applied,
            "needs_attention_count": attention,
            "message": f"Auto-Apply run completed: {applied} submitted autonomously, {attention} routed to Needs Attention.",
        }
