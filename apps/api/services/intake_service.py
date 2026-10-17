"""
OpportunityOS — Candidate Intake & Answer Bank Service
The intake is filled once; every form answer and LinkedIn edit is generated from it.
"""

import io
import re
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.models import CandidateIntakeModel
from apps.api.services.profile_service import ProfileService
from packages.answer_bank import AnswerBank

SECTIONS = ("identity", "targeting", "documents", "screening", "accounts", "linkedin")

# Fields the automation cannot work without, per section.
REQUIRED_FIELDS: Dict[str, List[str]] = {
    "identity": ["full_name", "email", "phone", "country", "timezone", "linkedin_url"],
    "targeting": ["target_titles", "seniority", "remote_scope", "daily_cap"],  # no salary floor = any pay
    "documents": ["master_resume_path"],
    "screening": ["work_authorization", "needs_sponsorship", "about_short"],
    "accounts": [],
    "linkedin": ["positioning", "topics"],
}

DEFAULT_DAILY_CAP = 15

RESUME_TYPES = (".pdf", ".docx")
MAX_RESUME_BYTES = 10 * 1024 * 1024

# Keys that must never be stored: logins live only in the candidate's browser profile.
_FORBIDDEN_KEYS = ("password", "passwd", "cookie", "li_at", "token", "secret")


def _is_filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, (list, dict, str)):
        return len(value) > 0
    return True


def _strip_secrets(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            k: _strip_secrets(v)
            for k, v in data.items()
            if not any(bad in str(k).lower() for bad in _FORBIDDEN_KEYS)
        }
    if isinstance(data, list):
        return [_strip_secrets(v) for v in data]
    return data


