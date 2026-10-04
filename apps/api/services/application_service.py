"""
OpportunityOS — Application Package Generation & Submission Service
Coordinates resume tailoring, cover letter generation, verified Q&A resolution,
and human-in-the-loop approval workflows.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.api.models import (
    OpportunityModel,
    ApplicationModel,
    ResumeVariantModel,
    CoverLetterModel,
    ApplicationAnswerModel,
)
from packages.domain.models import (
    Opportunity,
    RemoteType,
    OpportunityType,
    PipelineStatus,
    AuditEventType,
)
from packages.ai.provider import get_ai_provider
from apps.api.services.profile_service import ProfileService
from apps.api.services.activity_service import ActivityService


class ApplicationService:
    def __init__(self):
        self.ai = get_ai_provider()

    async def prepare_application(
        self,
        db: AsyncSession,
        opportunity_id: str,
        style: str = "TECHNICAL",
    ) -> ApplicationModel:
        """
        Synthesizes tailored resume variant, personalized cover letter,
        and resolves verified form answers.
        """
        # Fetch opportunity
        opp_stmt = select(OpportunityModel).where(OpportunityModel.id == opportunity_id)
        opp_res = await db.execute(opp_stmt)
        opp_model = opp_res.scalar_one_or_none()
        if not opp_model:
            raise ValueError(f"Opportunity {opportunity_id} not found")

        # Fetch candidate profile & verified answers
        profile = await ProfileService.get_domain_profile(db)
        verified_answers = await ProfileService.get_verified_answers(db)

        # Convert opp model to domain object
        opp_domain = Opportunity(
            id=opp_model.id,
            source=opp_model.source,
            external_id=opp_model.external_id,
            url=opp_model.url,
            company_name=opp_model.company_name,
            company_domain=opp_model.company_domain,
            title=opp_model.title,
            description=opp_model.description,
            location=opp_model.location,
            remote_type=RemoteType(opp_model.remote_type) if opp_model.remote_type in [r.value for r in RemoteType] else RemoteType.REMOTE,
            country=opp_model.country,
            employment_type=OpportunityType(opp_model.employment_type) if opp_model.employment_type in [e.value for e in OpportunityType] else OpportunityType.FULL_TIME,
            salary_min=opp_model.salary_min,
            salary_max=opp_model.salary_max,
            hourly_rate=opp_model.hourly_rate,
            required_skills=opp_model.required_skills or [],
            preferred_skills=opp_model.preferred_skills or [],
            experience_required_years=opp_model.experience_required_years,
        )

        # 1. Generate Tailored Resume Variant
        tailored_resume = self.ai.tailor_resume(profile, opp_domain)
        resume_model = ResumeVariantModel(
            id=str(uuid.uuid4()),
            opportunity_id=opp_model.id,
            variant_name=tailored_resume.variant_name,
            headline=tailored_resume.headline,
            summary=tailored_resume.summary,
            selected_skills=tailored_resume.selected_skills,
            reordered_experiences=tailored_resume.reordered_experiences,
            emphasized_achievements=tailored_resume.emphasized_achievements,
            pdf_render_url=tailored_resume.pdf_render_url,
            content_hash=tailored_resume.content_hash,
        )
        db.add(resume_model)
        await db.flush()

        # 2. Generate Tailored Cover Letter
        cover_letter = self.ai.generate_cover_letter(profile, opp_domain, style=style)
        cover_model = CoverLetterModel(
            id=str(uuid.uuid4()),
            opportunity_id=opp_model.id,
            style=cover_letter.style,
            content=cover_letter.content,
            key_selling_points=cover_letter.key_selling_points,
        )
        db.add(cover_model)
        await db.flush()

        # 3. Create or Update Application
        app_stmt = select(ApplicationModel).where(ApplicationModel.opportunity_id == opportunity_id)
        app_res = await db.execute(app_stmt)
        application = app_res.scalar_one_or_none()

        submission_mode = "APPROVAL"
        initial_status = "NEEDS_APPROVAL"
        if profile.automation_level >= 4:
            submission_mode = "AUTO"

        now_str = datetime.utcnow().strftime("%b %d, %H:%M")
        default_tasks = [
            {"id": "t1", "title": "Opportunity Crawled & Analyzed", "status": "COMPLETED", "completed_at": now_str},
            {"id": "t2", "title": "Semantic Fit & Salary Floor Validated", "status": "COMPLETED", "completed_at": now_str},
            {"id": "t3", "title": f"Tailored Resume Variant ({tailored_resume.variant_name}) Generated", "status": "COMPLETED", "completed_at": now_str},
            {"id": "t4", "title": f"Targeted Cover Letter ({style}) Synthesized", "status": "COMPLETED", "completed_at": now_str},
            {"id": "t5", "title": f"Screening Q&A Memory Resolved ({len(verified_answers)} Answers)", "status": "COMPLETED", "completed_at": now_str},
            {"id": "t6", "title": "Application Submitted to Employer Portal", "status": "PENDING", "completed_at": None},
            {"id": "t7", "title": "Hiring Manager / Team Follow-Up", "status": "PENDING", "completed_at": None},
        ]

        if not application:
            application = ApplicationModel(
                id=str(uuid.uuid4()),
                opportunity_id=opp_model.id,
                resume_variant_id=resume_model.id,
                cover_letter_id=cover_model.id,
                submission_mode=submission_mode,
                status=initial_status,
                submission_url=opp_model.url,
                notes=f"Prepared {style} application with {len(tailored_resume.selected_skills)} targeted skills.",
                tasks=default_tasks,
            )
            db.add(application)
        else:
            application.resume_variant_id = resume_model.id
            application.cover_letter_id = cover_model.id
            application.status = initial_status
            application.submission_mode = submission_mode
            if not application.tasks:
                application.tasks = default_tasks

        # Update opportunity pipeline status
        opp_model.status = PipelineStatus.NEEDS_APPROVAL.value

        await db.commit()
        await db.refresh(application)

        # Audit events
        await ActivityService.record_event(
            db=db,
            entity_type="APPLICATION",
            entity_id=application.id,
            action=AuditEventType.APPLICATION_PREPARED,
            reason=f"Generated tailored resume ({resume_model.variant_name}) and {style} cover letter.",
            input_payload={"opportunity_id": opportunity_id, "style": style},
            output_payload={"application_id": application.id, "status": application.status},
        )

        return application

    async def approve_and_submit(
        self,
        db: AsyncSession,
        application_id: str,
        user_notes: Optional[str] = None,
    ) -> ApplicationModel:
        """User explicitly reviews and submits the application."""
        stmt = (
            select(ApplicationModel)
            .options(
                selectinload(ApplicationModel.opportunity),
                selectinload(ApplicationModel.resume_variant),
                selectinload(ApplicationModel.cover_letter),
            )
            .where(ApplicationModel.id == application_id)
        )
        res = await db.execute(stmt)
        application = res.scalar_one_or_none()
        if not application:
            raise ValueError(f"Application {application_id} not found")

        # Mark as submitted
        application.status = "SUBMITTED"
        application.submitted_at = datetime.utcnow()
        if user_notes:
            application.notes = (application.notes or "") + f"\nUser Approval Note: {user_notes}"

        # Transition opportunity status to APPLIED
        if application.opportunity:
            application.opportunity.status = PipelineStatus.APPLIED.value

        await db.commit()
        await db.refresh(application)

        # Audit event
        await ActivityService.record_event(
            db=db,
            entity_type="APPLICATION",
            entity_id=application.id,
            action=AuditEventType.APPLICATION_SUBMITTED,
            actor="USER_APPROVAL",
            reason=f"Application submitted for {application.opportunity.company_name if application.opportunity else 'position'}.",
            input_payload={"application_id": application_id, "user_notes": user_notes},
            output_payload={"status": "SUBMITTED", "submitted_at": str(application.submitted_at)},
        )

        return application

    async def get_applications(
        self, db: AsyncSession, status: Optional[str] = None
    ) -> List[ApplicationModel]:
        stmt = (
            select(ApplicationModel)
            .options(
                selectinload(ApplicationModel.opportunity),
                selectinload(ApplicationModel.resume_variant),
                selectinload(ApplicationModel.cover_letter),
            )
            .order_by(ApplicationModel.created_at.desc())
        )
        if status:
            stmt = stmt.where(ApplicationModel.status == status)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def update_status(
        self, db: AsyncSession, application_id: str, status: str
    ) -> Optional[ApplicationModel]:
        stmt = (
            select(ApplicationModel)
            .options(
                selectinload(ApplicationModel.opportunity),
                selectinload(ApplicationModel.resume_variant),
                selectinload(ApplicationModel.cover_letter),
            )
            .where(ApplicationModel.id == application_id)
        )
        res = await db.execute(stmt)
        application = res.scalar_one_or_none()
        if not application:
            return None

        application.status = status
        if status in ["SUBMITTED", "AUTO_APPLIED"] and not application.submitted_at:
            application.submitted_at = datetime.utcnow()

        if application.opportunity:
            if status in ["SUBMITTED", "AUTO_APPLIED"]:
                application.opportunity.status = PipelineStatus.APPLIED.value
            elif status == "INTERVIEWING":
                application.opportunity.status = PipelineStatus.INTERVIEW.value
            elif status == "OFFERED":
                application.opportunity.status = PipelineStatus.OFFER.value
            elif status == "REJECTED":
                application.opportunity.status = PipelineStatus.REJECTED.value

        await db.commit()
        await db.refresh(application)
        return application

    async def add_task(
        self, db: AsyncSession, application_id: str, title: str
    ) -> Optional[ApplicationModel]:
        stmt = select(ApplicationModel).where(ApplicationModel.id == application_id)
        res = await db.execute(stmt)
        application = res.scalar_one_or_none()
        if not application:
            return None

        current_tasks = list(application.tasks or [])
        new_task = {
            "id": f"task-{uuid.uuid4().hex[:6]}",
            "title": title.strip(),
            "status": "PENDING",
            "created_at": datetime.utcnow().strftime("%b %d, %H:%M"),
        }
        current_tasks.append(new_task)
        application.tasks = current_tasks
        await db.commit()
        await db.refresh(application)
        return application

    async def toggle_task(
        self, db: AsyncSession, application_id: str, task_id: str, new_status: Optional[str] = None
    ) -> Optional[ApplicationModel]:
        stmt = select(ApplicationModel).where(ApplicationModel.id == application_id)
        res = await db.execute(stmt)
        application = res.scalar_one_or_none()
        if not application:
            return None

        current_tasks = list(application.tasks or [])
        updated = []
        for t in current_tasks:
            if t.get("id") == task_id:
                curr = t.get("status", "PENDING")
                target = new_status if new_status else ("COMPLETED" if curr == "PENDING" else "PENDING")
                completed_at = datetime.utcnow().strftime("%b %d, %H:%M") if target == "COMPLETED" else None
                updated.append({**t, "status": target, "completed_at": completed_at})
            else:
                updated.append(t)

        application.tasks = updated
        await db.commit()
        await db.refresh(application)
        return application
