"""
OpportunityOS — Contact & Outreach CRM Service
Manages hiring contacts, personalized outreach sequences, and follow-up drip schedules.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from apps.api.models import (
    ContactModel,
    OutreachSequenceModel,
    OutreachMessageModel,
    OpportunityModel,
)
from packages.domain.models import AuditEventType, RelationshipStatus
from apps.api.services.activity_service import ActivityService


class CRMService:
    @staticmethod
    async def get_contacts(db: AsyncSession, limit: int = 50) -> List[ContactModel]:
        stmt = (
            select(ContactModel)
            .options(selectinload(ContactModel.opportunity))
            .order_by(desc(ContactModel.created_at))
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def create_contact(
        db: AsyncSession,
        company_name: str,
        full_name: str,
        role: str,
        email: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        github_url: Optional[str] = None,
        associated_opportunity_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ContactModel:
        contact = ContactModel(
            id=str(uuid.uuid4()),
            company_name=company_name,
            full_name=full_name,
            role=role,
            email=email,
            linkedin_url=linkedin_url,
            github_url=github_url,
            associated_opportunity_id=associated_opportunity_id,
            relationship_status="NEW",
            notes=notes,
        )
        db.add(contact)
        await db.commit()
        await db.refresh(contact)

        await ActivityService.record_event(
            db=db,
            entity_type="CONTACT",
            entity_id=contact.id,
            action=AuditEventType.CONTACT_FOUND,
            reason=f"Identified {role} ({full_name}) for {company_name}",
            output_payload={"contact_id": contact.id, "company": company_name},
        )
        return contact

    @staticmethod
    async def create_outreach_sequence(
        db: AsyncSession,
        opportunity_id: str,
        contact_id: str,
        candidate_name: Optional[str] = None,
        candidate_skills: Optional[str] = None,
    ) -> OutreachSequenceModel:
        """Create a respectful 3-step outreach & follow-up sequence."""
        # Resolve real candidate details from DB profile
        if not candidate_name or not candidate_skills:
            from apps.api.models import CandidateProfileModel
            prof_res = await db.execute(select(CandidateProfileModel).order_by(CandidateProfileModel.created_at.desc()).limit(1))
            profile = prof_res.scalar_one_or_none()
            if profile:
                candidate_name = candidate_name or profile.full_name
                candidate_skills = candidate_skills or "Full Stack & Cloud Systems"
            else:
                candidate_name = candidate_name or "Candidate"
                candidate_skills = candidate_skills or "Software Engineering"

        # Fetch contact and opportunity
        contact_res = await db.execute(select(ContactModel).where(ContactModel.id == contact_id))
        contact = contact_res.scalar_one_or_none()
        opp_res = await db.execute(select(OpportunityModel).where(OpportunityModel.id == opportunity_id))
        opp = opp_res.scalar_one_or_none()

        seq = OutreachSequenceModel(
            id=str(uuid.uuid4()),
            opportunity_id=opportunity_id,
            contact_id=contact_id,
            status="ACTIVE",
            current_step=1,
        )
        db.add(seq)
        await db.flush()

        now = datetime.utcnow()
        comp_name = opp.company_name if opp else (contact.company_name if contact else "your team")
        opp_title = opp.title if opp else "Software Engineering"

        # Step 1: Day 1 Introduction
        msg1 = OutreachMessageModel(
            id=str(uuid.uuid4()),
            sequence_id=seq.id,
            step_number=1,
            channel="EMAIL",
            subject=f"Regarding {opp_title} at {comp_name} — {candidate_name}",
            body=(
                f"Hi {contact.full_name.split()[0] if contact else 'there'},\n\n"
                f"I submitted an application for the {opp_title} opening at {comp_name} and wanted to reach out directly. "
                f"With deep experience architecting high-throughput full stack systems in {candidate_skills}, "
                f"I've delivered similar technical outcomes and would love to contribute to your roadmap.\n\n"
                f"Happy to share relevant code samples or discuss anytime.\n\n"
                f"Best,\n{candidate_name}"
            ),
            scheduled_for=now + timedelta(days=1),
            status="PENDING",
        )
        db.add(msg1)

        # Step 2: Day 4 Value Add Follow-up
        msg2 = OutreachMessageModel(
            id=str(uuid.uuid4()),
            sequence_id=seq.id,
            step_number=2,
            channel="EMAIL",
            subject=f"Re: Regarding {opp_title} at {comp_name}",
            body=(
                f"Hi {contact.full_name.split()[0] if contact else 'there'},\n\n"
                f"Quick follow-up on my note earlier this week regarding the {opp_title} role. "
                f"I recently documented a case study on optimizing streaming architecture that directly parallels "
                f"the technical challenges at {comp_name}.\n\n"
                f"Let me know if you have 10 minutes next week to connect.\n\n"
                f"Best,\n{candidate_name}"
            ),
            scheduled_for=now + timedelta(days=4),
            status="PENDING",
        )
        db.add(msg2)

        # Step 3: Day 9 Final Check-in
        msg3 = OutreachMessageModel(
            id=str(uuid.uuid4()),
            sequence_id=seq.id,
            step_number=3,
            channel="EMAIL",
            subject=f"Re: Regarding {opp_title} at {comp_name}",
            body=(
                f"Hi {contact.full_name.split()[0] if contact else 'there'},\n\n"
                f"I know how busy engineering hiring gets, so I will keep this brief! If the {opp_title} position "
                f"has already moved forward, no problem at all. I would still love to stay connected for future opportunities.\n\n"
                f"All the best,\n{candidate_name}"
            ),
            scheduled_for=now + timedelta(days=9),
            status="PENDING",
        )
        db.add(msg3)

        await db.commit()

        stmt = (
            select(OutreachSequenceModel)
            .options(selectinload(OutreachSequenceModel.messages))
            .where(OutreachSequenceModel.id == seq.id)
        )
        seq_res = await db.execute(stmt)
        seq_loaded = seq_res.scalar_one()

        await ActivityService.record_event(
            db=db,
            entity_type="OUTREACH_SEQUENCE",
            entity_id=seq.id,
            action=AuditEventType.OUTREACH_PREPARED,
            reason=f"Staged 3-step outreach sequence for {contact.full_name if contact else 'contact'}.",
            output_payload={"sequence_id": seq.id, "steps": 3},
        )
        return seq_loaded

    @staticmethod
    async def get_outreach_sequences(db: AsyncSession) -> List[OutreachSequenceModel]:
        stmt = (
            select(OutreachSequenceModel)
            .options(selectinload(OutreachSequenceModel.messages))
            .order_by(desc(OutreachSequenceModel.created_at))
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def send_message(db: AsyncSession, message_id: str) -> OutreachMessageModel:
        stmt = (
            select(OutreachMessageModel)
            .options(selectinload(OutreachMessageModel.sequence))
            .where(OutreachMessageModel.id == message_id)
        )
        res = await db.execute(stmt)
        msg = res.scalar_one_or_none()
        if not msg:
            raise ValueError(f"Message {message_id} not found")

        msg.status = "SENT"
        msg.sent_at = datetime.utcnow()

        if msg.sequence and msg.sequence.contact_id:
            contact_res = await db.execute(select(ContactModel).where(ContactModel.id == msg.sequence.contact_id))
            contact = contact_res.scalar_one_or_none()
            if contact:
                contact.relationship_status = "CONTACTED"
                contact.last_interaction_at = datetime.utcnow()

        await db.commit()
        await db.refresh(msg)

        await ActivityService.record_event(
            db=db,
            entity_type="OUTREACH_MESSAGE",
            entity_id=msg.id,
            action="OUTREACH_EMAIL_DISPATCHED",
            reason=f"Dispatched Step {msg.step_number} outreach email: '{msg.subject}'",
            output_payload={"message_id": msg.id, "subject": msg.subject, "channel": msg.channel},
        )
        return msg