class IntakeService:
    @staticmethod
    async def get_or_create(db: AsyncSession, user_id: Optional[str] = None) -> CandidateIntakeModel:
        stmt = select(CandidateIntakeModel)
        if user_id:
            stmt = stmt.where(CandidateIntakeModel.user_id == user_id)
        stmt = stmt.order_by(CandidateIntakeModel.updated_at.desc()).limit(1)
        res = await db.execute(stmt)
        intake = res.scalar_one_or_none()
        if intake:
            return intake

        if user_id:
            # Single-candidate setup: a signed-in user takes over an intake saved before sign-in,
            # so the UI, the worker and the API always read the same answer bank.
            res = await db.execute(
                select(CandidateIntakeModel)
                .where(CandidateIntakeModel.user_id.is_(None))
                .order_by(CandidateIntakeModel.updated_at.desc())
                .limit(1)
            )
            unowned = res.scalar_one_or_none()
            if unowned:
                unowned.user_id = user_id
                await db.commit()
                await db.refresh(unowned)
                return unowned

        intake = CandidateIntakeModel(
            user_id=user_id,
            identity={},
            targeting={"daily_cap": DEFAULT_DAILY_CAP, "remote_scope": "WORLDWIDE"},
            documents={},
            screening={},
            accounts={},
            linkedin={},
        )
        db.add(intake)
        await db.commit()
        await db.refresh(intake)
        return intake

    @staticmethod
    async def update(
        db: AsyncSession, sections: Dict[str, Dict[str, Any]], user_id: Optional[str] = None
    ) -> CandidateIntakeModel:
        intake = await IntakeService.get_or_create(db, user_id=user_id)
        for section in SECTIONS:
            if section in sections and sections[section] is not None:
                merged = dict(getattr(intake, section) or {})
                merged.update(_strip_secrets(sections[section]))
                setattr(intake, section, merged)
        intake.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(intake)
        return intake

    @staticmethod
    async def save_resume(
        db: AsyncSession, filename: str, content: bytes, variant: Optional[str] = None, user_id: Optional[str] = None
    ) -> CandidateIntakeModel:
        """Stores an uploaded resume on this Mac, where the worker uploads it from, and points the intake at it."""
        from apps.worker.automation import OOS_HOME

        suffix = Path(filename or "").suffix.lower()
        if suffix not in RESUME_TYPES:
            raise ValueError("Upload a PDF or Word (.docx) file.")
        if not content:
            raise ValueError("The file is empty.")
        if len(content) > MAX_RESUME_BYTES:
            raise ValueError("Resume files must be under 10 MB.")
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).stem).strip("-.") or "resume"
        variant = (variant or "").strip()
        folder = (OOS_HOME / "resumes").resolve()
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{re.sub(r'[^A-Za-z0-9_-]+', '-', variant) + '-' if variant else ''}{name}{suffix}"
        path.write_bytes(content)

        documents = dict((await IntakeService.get_or_create(db, user_id=user_id)).documents or {})
        if variant:
            documents["resume_variants"] = {**(documents.get("resume_variants") or {}), variant: str(path)}
        else:
            documents["master_resume_path"] = str(path)
        return await IntakeService.update(db, {"documents": documents}, user_id=user_id)

    @staticmethod
    def resume_text(intake: CandidateIntakeModel) -> str:
        """Plain text of the master resume (PDF, .docx or text), or "" when it can't be read."""
        from apps.api.services.onboarding_service import OnboardingService

        path = Path((intake.documents or {}).get("master_resume_path") or "").expanduser()
        if not path.is_file() or path.stat().st_size > MAX_RESUME_BYTES:
            return ""
        content = path.read_bytes()
        if path.suffix.lower() == ".docx":
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
                return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", xml.replace("</w:p>", "\n"))).strip()
            except (zipfile.BadZipFile, KeyError):
                return ""
        return OnboardingService.extract_text_from_file(content, path.name)

    @staticmethod
    async def draft_texts(db: AsyncSession, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Drafts of the "about you" and "why this company" answers, for the candidate to edit and save."""
        from apps.api.services.linkedin_optimizer_service import LinkedInOptimizerService
        from packages.ai.intake_writer import write_intake_texts
        from packages.ai.llm import llm_available, provider_label

        intake = await IntakeService.get_or_create(db, user_id=user_id)
        facts = (await LinkedInOptimizerService.candidate_facts(db)).model_dump()
        facts["location"] = {k: (intake.identity or {}).get(k) for k in ("city", "country", "timezone")}
        resume = IntakeService.resume_text(intake)
        drafts = await write_intake_texts(facts, resume, use_ai=llm_available())
        return {"drafts": drafts, "used_resume": bool(resume.strip()), "ai_provider": provider_label()}

    @staticmethod
    def completeness(intake: CandidateIntakeModel) -> Dict[str, Any]:
        missing: Dict[str, List[str]] = {}
        total = filled = 0
        for section, fields in REQUIRED_FIELDS.items():
            data = getattr(intake, section) or {}
            gaps = [f for f in fields if not _is_filled(data.get(f))]
            missing[section] = gaps
            total += len(fields)
            filled += len(fields) - len(gaps)
        return {
            "percent": round(100 * filled / total) if total else 100,
            "missing": missing,
            "ready_for_automation": filled == total,
        }

    @staticmethod
    def to_dict(intake: CandidateIntakeModel) -> Dict[str, Any]:
        data = {section: getattr(intake, section) or {} for section in SECTIONS}
        data["id"] = intake.id
        data["user_id"] = intake.user_id
        data["updated_at"] = intake.updated_at.isoformat() + "Z" if intake.updated_at else None
        data["completeness"] = IntakeService.completeness(intake)
        return data

    @staticmethod
    async def build_answer_bank(
        db: AsyncSession,
        user_id: Optional[str] = None,
        resume_variant: Optional[str] = None,
        cover_note: Optional[str] = None,
        role: Optional[str] = None,
        job_answers: Optional[Dict[str, str]] = None,
        company: Optional[str] = None,
    ) -> AnswerBank:
        intake = await IntakeService.get_or_create(db, user_id=user_id)
        profile_facts: Dict[str, Any] = {}
        profile = await ProfileService.get_or_create_profile(db, user_id=user_id)
        if profile and profile.work_experiences:
            current = next((e for e in profile.work_experiences if e.is_current), None)
            if current:
                profile_facts = {"current_company": current.company, "current_title": current.role}

        custom = {
            a.question_canonical: a.answer_text
            for a in await ProfileService.get_verified_answers(db)
            if a.is_verified
        }
        return AnswerBank.from_intake(
            {section: getattr(intake, section) or {} for section in SECTIONS},
            profile=profile_facts,
            resume_variant=resume_variant,
            cover_note=cover_note,
            custom_answers=custom,
            role=role,
            job_answers=job_answers,
            company=company,
        )
