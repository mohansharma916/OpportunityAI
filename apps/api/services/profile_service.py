"""
OpportunityOS — Candidate Profile & Knowledge Base Service
"""

import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.api.models import (
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
    async def get_or_create_profile(db: AsyncSession) -> CandidateProfileModel:
        stmt = (
            select(CandidateProfileModel)
            .options(
                selectinload(CandidateProfileModel.skills),
                selectinload(CandidateProfileModel.knowledge_items),
                selectinload(CandidateProfileModel.work_experiences),
            )
            .limit(1)
        )
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()

        if profile:
            return profile

        # Seed initial rich profile
        profile = CandidateProfileModel(
            id=str(uuid.uuid4()),
            full_name="Alex Morgan",
            headline="Staff Full Stack & Distributed Systems Architect",
            email="alex.morgan.dev@gmail.com",
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
    async def get_domain_profile(db: AsyncSession) -> CandidateProfile:
        model = await ProfileService.get_or_create_profile(db)
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
        stmt = select(ApplicationAnswerModel)
        res = await db.execute(stmt)
        return list(res.scalars().all())
