"""
OpportunityOS — Audit & Real-time Activity Service
Guarantees that every action has an immutable audit log entry.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from apps.api.models import AuditEventModel
from packages.domain.models import AuditEvent, AuditEventType


class ActivityService:
    @staticmethod
    async def record_event(
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        action: AuditEventType | str,
        actor: str = "SYSTEM_AGENT",
        reason: Optional[str] = None,
        input_payload: Optional[Dict[str, Any]] = None,
        output_payload: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        latency_ms: int = 0,
    ) -> AuditEventModel:
        action_str = action.value if hasattr(action, "value") else str(action)
        event = AuditEventModel(
            timestamp=datetime.utcnow(),
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action_str,
            actor=actor,
            reason=reason,
            input_payload=input_payload or {},
            output_payload=output_payload or {},
            status=status,
            latency_ms=latency_ms,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def get_recent_activity(
        db: AsyncSession,
        limit: int = 50,
        entity_type: Optional[str] = None,
    ) -> List[AuditEventModel]:
        stmt = select(AuditEventModel).order_by(desc(AuditEventModel.timestamp)).limit(limit)
        if entity_type:
            stmt = stmt.where(AuditEventModel.entity_type == entity_type)
        res = await db.execute(stmt)
        return list(res.scalars().all())
