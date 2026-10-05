"""
OpportunityOS — Candidate Profile & Knowledge Base Service
"""

import uuid
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.api.models import (
    UserModel,
    CandidateProfileModel,
    CandidateSkillModel,
    KnowledgeItemModel,
    WorkExperienceModel,
    ApplicationAnswerModel,
)
from packages.domain.models import (
    CandidateProfile,
    CandidateSkill,
    KnowledgeItem,
    WorkExperience,
    SkillProficiency,
)


class ProfileService:
    @staticmethod
    async def get_or_create_profile(
        db: AsyncSession, seed_if_empty: bool = False, user_id: Optional[str] = None
    ) -> Optional[CandidateProfileModel]:
        # 1. If user_id provided, look for that specific user's profile
        if user_id:
            stmt = (
                select(CandidateProfileModel)
                .options(
                    selectinload(CandidateProfileModel.skills),
                    selectinload(CandidateProfileModel.knowledge_items),
                    selectinload(CandidateProfileModel.work_experiences),
                )
                .where(CandidateProfileModel.user_id == user_id)
                .limit(1)
            )
            res = await db.execute(stmt)
            profile = res.scalar_one_or_none()
            if profile:
                return profile

        # 2. Try to find the latest candidate profile
        stmt = (
            select(CandidateProfileModel)
            .options(
                selectinload(CandidateProfileModel.skills),
                selectinload(CandidateProfileModel.knowledge_items),
                selectinload(CandidateProfileModel.work_experiences),
            )
            .order_by(CandidateProfileModel.updated_at.desc(), CandidateProfileModel.created_at.desc())
            .limit(1)
        )
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()

        # If existing profile was populated with "Alex Morgan", update it to real user if available
        if profile and profile.full_name and profile.full_name.strip().lower() in ["alex", "alex morgan"]:
            u_stmt = select(UserModel).where(~UserModel.email.ilike("%alex.morgan%")).order_by(UserModel.created_at.desc()).limit(1)
            u_res = await db.execute(u_stmt)
            real_u = u_res.scalar_one_or_none()
            if real_u and real_u.full_name:
                profile.full_name = real_u.full_name
                profile.email = real_u.email
                if not profile.user_id:
                    profile.user_id = real_u.id
                await db.commit()
                await db.refresh(profile)

        if profile or not seed_if_empty:
            return profile

        # 3. Determine real name and email from UserModel if available
        seed_name = "Lead Engineer"
        seed_email = "engineer@opportunityos.internal"
        target_uid = user_id
        if target_uid:
            u_res = await db.execute(select(UserModel).where(UserModel.id == target_uid))
            u_match = u_res.scalar_one_or_none()
            if u_match:
                seed_name = u_match.full_name or seed_name
                seed_email = u_match.email or seed_email
        else:
            u_res = await db.execute(select(UserModel).where(~UserModel.email.ilike("%alex.morgan%")).order_by(UserModel.created_at.desc()).limit(1))
            u_latest = u_res.scalar_one_or_none()
            if u_latest:
                seed_name = u_latest.full_name or seed_name
                seed_email = u_latest.email or seed_email
                target_uid = u_latest.id

        # Seed initial rich profile
        profile = CandidateProfileModel(
            id=str(uuid.uuid4()),
            user_id=target_uid,
            full_name=seed_name,
            headline="Staff Full Stack & Distributed Systems Architect",
            email=seed_email,
            location="San Francisco, CA / Remote",
            country="United States",
            timezone="America/Los_Angeles",
            preferred_working_hours="08:00 - 17:00 PST",
            countries_willing_to_work=["US", "EU", "UK", "Canada", "Worldwide Remote"],
            target_roles=[
                "Staff Software Engineer",
                "Senior Full Stack Engineer",
                "Founding Engineer",
                "Contract Systems Architect",
                "Technical Lead",
            ],
            minimum_salary_annual=160000.0,
            minimum_hourly_rate=85.0,
            preferred_currencies=["USD", "EUR", "GBP"],
            remote_preference="REMOTE",
            timezone_overlap_hours=4,
            notice_period_days=14,
            visa_sponsorship_needed=False,
            authorized_countries=["US", "EU"],
            automation_level=3,
        )
        db.add(profile)
        await db.flush()

        # Seed skills with evidence
        skills_data = [
            ("React", 7.0, "EXPERT", ["Cinematic UI", "Next.js migration"], ["Next.js 14 App Router", "Server Components"]),
            ("TypeScript", 6.5, "EXPERT", ["Type-safe GraphQL", "Monorepo"], ["Strict mode libraries", "AST codemods"]),
            ("Python", 8.0, "EXPERT", ["FastAPI Microservices", "Asyncio runners"], ["Temporal orchestrators", "Pytest"]),
            ("FastAPI", 5.0, "EXPERT", ["Enterprise API gateways", "Pydantic v2"], ["OAuth2 RBAC", "Streaming sockets"]),
            ("PostgreSQL", 7.0, "ADVANCED", ["pgvector indexing", "Query optimization"], ["Read-replicas", "Connection pool"]),
            ("Docker", 6.0, "ADVANCED", ["Multi-stage builds", "Rootless containers"], ["DevOps pipeline", "Kubernetes"]),
            ("Temporal", 3.0, "ADVANCED", ["Durable workflows", "Saga orchestration"], ["Job apply workflow", "Retry signals"]),
            ("Redis", 5.5, "ADVANCED", ["Distributed locks", "Pub/sub caching"], ["Rate-limiting", "Session store"]),
            ("Playwright", 3.5, "ADVANCED", ["E2E automated testing", "Browser automation"], ["Resilient selectors", "Trace review"]),
        ]
        for name, yrs, prof, evidence, projs in skills_data:
            db.add(
                CandidateSkillModel(
                    profile_id=profile.id,
                    skill_name=name,
                    experience_years=yrs,
                    proficiency=prof,
                    evidence=evidence,
                    related_projects=projs,
                )
            )

        # Seed knowledge items with quantified impact
        knowledge_data = [
            (
                "Reduced Frontend Load Time by 42%",
                "Migrated legacy monolithic SPA to Next.js with React Server Components and edge caching, dropping P95 latency from 2.8s to 1.6s.",
                "ACCOMPLISHMENT",
                ["React", "Next.js", "Web Performance"],
                "42% latency reduction",
            ),
            (
                "Architected Real-Time Workflow Runner",
                "Designed distributed task orchestration layer using Python, FastAPI, and Temporal handling 100k+ asynchronous jobs daily with zero data loss.",
                "ARCHITECTURE",
                ["Python", "FastAPI", "Temporal", "Distributed Systems"],
                "100k+ daily durable events",
            ),
            (
                "Automated Full-Stack Test Suite",
                "Implemented unified Playwright and Pytest regression pipeline cutting deployment failures by 68%.",
                "ACCOMPLISHMENT",
                ["Playwright", "Python", "CI/CD"],
                "68% bug reduction",
            ),
        ]
        for title, content, cat, skills, impact in knowledge_data:
            db.add(
                KnowledgeItemModel(
                    profile_id=profile.id,
                    title=title,
                    raw_content=content,
                    category=cat,
                    associated_skills=skills,
                    quantified_impact=impact,
                )
            )

        # Seed work experiences
        work_data = [
            (
                "Loomis Cloud Systems",
                "Staff Software Engineer",
                "San Francisco, CA (Remote)",
                "FULL_TIME",
                "2022-03",
                None,
                True,
                "Led core infrastructure and full-stack platform initiatives for cloud developer tooling.",
                [
                    "Engineered distributed microservices processing 40M+ telemetry signals daily.",
                    "Mentored 6 engineers and spearheaded company-wide TypeScript/React architectural standards.",
                ],
                ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker"],
            ),
            (
                "Hyperion Technologies",
                "Senior Full Stack Engineer",
                "New York, NY (Remote)",
                "FULL_TIME",
                "2019-06",
                "2022-02",
                False,
                "Developed high-throughput dashboard interfaces and automated integration pipelines.",
                [
                    "Built real-time financial collaboration workspaces used by 80k+ enterprise users.",
                    "Refactored legacy REST endpoints to high-performance async APIs with Redis caching.",
                ],
                ["React", "TypeScript", "Node.js", "Redis", "PostgreSQL"],
            ),
        ]
        for comp, role, loc, emp, start, end, curr, summ, ach, techs in work_data:
            db.add(
                WorkExperienceModel(
                    profile_id=profile.id,
                    company=comp,
                    role=role,
                    location=loc,
                    employment_type=emp,
                    start_date=start,
                    end_date=end,
                    is_current=curr,
                    summary=summ,
                    key_achievements=ach,
                    technologies=techs,
                )
            )

        # Seed verified application answers
        answers_data = [
            ("work_authorization_us", "Are you legally authorized to work in the United States?", "Yes, I am a US citizen and legally authorized to work without restrictions."),
            ("sponsorship_needed", "Will you now or in the future require visa sponsorship?", "No, I do not require visa sponsorship."),
            ("notice_period", "What is your notice period or earliest start date?", "2 weeks notice period."),
            ("salary_expectation", "What are your salary or compensation expectations?", "$160,000 - $190,000 base annual or $85 - $125/hr contract depending on scope."),
            ("remote_experience", "Do you have experience working with distributed remote teams?", "Yes, 5+ years working remotely with asynchronous communication across US and European timezones."),
        ]
        for canon, q_text, a_text in answers_data:
            db.add(
                ApplicationAnswerModel(
                    question_canonical=canon,
                    question_text=q_text,
                    answer_text=a_text,
                    is_verified=True,
                    confidence=1.0,
                    source="USER_PROFILE",
                )
            )

        await db.commit()
        # Re-fetch with eager loaded relationships
        return await ProfileService.get_or_create_profile(db)

    @staticmethod
    async def get_domain_profile(db: AsyncSession, user_id: Optional[str] = None) -> Optional[CandidateProfile]:
        model = await ProfileService.get_or_create_profile(db, seed_if_empty=True, user_id=user_id)
        if not model:
            return None
        skills = [
            CandidateSkill(
                id=s.id,
                skill_name=s.skill_name,
                category=s.category,
                experience_years=s.experience_years,
                proficiency=SkillProficiency(s.proficiency),
                last_used=s.last_used,
                evidence=s.evidence or [],
                related_projects=s.related_projects or [],
            )
            for s in model.skills
        ]
        knowledge = [
            KnowledgeItem(
                id=k.id,
                title=k.title,
                raw_content=k.raw_content,
                category=k.category,
                associated_skills=k.associated_skills or [],
                quantified_impact=k.quantified_impact,
                created_at=k.created_at,
            )
            for k in model.knowledge_items
        ]
        experiences = [
            WorkExperience(
                id=w.id,
                company=w.company,
                role=w.role,
                location=w.location,
                employment_type=w.employment_type,
                start_date=w.start_date,
                end_date=w.end_date,
                is_current=w.is_current,
                summary=w.summary,
                key_achievements=w.key_achievements or [],
                technologies=w.technologies or [],
            )
            for w in model.work_experiences
        ]

        return CandidateProfile(
            id=model.id,
            full_name=model.full_name,
            headline=model.headline,
            email=model.email,
            location=model.location,
            country=model.country,
            timezone=model.timezone,
            preferred_working_hours=model.preferred_working_hours,
            countries_willing_to_work=model.countries_willing_to_work or [],
            target_roles=model.target_roles or [],
            minimum_salary_annual=model.minimum_salary_annual,
            minimum_hourly_rate=model.minimum_hourly_rate,
            salary_currency=getattr(model, "salary_currency", "USD") or "USD",
            preferred_currencies=model.preferred_currencies or [],
            remote_preference=model.remote_preference,
            timezone_overlap_hours=model.timezone_overlap_hours,
            notice_period_days=model.notice_period_days,
            visa_sponsorship_needed=model.visa_sponsorship_needed,
            authorized_countries=model.authorized_countries or [],
            skills=skills,
            knowledge_items=knowledge,
            work_experiences=experiences,
            automation_level=model.automation_level,
        )

    @staticmethod
    async def get_verified_answers(db: AsyncSession) -> List[ApplicationAnswerModel]:
        stmt = select(ApplicationAnswerModel).order_by(ApplicationAnswerModel.last_verified.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    def canonicalize_question(text: str) -> str:
        clean = re.sub(r'[^a-zA-Z0-9]+', '_', text.lower()).strip('_')
        return clean[:100] or "custom_question"

    @staticmethod
    async def save_or_update_answer(
        db: AsyncSession,
        question_text: str,
        answer_text: str,
        question_canonical: Optional[str] = None,
        source: str = "USER_INPUT",
    ) -> ApplicationAnswerModel:
        if not question_canonical or not question_canonical.strip():
            question_canonical = ProfileService.canonicalize_question(question_text)

        stmt = select(ApplicationAnswerModel).where(
            (ApplicationAnswerModel.question_canonical == question_canonical) |
            (ApplicationAnswerModel.question_text == question_text.strip())
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            existing.answer_text = answer_text.strip()
            existing.question_text = question_text.strip()
            existing.is_verified = True
            existing.last_verified = datetime.utcnow()
            existing.source = source
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            new_ans = ApplicationAnswerModel(
                id=str(uuid.uuid4()),
                question_canonical=question_canonical,
                question_text=question_text.strip(),
                answer_text=answer_text.strip(),
                is_verified=True,
                confidence=1.0,
                source=source,
                last_verified=datetime.utcnow(),
            )
            db.add(new_ans)
            await db.commit()
            await db.refresh(new_ans)
            return new_ans

    @staticmethod
    async def update_answer(
        db: AsyncSession,
        answer_id: str,
        question_text: Optional[str] = None,
        answer_text: Optional[str] = None,
        question_canonical: Optional[str] = None,
        is_verified: Optional[bool] = None,
    ) -> Optional[ApplicationAnswerModel]:
        stmt = select(ApplicationAnswerModel).where(ApplicationAnswerModel.id == answer_id)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            return None

        if question_text is not None:
            existing.question_text = question_text.strip()
        if answer_text is not None:
            existing.answer_text = answer_text.strip()
        if question_canonical is not None:
            existing.question_canonical = question_canonical.strip()
        if is_verified is not None:
            existing.is_verified = is_verified

        existing.last_verified = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing

    @staticmethod
    async def delete_answer(db: AsyncSession, answer_id: str) -> bool:
        stmt = select(ApplicationAnswerModel).where(ApplicationAnswerModel.id == answer_id)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            return False

        await db.delete(existing)
        await db.commit()
        return True

    @staticmethod
    async def update_profile(
        db: AsyncSession, data: Dict[str, Any], user_id: Optional[str] = None
    ) -> Optional[CandidateProfile]:
        model = await ProfileService.get_or_create_profile(db, seed_if_empty=True, user_id=user_id)
        if not model:
            return None

        # Update scalar fields
        for field in [
            "full_name", "headline", "location", "country", "timezone",
            "preferred_working_hours", "minimum_salary_annual", "minimum_hourly_rate",
            "salary_currency", "remote_preference", "timezone_overlap_hours",
            "notice_period_days", "visa_sponsorship_needed", "automation_level"
        ]:
            if field in data and data[field] is not None:
                setattr(model, field, data[field])

        # Keep UserModel full_name in sync if profile is linked to a user
        if model.user_id:
            u_stmt = select(UserModel).where(UserModel.id == model.user_id)
            u_res = await db.execute(u_stmt)
            user_rec = u_res.scalar_one_or_none()
            if user_rec and "full_name" in data and data["full_name"]:
                user_rec.full_name = data["full_name"].strip()

        # Update JSON list fields
        for json_field in ["countries_willing_to_work", "target_roles", "preferred_currencies", "authorized_countries"]:
            if json_field in data and data[json_field] is not None:
                setattr(model, json_field, data[json_field])

        await db.commit()
        return await ProfileService.get_domain_profile(db, user_id=user_id)

    @staticmethod
    async def add_skill(
        db: AsyncSession,
        skill_name: str,
        proficiency: str = "ADVANCED",
        experience_years: float = 3.0,
    ) -> CandidateSkillModel:
        model = await ProfileService.get_or_create_profile(db)
        new_skill = CandidateSkillModel(
            id=str(uuid.uuid4()),
            profile_id=model.id if model else None,
            skill_name=skill_name.strip(),
            proficiency=proficiency,
            experience_years=float(experience_years),
            last_used="Currently used",
            related_projects=[],
        )
        db.add(new_skill)
        await db.commit()
        await db.refresh(new_skill)
        return new_skill

    @staticmethod
    async def delete_skill(db: AsyncSession, skill_id: str) -> bool:
        stmt = select(CandidateSkillModel).where(CandidateSkillModel.id == skill_id)
        res = await db.execute(stmt)
        skill = res.scalar_one_or_none()
        if not skill:
            return False
        await db.delete(skill)
        await db.commit()
        return True

    @staticmethod
    async def add_work_experience(db: AsyncSession, exp_data: Dict[str, Any]) -> WorkExperienceModel:
        model = await ProfileService.get_or_create_profile(db)
        new_exp = WorkExperienceModel(
            id=str(uuid.uuid4()),
            profile_id=model.id if model else None,
            company=exp_data.get("company", "Company"),
            role=exp_data.get("role", "Software Engineer"),
            location=exp_data.get("location", "Remote"),
            employment_type=exp_data.get("employment_type", "FULL_TIME"),
            start_date=exp_data.get("start_date", "2022"),
            end_date=exp_data.get("end_date", "Present"),
            is_current=exp_data.get("is_current", True),
            summary=exp_data.get("summary", ""),
            key_achievements=exp_data.get("key_achievements", []),
            technologies=exp_data.get("technologies", []),
        )
        db.add(new_exp)
        await db.commit()
        await db.refresh(new_exp)
        return new_exp

    @staticmethod
    async def delete_work_experience(db: AsyncSession, exp_id: str) -> bool:
        stmt = select(WorkExperienceModel).where(WorkExperienceModel.id == exp_id)
        res = await db.execute(stmt)
        exp = res.scalar_one_or_none()
        if not exp:
            return False
        await db.delete(exp)
        await db.commit()
        return True
