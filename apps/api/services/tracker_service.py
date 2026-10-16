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
    "SUBMITTED",
    "VIEWED",
    "REPLIED",
    "INTERVIEW",
    "OFFER",
    "REJECTED",
    "GHOSTED",
]
FOLLOW_UP_AFTER_DAYS = 7

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
