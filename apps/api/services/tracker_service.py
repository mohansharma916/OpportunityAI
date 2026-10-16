"""
OpportunityOS — Application Tracker Service
One row per application across every channel, de-duplicated by company + role.
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from apps.api.models import TrackedApplicationModel
from apps.api.services.activity_service import ActivityService

STATUSES = [
    "QUEUED",
    "PAUSED",
    "AWAITING_APPROVAL",
    "APPROVED",
    "SUBMITTED",
    "VIEWED",
    "REPLIED",
    "INTERVIEW",
    "OFFER",
    "REJECTED",
    "GHOSTED",
]
FOLLOW_UP_AFTER_DAYS = 7
MAX_FOLLOW_UPS = 2
TRUSTED_AFTER_CLEAN_SUBMITS = 20

_EDITABLE = {
    "company", "role", "job_url", "source_platform", "apply_channel", "opportunity_id", "post_url",
    "match_score", "resume_variant", "cover_note", "status", "submitted_at", "evidence",
    "next_action", "next_action_due", "contact_name", "contact_url", "notes", "last_error",
}


class DuplicateApplicationError(Exception):
    def __init__(self, existing: TrackedApplicationModel):
        super().__init__(f"Already tracked: {existing.company} — {existing.role} ({existing.status})")
        self.existing = existing


def make_dedup_key(company: str, role: str) -> str:
    def norm(text: str) -> str:
        text = re.sub(r"\b(inc|llc|ltd|gmbh|corp|co)\b\.?", "", (text or "").lower())
        return re.sub(r"[^a-z0-9]+", " ", text).strip()
    return f"{norm(company)}|{norm(role)}"


def _parse_dt(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)


class TrackerService:
    @staticmethod
    def to_dict(row: TrackedApplicationModel) -> Dict[str, Any]:
        def iso(dt: Optional[datetime]) -> Optional[str]:
            return dt.isoformat() + "Z" if dt else None
        return {
            "id": row.id,
            "company": row.company,
            "role": row.role,
            "job_url": row.job_url,
            "source_platform": row.source_platform,
            "apply_channel": row.apply_channel,
            "opportunity_id": row.opportunity_id,
            "post_url": row.post_url,
            "match_score": row.match_score,
            "resume_variant": row.resume_variant,
            "cover_note": row.cover_note,
            "status": row.status,
            "submitted_at": iso(row.submitted_at),
            "evidence": row.evidence or [],
            "next_action": row.next_action,
            "next_action_due": iso(row.next_action_due),
            "contact_name": row.contact_name,
            "contact_url": row.contact_url,
            "notes": row.notes,
            "last_error": row.last_error,
            "form": row.form,
            "follow_ups": row.follow_ups or 0,
            "created_at": iso(row.created_at),
            "updated_at": iso(row.updated_at),
        }

    @staticmethod
    async def find_duplicate(db: AsyncSession, company: str, role: str) -> Optional[TrackedApplicationModel]:
        res = await db.execute(
            select(TrackedApplicationModel).where(TrackedApplicationModel.dedup_key == make_dedup_key(company, role))
        )
        return res.scalar_one_or_none()

    @staticmethod
    def _apply_fields(row: TrackedApplicationModel, data: Dict[str, Any]) -> None:
        for key, value in data.items():
            if key not in _EDITABLE:
                continue
            if key == "status":
                value = str(value).upper()
                if value not in STATUSES:
                    raise ValueError(f"Unknown status '{value}'. Use one of: {', '.join(STATUSES)}")
            if key in ("submitted_at", "next_action_due"):
                value = _parse_dt(value)
            setattr(row, key, value)

        if row.status == "SUBMITTED" and not row.submitted_at:
            row.submitted_at = datetime.utcnow()
        if row.status == "SUBMITTED" and not row.next_action_due:
            row.next_action = row.next_action or "Follow up"
            row.next_action_due = row.submitted_at + timedelta(days=FOLLOW_UP_AFTER_DAYS)

    @staticmethod
    async def create(db: AsyncSession, data: Dict[str, Any]) -> TrackedApplicationModel:
        company = (data.get("company") or "").strip()
        role = (data.get("role") or "").strip()
        if not company or not role:
            raise ValueError("company and role are required")

        existing = await TrackerService.find_duplicate(db, company, role)
        if existing:
            raise DuplicateApplicationError(existing)

        row = TrackedApplicationModel(
            dedup_key=make_dedup_key(company, role),
            company=company,
            role=role,
            source_platform=data.get("source_platform") or "MANUAL",
            status="QUEUED",
            evidence=[],
        )
        TrackerService._apply_fields(row, {k: v for k, v in data.items() if k not in ("company", "role")})
        db.add(row)
        await db.commit()
        await db.refresh(row)

        await ActivityService.record_event(
            db=db,
            entity_type="TRACKED_APPLICATION",
            entity_id=row.id,
            action="APPLICATION_TRACKED",
            actor="USER" if row.source_platform == "MANUAL" else "SYSTEM_AGENT",
            reason=f"Tracking {row.company} — {row.role} ({row.status})",
        )
        return row

    @staticmethod
    async def get(db: AsyncSession, row_id: str) -> Optional[TrackedApplicationModel]:
        res = await db.execute(select(TrackedApplicationModel).where(TrackedApplicationModel.id == row_id))
        return res.scalar_one_or_none()

    @staticmethod
    async def list(
        db: AsyncSession,
        status: Optional[str] = None,
        source_platform: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[TrackedApplicationModel]:
        stmt = select(TrackedApplicationModel).order_by(TrackedApplicationModel.updated_at.desc())
        if status:
            stmt = stmt.where(TrackedApplicationModel.status == status.upper())
        if source_platform:
            stmt = stmt.where(TrackedApplicationModel.source_platform == source_platform)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                TrackedApplicationModel.company.ilike(like) | TrackedApplicationModel.role.ilike(like)
            )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, row_id: str, data: Dict[str, Any]) -> TrackedApplicationModel:
        row = await TrackerService.get(db, row_id)
        if not row:
            raise LookupError(f"Application {row_id} not found")
        old_status = row.status
        if "company" in data or "role" in data:
            company = data.get("company", row.company)
            role = data.get("role", row.role)
            dup = await TrackerService.find_duplicate(db, company, role)
            if dup and dup.id != row.id:
                raise DuplicateApplicationError(dup)
            row.dedup_key = make_dedup_key(company, role)
        TrackerService._apply_fields(row, data)
        row.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(row)

        if row.status != old_status:
            await ActivityService.record_event(
                db=db,
                entity_type="TRACKED_APPLICATION",
                entity_id=row.id,
                action="APPLICATION_STATUS_CHANGED",
                reason=f"{row.company} — {row.role}: {old_status} -> {row.status}",
            )
        return row

    @staticmethod
    async def add_evidence(db: AsyncSession, row_id: str, item: str) -> TrackedApplicationModel:
        row = await TrackerService.get(db, row_id)
        if not row:
            raise LookupError(f"Application {row_id} not found")
        row.evidence = list(row.evidence or []) + [item]
        await db.commit()
        await db.refresh(row)
        return row

    @staticmethod
    async def delete(db: AsyncSession, row_id: str) -> bool:
        row = await TrackerService.get(db, row_id)
        if not row:
            return False
        await db.delete(row)
        await db.commit()
        return True

    @staticmethod
    async def submitted_today(db: AsyncSession, now: Optional[datetime] = None) -> int:
        now = now or datetime.utcnow()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        res = await db.execute(
            select(func.count(TrackedApplicationModel.id)).where(TrackedApplicationModel.submitted_at >= start)
        )
        return int(res.scalar() or 0)

    @staticmethod
    async def stats(db: AsyncSession) -> Dict[str, Any]:
        rows = await TrackerService.list(db)
        now = datetime.utcnow()
        by_status = {s: 0 for s in STATUSES}
        by_source: Dict[str, int] = {}
        for r in rows:
            by_status[r.status] = by_status.get(r.status, 0) + 1
            by_source[r.source_platform] = by_source.get(r.source_platform, 0) + 1
        submitted = [r for r in rows if r.submitted_at]
        responded = [r for r in submitted if r.status in ("REPLIED", "INTERVIEW", "OFFER", "REJECTED")]
        return {
            "total": len(rows),
            "by_status": by_status,
            "by_source": by_source,
            "submitted_today": await TrackerService.submitted_today(db, now),
            "follow_ups_due": sum(
                1 for r in rows
                if r.next_action_due and r.next_action_due <= now
                and r.status in ("SUBMITTED", "VIEWED", "REPLIED")
            ),
            "response_rate": round(100 * len(responded) / len(submitted)) if submitted else None,
        }

    # ------------------------------------------------------------------
    # Apply workflow: fill report -> candidate answers -> approval -> submit
    # ------------------------------------------------------------------
    @staticmethod
    async def record_run(
        db: AsyncSession,
        row_id: str,
        result: Dict[str, Any],
        suggestions: Optional[Dict[str, Dict[str, Any]]] = None,
        submit: bool = False,
    ) -> TrackedApplicationModel:
        """Store a worker run (fill report + outcome) on the tracker row and move its status."""
        row = await TrackerService.get(db, row_id)
        if not row:
            raise LookupError(f"Application {row_id} not found")
        form = dict(row.form or {})
        unanswered = []
        for q in result.get("unanswered_fields") or []:
            q = dict(q)
            if suggestions and q.get("canonical") in suggestions:
                q["suggestion"] = suggestions[q["canonical"]]
            unanswered.append(q)
        form.update({
            "adapter": result.get("adapter"), "fields": result.get("fields") or [], "unanswered": unanswered,
            "fingerprint": result.get("fingerprint"), "details": result.get("details"),
            "step": result.get("step_reached"), "run_at": datetime.utcnow().isoformat() + "Z",
        })
        row.form = form
        row.evidence = list(row.evidence or []) + list(result.get("screenshots") or [])
        row.apply_channel = row.apply_channel or result.get("adapter")

        status = result.get("status")
        if status == "SUBMITTED":
            TrackerService._apply_fields(row, {"status": "SUBMITTED", "last_error": None})
        elif status == "FILLED":
            row.status, row.last_error, row.next_action = "AWAITING_APPROVAL", None, "Review the fill and approve"
        elif status == "NEEDS_CANDIDATE":
            row.status, row.last_error = "PAUSED", result.get("details")
            row.next_action = "Answer the open questions" if unanswered else "Candidate action needed"
        else:
            row.last_error = result.get("details")
        row.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(row)
        await ActivityService.record_event(
            db=db, entity_type="TRACKED_APPLICATION", entity_id=row.id,
            action="APPLICATION_SUBMIT_RUN" if submit else "APPLICATION_FILL_RUN",
            reason=f"{row.company} — {row.role}: {status} ({result.get('step_reached')})",
        )
        return row

    @staticmethod
    async def submit_answers(db: AsyncSession, row_id: str, answers: Dict[str, str]) -> TrackedApplicationModel:
        """Candidate answers to open questions: saved to the answer bank, then the row is re-filled."""
        from apps.api.services.profile_service import ProfileService

        row = await TrackerService.get(db, row_id)
        if not row:
            raise LookupError(f"Application {row_id} not found")
        form = dict(row.form or {})
        labels = {q.get("canonical"): q.get("label") for q in form.get("unanswered") or []}
        saved = 0
        for canonical, value in answers.items():
            if canonical not in labels:
                raise ValueError(f"'{canonical}' is not an open question on this application")
            if value is None or not str(value).strip():
                continue
            await ProfileService.save_or_update_answer(
                db, question_text=labels[canonical], answer_text=str(value), question_canonical=canonical,
                source="CANDIDATE",
            )
            saved += 1
        form["manual_answers"] = int(form.get("manual_answers") or 0) + saved
        row.form = form
        if saved:
            row.status, row.next_action = "QUEUED", "Worker re-fills with your answers"
        row.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(row)
        return row

    @staticmethod
    async def approve(db: AsyncSession, row_id: str) -> TrackedApplicationModel:
        row = await TrackerService.get(db, row_id)
        if not row:
            raise LookupError(f"Application {row_id} not found")
        form = dict(row.form or {})
        if row.status != "AWAITING_APPROVAL" or not form.get("fingerprint"):
            raise ValueError("Only a filled form awaiting approval can be approved.")
        form["approved_fingerprint"] = form["fingerprint"]
        form["approved_at"] = datetime.utcnow().isoformat() + "Z"
        row.form = form
        row.status, row.next_action = "APPROVED", "Worker submits it"
        await db.commit()
        await db.refresh(row)
        await ActivityService.record_event(
            db=db, entity_type="TRACKED_APPLICATION", entity_id=row.id, action="APPLICATION_APPROVED",
            actor="USER", reason=f"{row.company} — {row.role} approved for submission",
        )
        return row

    @staticmethod
    async def clean_submits(db: AsyncSession, channel: Optional[str]) -> int:
        """Submitted applications on this ATS that needed no answers from the candidate."""
        if not channel:
            return 0
        rows = await TrackerService.list(db, status="SUBMITTED")
        return sum(1 for r in rows if r.apply_channel == channel and r.form
                   and r.form.get("approved_fingerprint") and not r.form.get("manual_answers"))

    @staticmethod
    async def is_trusted(db: AsyncSession, channel: Optional[str], enabled: bool) -> bool:
        return enabled and await TrackerService.clean_submits(db, channel) >= TRUSTED_AFTER_CLEAN_SUBMITS

    @staticmethod
    def follow_up_message(row: TrackedApplicationModel, candidate_name: str) -> str:
        first = (row.contact_name or "").split(" ")[0] or "there"
        days = (datetime.utcnow() - row.submitted_at).days if row.submitted_at else FOLLOW_UP_AFTER_DAYS
        return (
            f"Hi {first}, I applied for the {row.role} role at {row.company} {days} days ago and wanted to check in. "
            f"I'm still very interested and happy to share more about my work. Thanks for your time! — {candidate_name}"
        )

    @staticmethod
    async def follow_ups_due(db: AsyncSession, candidate_name: str = "") -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        rows = [r for r in await TrackerService.list(db)
                if r.status in ("SUBMITTED", "VIEWED") and r.next_action_due and r.next_action_due <= now]
        return [{**TrackerService.to_dict(r), "message": TrackerService.follow_up_message(r, candidate_name)} for r in rows]

    @staticmethod
    async def mark_followed_up(db: AsyncSession, row_id: str, note: Optional[str] = None) -> TrackedApplicationModel:
        row = await TrackerService.get(db, row_id)
        if not row:
            raise LookupError(f"Application {row_id} not found")
        row.follow_ups = (row.follow_ups or 0) + 1
        stamp = datetime.utcnow().strftime("%Y-%m-%d")
        row.notes = "\n".join(x for x in [row.notes, f"{stamp}: followed up" + (f" — {note}" if note else "")] if x)
        if row.follow_ups >= MAX_FOLLOW_UPS:
            row.next_action, row.next_action_due = "No reply after 2 follow-ups; mark as ghosted?", None
        else:
            row.next_action, row.next_action_due = "Follow up again", datetime.utcnow() + timedelta(days=FOLLOW_UP_AFTER_DAYS)
        await db.commit()
        await db.refresh(row)
        return row
