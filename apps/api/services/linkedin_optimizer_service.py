"""
OpportunityOS — LinkedIn Profile Optimizer Service
Snapshot -> audit -> grounded drafts -> candidate approval -> applied (worker or by hand).
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models import LinkedInProfileDraftModel, LinkedInProfileSnapshotModel, OpportunityModel
from apps.api.services.activity_service import ActivityService
from apps.api.services.intake_service import SECTIONS, IntakeService
from apps.api.services.profile_service import ProfileService
from packages.linkedin_optimizer import (
    CandidateFacts,
    ProfileSnapshot,
    build_drafts,
    parse_export,
    run_audit,
    top_keywords,
)

DECISIONS = ("APPROVE", "REJECT", "REOPEN", "MARK_APPLIED")


class LinkedInOptimizerService:
    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------
    @staticmethod
    async def save_snapshot(db: AsyncSession, snapshot: ProfileSnapshot) -> LinkedInProfileSnapshotModel:
        row = LinkedInProfileSnapshotModel(source=snapshot.source, data=snapshot.model_dump())
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return row

    @staticmethod
    async def import_export(db: AsyncSession, path: Optional[str] = None) -> LinkedInProfileSnapshotModel:
        if not path:
            intake = await IntakeService.get_or_create(db)
            path = (intake.linkedin or {}).get("profile_export_path")
        if not path:
            raise ValueError("No export path given. Set it in the intake (section F) or pass one.")
        return await LinkedInOptimizerService.save_snapshot(db, parse_export(path))

    @staticmethod
    async def latest_snapshot(db: AsyncSession) -> Optional[LinkedInProfileSnapshotModel]:
        res = await db.execute(
            select(LinkedInProfileSnapshotModel).order_by(LinkedInProfileSnapshotModel.captured_at.desc()).limit(1)
        )
        return res.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Facts & keywords
    # ------------------------------------------------------------------
    @staticmethod
    async def candidate_facts(db: AsyncSession) -> CandidateFacts:
        intake = await IntakeService.get_or_create(db)
        identity, targeting, linkedin = intake.identity or {}, intake.targeting or {}, intake.linkedin or {}
        profile = await ProfileService.get_or_create_profile(db)

        experiences: List[Dict[str, Any]] = []
        wins: List[str] = []
        skills: List[str] = []
        if profile:
            skills = [s.skill_name for s in profile.skills]
            roles = sorted(profile.work_experiences, key=lambda e: (bool(e.is_current), str(e.start_date)), reverse=True)
            for e in roles:
                achievements = [a for a in (e.key_achievements or []) if isinstance(a, str) and a.strip()]
                experiences.append({
                    "company": e.company, "role": e.role,
                    "achievements": achievements, "technologies": e.technologies or [],
                })
                wins.extend(a for a in achievements if re.search(r"\d", a))
            wins.extend(k.quantified_impact for k in profile.knowledge_items if k.quantified_impact)

        return CandidateFacts(
            full_name=identity.get("full_name") or (profile.full_name if profile else ""),
            email=identity.get("email") or (profile.email if profile else None),
            target_titles=targeting.get("target_titles") or (profile.target_roles if profile else []) or [],
            positioning=linkedin.get("positioning"),
            topics=linkedin.get("topics") or [],
            skills=skills,
            years_experience=targeting.get("years_experience"),
            wins=list(dict.fromkeys(wins)),
            experiences=experiences,
            github_url=identity.get("github_url"),
            portfolio_url=identity.get("portfolio_url"),
        )

    @staticmethod
    async def keywords(db: AsyncSession, facts: CandidateFacts) -> Dict[str, Any]:
        res = await db.execute(select(OpportunityModel).order_by(OpportunityModel.created_at.desc()).limit(500))
        opps = [
            {"title": o.title, "required_skills": o.required_skills, "preferred_skills": o.preferred_skills}
            for o in res.scalars().all()
        ]
        found = top_keywords(opps, facts.target_titles)
        if found:
            return {"keywords": found, "source": f"{len(opps)} discovered jobs"}
        return {"keywords": facts.skills[:15], "source": "your own skills (run job discovery for market keywords)"}

    # ------------------------------------------------------------------
    # Audit + drafts
    # ------------------------------------------------------------------
    @staticmethod
    async def analyze(db: AsyncSession, use_claude: Optional[bool] = None) -> Dict[str, Any]:
        row = await LinkedInOptimizerService.latest_snapshot(db)
        if not row:
            raise LookupError("No profile snapshot yet. Run the live profile audit or import your LinkedIn export.")
        snapshot = ProfileSnapshot.model_validate(row.data)
        intake = await IntakeService.get_or_create(db)
        facts = await LinkedInOptimizerService.candidate_facts(db)
        kw = await LinkedInOptimizerService.keywords(db, facts)

        report = run_audit(snapshot, {s: getattr(intake, s) or {} for s in SECTIONS}, kw["keywords"])
        drafts = build_drafts(snapshot, facts, kw["keywords"], report.missing_keywords)

        from packages.ai.claude_drafter import claude_available, polish_drafts
        if use_claude is None:
            use_claude = claude_available()
        if use_claude and drafts:
            drafts = await polish_drafts(facts, kw["keywords"], drafts)

        row.audit = {**report.model_dump(), "keywords_source": kw["source"]}

        pending = await db.execute(
            select(LinkedInProfileDraftModel).where(LinkedInProfileDraftModel.status == "PENDING")
        )
        for old in pending.scalars().all():
            old.status = "SUPERSEDED"
        for d in drafts:
            db.add(LinkedInProfileDraftModel(
                snapshot_id=row.id, section=d.section, title=d.title, current_value=d.current,
                proposed_value=d.proposed, alternatives=d.alternatives, rationale=d.rationale,
                instructions=d.instructions, apply_mode=d.apply_mode, char_limit=d.char_limit,
                generated_by=d.generated_by, status="PENDING", evidence=[],
            ))
        await db.commit()

        await ActivityService.record_event(
            db=db, entity_type="LINKEDIN_PROFILE", entity_id=row.id, action="PROFILE_AUDITED",
            reason=f"Score {report.overall_score}/100 from {snapshot.source}; {len(drafts)} drafts",
        )
        return await LinkedInOptimizerService.state(db)

    # ------------------------------------------------------------------
    # Drafts
    # ------------------------------------------------------------------
    @staticmethod
    def draft_dict(d: LinkedInProfileDraftModel) -> Dict[str, Any]:
        return {
            "id": d.id, "section": d.section, "title": d.title,
            "current_value": d.current_value, "proposed_value": d.proposed_value,
            "alternatives": d.alternatives or [], "rationale": d.rationale, "instructions": d.instructions,
            "apply_mode": d.apply_mode, "char_limit": d.char_limit, "generated_by": d.generated_by,
            "status": d.status, "last_error": d.last_error, "evidence": d.evidence or [],
            "applied_at": d.applied_at.isoformat() + "Z" if d.applied_at else None,
        }

    @staticmethod
    async def get_draft(db: AsyncSession, draft_id: str) -> Optional[LinkedInProfileDraftModel]:
        res = await db.execute(select(LinkedInProfileDraftModel).where(LinkedInProfileDraftModel.id == draft_id))
        return res.scalar_one_or_none()

    @staticmethod
    async def list_drafts(db: AsyncSession, status: Optional[str] = None) -> List[LinkedInProfileDraftModel]:
        stmt = select(LinkedInProfileDraftModel).where(LinkedInProfileDraftModel.status != "SUPERSEDED")
        if status:
            stmt = select(LinkedInProfileDraftModel).where(LinkedInProfileDraftModel.status == status)
        res = await db.execute(stmt.order_by(LinkedInProfileDraftModel.created_at))
        return list(res.scalars().all())

    @staticmethod
    async def decide(
        db: AsyncSession, draft_id: str, decision: str, value: Optional[str] = None
    ) -> LinkedInProfileDraftModel:
        draft = await LinkedInOptimizerService.get_draft(db, draft_id)
        if not draft:
            raise LookupError(f"Draft {draft_id} not found")
        decision = decision.upper()
        if decision not in DECISIONS:
            raise ValueError(f"Decision must be one of {', '.join(DECISIONS)}")

        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Text can't be empty")
            if draft.char_limit and len(value) > draft.char_limit:
                raise ValueError(f"{len(value)} characters; LinkedIn allows {draft.char_limit}")
            draft.proposed_value = value

        if decision == "APPROVE":
            draft.status = "APPROVED"
        elif decision == "REJECT":
            draft.status = "REJECTED"
        elif decision == "REOPEN":
            draft.status, draft.last_error = "PENDING", None
        elif decision == "MARK_APPLIED":
            draft.status, draft.applied_at = "APPLIED", datetime.utcnow()
        await db.commit()
        await db.refresh(draft)

        await ActivityService.record_event(
            db=db, entity_type="LINKEDIN_PROFILE", entity_id=draft.id, action=f"DRAFT_{draft.status}",
            actor="USER", reason=f"{draft.title}: {draft.status.lower()}",
        )
        return draft

    @staticmethod
    async def record_apply(
        db: AsyncSession, draft_id: str, ok: bool, error: Optional[str] = None, evidence: Optional[List[str]] = None
    ) -> LinkedInProfileDraftModel:
        draft = await LinkedInOptimizerService.get_draft(db, draft_id)
        if not draft:
            raise LookupError(f"Draft {draft_id} not found")
        draft.evidence = list(draft.evidence or []) + list(evidence or [])
        if ok:
            draft.status, draft.applied_at, draft.last_error = "APPLIED", datetime.utcnow(), None
        else:
            draft.status, draft.last_error = "FAILED", error
        await db.commit()
        await db.refresh(draft)
        return draft

    # ------------------------------------------------------------------
    # Page state
    # ------------------------------------------------------------------
    @staticmethod
    async def state(db: AsyncSession) -> Dict[str, Any]:
        from packages.ai.llm import provider_label

        row = await LinkedInOptimizerService.latest_snapshot(db)
        drafts = await LinkedInOptimizerService.list_drafts(db)
        return {
            "snapshot": {
                "id": row.id, "source": row.source, "captured_at": row.captured_at.isoformat() + "Z", "data": row.data,
            } if row else None,
            "audit": row.audit if row else None,
            "drafts": [LinkedInOptimizerService.draft_dict(d) for d in drafts],
            "ai_provider": provider_label(),
        }
