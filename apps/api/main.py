"""
OpportunityOS — Primary FastAPI Application
Production REST API with async database sessions, OpenAPI docs, and domain services.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.config import settings
from apps.api.db import init_db, get_db
from apps.api.services.profile_service import ProfileService
from apps.api.services.opportunity_service import OpportunityService
from apps.api.services.application_service import ApplicationService
from apps.api.services.activity_service import ActivityService
from apps.api.services.auto_apply_service import AutoApplyService
from apps.api.services.auth_service import AuthService
from apps.api.services.onboarding_service import OnboardingService
from apps.api.services.linkedin_growth_service import LinkedInGrowthService
from apps.api.services.platform_service import PlatformService
from apps.api.services.discovery_service import DiscoveryService
from apps.api.services.intake_service import IntakeService
from apps.api.services.linkedin_optimizer_service import LinkedInOptimizerService
from apps.api.services.tracker_service import (
    DuplicateApplicationError,
    STATUSES as TRACKER_STATUSES,
    TRUSTED_AFTER_CLEAN_SUBMITS,
    TrackerService,
)
from apps.api.models import (
    OpportunityModel,
    ResumeVariantModel,
    UserModel,
    ScrapingPlatformModel,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema
    await init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="OpportunityOS: AI-Powered Career Development, Opportunity Discovery & Automation Platform",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

opp_service = OpportunityService()
app_service = ApplicationService()


# -------------------------------------------------------------------
# Request / Response Schemas
# -------------------------------------------------------------------

class ManualImportRequest(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    body: str


class StatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = None


class PrepareApplicationRequest(BaseModel):
    style: str = "TECHNICAL"


class ApproveApplicationRequest(BaseModel):
    user_notes: Optional[str] = None
    answers: Optional[List[Dict[str, Any]]] = None


class CreateAnswerRequest(BaseModel):
    question_text: str
    answer_text: str
    question_canonical: Optional[str] = None
    source: Optional[str] = "USER_INPUT"


class UpdateAnswerRequest(BaseModel):
    question_text: Optional[str] = None
    answer_text: Optional[str] = None
    question_canonical: Optional[str] = None
    is_verified: Optional[bool] = None


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    preferred_working_hours: Optional[str] = None
    target_roles: Optional[List[str]] = None
    minimum_salary_annual: Optional[float] = None
    minimum_hourly_rate: Optional[float] = None
    salary_currency: Optional[str] = None
    preferred_currencies: Optional[List[str]] = None
    remote_preference: Optional[str] = None
    notice_period_days: Optional[int] = None
    visa_sponsorship_needed: Optional[bool] = None
    authorized_countries: Optional[List[str]] = None
    automation_level: Optional[int] = None


class CreateSkillRequest(BaseModel):
    skill_name: str
    proficiency: Optional[str] = "ADVANCED"
    experience_years: Optional[float] = 3.0


class CreateExperienceRequest(BaseModel):
    company: str
    role: str
    location: Optional[str] = "Remote"
    employment_type: Optional[str] = "FULL_TIME"
    start_date: Optional[str] = "2022"
    end_date: Optional[str] = "Present"
    is_current: Optional[bool] = True
    summary: Optional[str] = ""
    technologies: Optional[List[str]] = []


class UpdateAppStatusRequest(BaseModel):
    status: str


class CreateTaskRequest(BaseModel):
    title: str


class ToggleTaskRequest(BaseModel):
    status: Optional[str] = None


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ParseResumeRequest(BaseModel):
    resume_text: str


class CompleteOnboardingRequest(BaseModel):
    user_id: str
    verified_data: Dict[str, Any]


class ImportExportRequest(BaseModel):
    path: Optional[str] = None
    use_claude: Optional[bool] = None


class DraftDecisionRequest(BaseModel):
    decision: str  # APPROVE, REJECT, REOPEN, MARK_APPLIED
    value: Optional[str] = None


class GeneratePostRequest(BaseModel):
    post_type: Optional[str] = "TECHNICAL_BREAKDOWN"
    topic_pillar: Optional[str] = "Technical Deep-Dives"
    custom_topic: Optional[str] = None
    source_context: Optional[str] = None


class GenerateKnowledgePostRequest(BaseModel):
    knowledge_input: str
    source_type: Optional[str] = "GITHUB_COMMIT"


class UpdateRelationshipStageRequest(BaseModel):
    stage: str


class DecideActionRequest(BaseModel):
    decision: str  # APPROVE, EDIT, REJECT, LATER
    edited_payload: Optional[Dict[str, Any]] = None


class LinkedInCommandRequest(BaseModel):
    prompt: str


class CreatePlatformRequest(BaseModel):
    name: str
    url: str
    auth_notes: Optional[str] = None
    crawl_frequency_hours: int = 12


class UpdatePlatformRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    status: Optional[str] = None
    auth_notes: Optional[str] = None
    crawl_frequency_hours: Optional[int] = None


class UpdateIntakeRequest(BaseModel):
    identity: Optional[Dict[str, Any]] = None
    targeting: Optional[Dict[str, Any]] = None
    documents: Optional[Dict[str, Any]] = None
    screening: Optional[Dict[str, Any]] = None
    accounts: Optional[Dict[str, Any]] = None
    linkedin: Optional[Dict[str, Any]] = None


class TrackerAnswersRequest(BaseModel):
    answers: Dict[str, str]  # canonical question id -> answer


class FollowUpRequest(BaseModel):
    note: Optional[str] = None


class TrackedApplicationRequest(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    job_url: Optional[str] = None
    source_platform: Optional[str] = None
    apply_channel: Optional[str] = None
    opportunity_id: Optional[str] = None
    post_url: Optional[str] = None
    match_score: Optional[float] = None
    resume_variant: Optional[str] = None
    cover_note: Optional[str] = None
    status: Optional[str] = None
    submitted_at: Optional[str] = None
    next_action: Optional[str] = None
    next_action_due: Optional[str] = None
    contact_name: Optional[str] = None
    contact_url: Optional[str] = None
    notes: Optional[str] = None


class SynthesizeHumanPostRequest(BaseModel):
    angle_key: str = "PERSONAL_PRODUCTION_EXPERIENCE"
    custom_notes: Optional[str] = None


# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME, "version": "1.0.0"}


# -------------------------------------------------------------------
# Authentication Endpoints
# -------------------------------------------------------------------

@app.post("/api/auth/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await AuthService.register_user(db, req.email, req.password, req.full_name)
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "onboarding_completed": user.onboarding_completed,
            "token": f"dev_token_{user.id}",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await AuthService.authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "onboarding_completed": user.onboarding_completed,
        "token": f"dev_token_{user.id}",
    }


@app.post("/api/auth/demo")
async def demo_login(db: AsyncSession = Depends(get_db)):
    user = await AuthService.get_or_create_demo_user(db)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "onboarding_completed": user.onboarding_completed,
        "token": f"dev_token_{user.id}",
    }


@app.get("/api/auth/me")
async def get_me(user_id: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user = await AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "onboarding_completed": user.onboarding_completed,
    }


@app.post("/api/auth/logout")
async def logout():
    return {"status": "SUCCESS", "message": "Successfully signed out"}


# -------------------------------------------------------------------
# Onboarding & Resume Parsing Endpoints
# -------------------------------------------------------------------

@app.post("/api/onboarding/parse-resume")
async def parse_resume(req: ParseResumeRequest):
    parsed = OnboardingService.parse_resume_text(req.resume_text)
    return parsed


@app.post("/api/onboarding/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        content = await file.read()
        extracted_text = OnboardingService.extract_text_from_file(content, file.filename or "resume.txt")
        parsed = OnboardingService.parse_resume_text(extracted_text)
        parsed["raw_extracted_text"] = extracted_text
        parsed["filename"] = file.filename
        return parsed
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process resume file: {str(e)}")


@app.post("/api/onboarding/complete")
async def complete_onboarding(req: CompleteOnboardingRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await OnboardingService.complete_onboarding(db, req.user_id, req.verified_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/profile")
async def get_profile(
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    profile = await ProfileService.get_domain_profile(db, user_id=user_id)
    return profile


@app.put("/api/profile")
async def update_profile(
    req: UpdateProfileRequest,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        updated = await ProfileService.update_profile(db, req.dict(exclude_unset=True), user_id=user_id)
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/profile/skills")
async def add_skill(req: CreateSkillRequest, db: AsyncSession = Depends(get_db)):
    try:
        skill = await ProfileService.add_skill(
            db,
            skill_name=req.skill_name,
            proficiency=req.proficiency or "ADVANCED",
            experience_years=req.experience_years or 3.0,
        )
        return {
            "id": skill.id,
            "skill_name": skill.skill_name,
            "proficiency": skill.proficiency,
            "experience_years": skill.experience_years,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/profile/skills/{skill_id}")
async def delete_skill(skill_id: str, db: AsyncSession = Depends(get_db)):
    try:
        success = await ProfileService.delete_skill(db, skill_id)
        if not success:
            raise HTTPException(status_code=404, detail="Skill not found")
        return {"deleted": True, "id": skill_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/profile/experiences")
async def add_experience(req: CreateExperienceRequest, db: AsyncSession = Depends(get_db)):
    try:
        exp = await ProfileService.add_work_experience(db, req.dict())
        return {
            "id": exp.id,
            "company": exp.company,
            "role": exp.role,
            "location": exp.location,
            "employment_type": exp.employment_type,
            "start_date": exp.start_date,
            "end_date": exp.end_date,
            "is_current": exp.is_current,
            "summary": exp.summary,
            "technologies": exp.technologies or [],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/profile/experiences/{exp_id}")
async def delete_experience(exp_id: str, db: AsyncSession = Depends(get_db)):
    try:
        success = await ProfileService.delete_work_experience(db, exp_id)
        if not success:
            raise HTTPException(status_code=404, detail="Experience not found")
        return {"deleted": True, "id": exp_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/profile/answers")
async def get_answers(db: AsyncSession = Depends(get_db)):
    answers = await ProfileService.get_verified_answers(db)
    return answers


@app.post("/api/profile/answers")
async def create_answer(req: CreateAnswerRequest, db: AsyncSession = Depends(get_db)):
    try:
        ans = await ProfileService.save_or_update_answer(
            db,
            question_text=req.question_text,
            answer_text=req.answer_text,
            question_canonical=req.question_canonical,
            source=req.source or "USER_INPUT",
        )
        return ans
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/profile/answers/{answer_id}")
async def update_answer_endpoint(
    answer_id: str, req: UpdateAnswerRequest, db: AsyncSession = Depends(get_db)
):
    try:
        ans = await ProfileService.update_answer(
            db,
            answer_id=answer_id,
            question_text=req.question_text,
            answer_text=req.answer_text,
            question_canonical=req.question_canonical,
            is_verified=req.is_verified,
        )
        if not ans:
            raise HTTPException(status_code=404, detail=f"Answer {answer_id} not found")
        return ans
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/profile/answers/{answer_id}")
async def delete_answer_endpoint(answer_id: str, db: AsyncSession = Depends(get_db)):
    try:
        success = await ProfileService.delete_answer(db, answer_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Answer {answer_id} not found")
        return {"deleted": True, "id": answer_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/opportunities")
async def list_opportunities(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    items = await opp_service.get_opportunities(db, status=status, search=search, min_score=min_score)
    return items


@app.post("/api/opportunities/discover")
async def trigger_discovery(db: AsyncSession = Depends(get_db)):
    new_opps = await opp_service.run_discovery(db)
    return {"message": "Discovery cycle completed", "discovered_count": len(new_opps)}


@app.post("/api/opportunities/import")
async def manual_import(req: ManualImportRequest, db: AsyncSession = Depends(get_db)):
    opp = await opp_service.import_manual_opportunity(
        db, url=req.url, title=req.title, company=req.company, body=req.body
    )
    return opp


@app.get("/api/opportunities/grouped-by-date")
async def get_opportunities_grouped_by_date_endpoint(
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await opp_service.get_opportunities_grouped_by_date(db, search=search, status=status)
        formatted_groups = {}
        for bucket, items in data["groups"].items():
            formatted_groups[bucket] = [
                {
                    "id": item.id,
                    "title": item.title,
                    "company_name": item.company_name,
                    "location": item.location,
                    "remote_type": item.remote_type,
                    "source": item.source,
                    "url": item.url,
                    "salary_min": item.salary_min,
                    "salary_max": item.salary_max,
                    "salary_currency": item.salary_currency,
                    "hourly_rate": item.hourly_rate,
                    "required_skills": item.required_skills,
                    "status": item.status,
                    "date_posted": item.date_posted.isoformat() if item.date_posted else item.created_at.isoformat(),
                    "date_formatted": item.date_posted.strftime("%b %d, %Y") if item.date_posted else "Recent",
                    "overall_match_score": item.matching_score.overall_match_score if item.matching_score else 0.0,
                    "match_rationale": item.matching_score.match_rationale if item.matching_score else None,
                }
                for item in items
            ]
        return {
            "total": data["total"],
            "status_counts": data["status_counts"],
            "groups": formatted_groups,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/opportunities/{opportunity_id}")
async def get_opportunity(opportunity_id: str, db: AsyncSession = Depends(get_db)):
    opp = await opp_service.get_opportunity_by_id(db, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@app.put("/api/opportunities/{opportunity_id}/status")
async def update_status(
    opportunity_id: str, req: StatusUpdateRequest, db: AsyncSession = Depends(get_db)
):
    opp = await opp_service.update_opportunity_status(db, opportunity_id, req.status, req.reason)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@app.post("/api/opportunities/{opportunity_id}/prepare")
async def prepare_application(
    opportunity_id: str,
    req: PrepareApplicationRequest = PrepareApplicationRequest(),
    db: AsyncSession = Depends(get_db),
):
    try:
        app_model = await app_service.prepare_application(db, opportunity_id, style=req.style)
        return app_model
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/applications")
async def list_applications(
    status: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)
):
    apps = await app_service.get_applications(db, status=status)
    return apps


@app.post("/api/applications/{application_id}/approve")
async def approve_application(
    application_id: str,
    req: ApproveApplicationRequest = ApproveApplicationRequest(),
    db: AsyncSession = Depends(get_db),
):
    try:
        if req.answers:
            for a in req.answers:
                q_text = a.get("question_text", "").strip()
                a_text = a.get("answer_text", "").strip()
                canon = a.get("question_canonical")
                if q_text and a_text:
                    await ProfileService.save_or_update_answer(
                        db,
                        question_text=q_text,
                        answer_text=a_text,
                        question_canonical=canon,
                        source="APPLICATION_REVIEW",
                    )

        sub = await app_service.approve_and_submit(db, application_id, user_notes=req.user_notes)
        return sub
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/applications/{application_id}/status")
async def update_application_status_endpoint(
    application_id: str, req: UpdateAppStatusRequest, db: AsyncSession = Depends(get_db)
):
    try:
        app_mod = await app_service.update_status(db, application_id, req.status)
        if not app_mod:
            raise HTTPException(status_code=404, detail="Application not found")
        return {
            "id": app_mod.id,
            "opportunity_id": app_mod.opportunity_id,
            "status": app_mod.status,
            "tasks": app_mod.tasks or [],
            "submission_mode": app_mod.submission_mode,
            "notes": app_mod.notes,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/applications/{application_id}/tasks")
async def add_application_task_endpoint(
    application_id: str, req: CreateTaskRequest, db: AsyncSession = Depends(get_db)
):
    try:
        app_mod = await app_service.add_task(db, application_id, req.title)
        if not app_mod:
            raise HTTPException(status_code=404, detail="Application not found")
        return app_mod.tasks or []
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/applications/{application_id}/tasks/{task_id}")
async def toggle_application_task_endpoint(
    application_id: str, task_id: str, req: ToggleTaskRequest = ToggleTaskRequest(), db: AsyncSession = Depends(get_db)
):
    try:
        app_mod = await app_service.toggle_task(db, application_id, task_id, req.status)
        if not app_mod:
            raise HTTPException(status_code=404, detail="Application not found")
        return app_mod.tasks or []
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/activity")
async def get_activity_feed(
    limit: int = Query(50),
    entity_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    logs = await ActivityService.get_recent_activity(db, limit=limit, entity_type=entity_type)
    return logs


@app.post("/api/applications/auto-run")
async def run_auto_apply_batch(db: AsyncSession = Depends(get_db)):
    auto_svc = AutoApplyService()
    result = await auto_svc.run_batch_auto_apply(db)
    return result


@app.post("/api/opportunities/{opportunity_id}/auto-apply")
async def auto_apply_single(
    opportunity_id: str,
    force: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    auto_svc = AutoApplyService()
    result = await auto_svc.auto_apply_opportunity(db, opportunity_id, force=force)
    return result


@app.get("/api/resumes")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    stmt = select(ResumeVariantModel).order_by(ResumeVariantModel.generated_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


# -------------------------------------------------------------------
# LinkedIn AI Growth Agent Endpoints
# -------------------------------------------------------------------

@app.get("/api/linkedin/dashboard")
async def get_linkedin_dashboard(db: AsyncSession = Depends(get_db)):
    try:
        overview = await LinkedInGrowthService.get_dashboard_overview(db)
        return overview
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/linkedin/optimizer")
async def get_linkedin_optimizer(db: AsyncSession = Depends(get_db)):
    return await LinkedInOptimizerService.state(db)


@app.post("/api/linkedin/optimizer/import-export")
async def import_linkedin_export(req: ImportExportRequest, db: AsyncSession = Depends(get_db)):
    try:
        await LinkedInOptimizerService.import_export(db, req.path)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await LinkedInOptimizerService.analyze(db, use_claude=req.use_claude)


@app.post("/api/linkedin/optimizer/analyze")
async def analyze_linkedin_profile(use_claude: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    try:
        return await LinkedInOptimizerService.analyze(db, use_claude=use_claude)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/linkedin/optimizer/drafts/{draft_id}")
async def decide_linkedin_draft(draft_id: str, req: DraftDecisionRequest, db: AsyncSession = Depends(get_db)):
    try:
        draft = await LinkedInOptimizerService.decide(db, draft_id, req.decision, req.value)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return LinkedInOptimizerService.draft_dict(draft)


@app.get("/api/linkedin/brand-strategy")
async def get_brand_strategy_endpoint(db: AsyncSession = Depends(get_db)):
    try:
        data = await LinkedInGrowthService.get_brand_strategy(db)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/linkedin/content")
async def get_linkedin_content(db: AsyncSession = Depends(get_db)):
    try:
        posts = await LinkedInGrowthService.list_content_posts(db)
        return posts
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/linkedin/content/generate")
async def generate_linkedin_post(req: GeneratePostRequest = GeneratePostRequest(), db: AsyncSession = Depends(get_db)):
    try:
        post = await LinkedInGrowthService.generate_post(
            db,
            post_type=req.post_type or "TECHNICAL_BREAKDOWN",
            topic_pillar=req.topic_pillar or "Technical Deep-Dives",
            custom_topic=req.custom_topic,
            source_context=req.source_context,
        )
        return post
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/linkedin/content/from-knowledge")
async def generate_post_from_knowledge_endpoint(req: GenerateKnowledgePostRequest, db: AsyncSession = Depends(get_db)):
    try:
        post = await LinkedInGrowthService.generate_post_from_knowledge(
            db,
            knowledge_input=req.knowledge_input,
            source_type=req.source_type or "GITHUB_COMMIT",
        )
        return post
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/linkedin/relationships")
async def get_relationships_endpoint(db: AsyncSession = Depends(get_db)):
    try:
        data = await LinkedInGrowthService.list_relationships(db)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/linkedin/relationships/{relationship_id}/stage")
async def update_relationship_stage_endpoint(
    relationship_id: str, req: UpdateRelationshipStageRequest, db: AsyncSession = Depends(get_db)
):
    try:
        res = await LinkedInGrowthService.update_relationship_stage(db, relationship_id, req.stage)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/linkedin/comment-opportunities")
async def get_comment_opportunities_endpoint(db: AsyncSession = Depends(get_db)):
    try:
        data = await LinkedInGrowthService.list_comment_opportunities(db)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/linkedin/companies")
async def get_target_companies_endpoint(db: AsyncSession = Depends(get_db)):
    try:
        data = await LinkedInGrowthService.list_target_companies(db)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/linkedin/actions/approvals")
async def get_pending_actions_endpoint(db: AsyncSession = Depends(get_db)):
    try:
        actions = await LinkedInGrowthService.list_pending_actions(db)
        return actions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/linkedin/actions/{action_id}/decide")
async def decide_action_endpoint(action_id: str, req: DecideActionRequest, db: AsyncSession = Depends(get_db)):
    try:
        res = await LinkedInGrowthService.decide_action(
            db, action_id, req.decision, req.edited_payload
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/linkedin/agent/run-cycle")
async def run_agent_planner_cycle_endpoint(db: AsyncSession = Depends(get_db)):
    try:
        cycle_res = await LinkedInGrowthService.run_agent_planner_cycle(db)
        return cycle_res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/linkedin/command")
async def run_linkedin_command_endpoint(req: LinkedInCommandRequest, db: AsyncSession = Depends(get_db)):
    try:
        res = await LinkedInGrowthService.process_natural_language_command(db, req.prompt)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------------------------
# Platforms & Discovery
# -------------------------------------------------------------------

@app.get("/api/platforms")
async def get_platforms_endpoint(db: AsyncSession = Depends(get_db)):
    return [PlatformService.to_dict(p) for p in await PlatformService.list_platforms(db)]


@app.post("/api/platforms")
async def create_platform_endpoint(req: CreatePlatformRequest, db: AsyncSession = Depends(get_db)):
    try:
        platform = await PlatformService.create_platform(
            db=db, name=req.name, url=req.url, auth_notes=req.auth_notes,
            crawl_frequency_hours=req.crawl_frequency_hours, added_by="USER",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PlatformService.to_dict(platform)


@app.put("/api/platforms/{platform_id}")
async def update_platform_endpoint(platform_id: str, req: UpdatePlatformRequest, db: AsyncSession = Depends(get_db)):
    try:
        updated = await PlatformService.update_platform(db, platform_id, req.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PlatformService.to_dict(updated)


@app.delete("/api/platforms/{platform_id}")
async def delete_platform_endpoint(platform_id: str, db: AsyncSession = Depends(get_db)):
    if not await PlatformService.delete_platform(db, platform_id):
        raise HTTPException(status_code=404, detail="Platform not found")
    return {"success": True}


@app.post("/api/platforms/{platform_id}/scrape")
async def scrape_single_platform_endpoint(platform_id: str, db: AsyncSession = Depends(get_db)):
    if not await PlatformService.get(db, platform_id):
        raise HTTPException(status_code=404, detail="Platform not found")
    return await DiscoveryService.run(db, platform_ids=[platform_id])


@app.post("/api/platforms/scrape-all")
@app.post("/api/discovery/run")
async def run_discovery_endpoint(force: bool = Query(False), db: AsyncSession = Depends(get_db)):
    """Search every active source that is due (or all of them with force=true)."""
    return await DiscoveryService.run(db, force=force)


# -------------------------------------------------------------------
# Date-Grouped Opportunities & Apply Queue
# -------------------------------------------------------------------


@app.put("/api/opportunities/{opportunity_id}/user-status")
async def update_opportunity_user_status_endpoint(
    opportunity_id: str,
    req: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        updated = await opp_service.update_opportunity_status(
            db=db,
            opportunity_id=opportunity_id,
            new_status=req.status,
            reason=req.reason or f"User manually updated status to {req.status}",
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        return {"id": updated.id, "status": updated.status, "message": "Status updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/opportunities/{opportunity_id}/human-apply")
async def human_apply_endpoint(opportunity_id: str, db: AsyncSession = Depends(get_db)):
    """
    Queues the opportunity in the application tracker. The worker on the candidate's
    machine fills it in their own browser (`python -m apps.worker.cli queue`), and
    nothing is submitted until the candidate approves it.
    """
    opp = await opp_service.get_opportunity_by_id(db, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    score = opp.matching_score.overall_match_score if opp.matching_score else None
    try:
        row = await TrackerService.create(db, {
            "company": opp.company_name,
            "role": opp.title,
            "job_url": opp.url,
            "source_platform": opp.source,
            "opportunity_id": opp.id,
            "match_score": score,
        })
    except DuplicateApplicationError as dup:
        raise HTTPException(status_code=409, detail={
            "message": str(dup), "application": TrackerService.to_dict(dup.existing),
        })
    opp.status = "QUEUED"
    await db.commit()
    return {
        "success": True,
        "status": row.status,
        "application": TrackerService.to_dict(row),
        "message": "Queued. The worker fills it in your browser; you approve before anything is submitted.",
    }


# -------------------------------------------------------------------
# Candidate Intake (Answer Bank)
# -------------------------------------------------------------------

@app.get("/api/intake")
async def get_intake_endpoint(user_id: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    intake = await IntakeService.get_or_create(db, user_id=user_id)
    return IntakeService.to_dict(intake)


@app.put("/api/intake")
async def update_intake_endpoint(
    req: UpdateIntakeRequest,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    intake = await IntakeService.update(db, req.model_dump(exclude_none=True), user_id=user_id)
    return IntakeService.to_dict(intake)


# -------------------------------------------------------------------
# Application Tracker
# -------------------------------------------------------------------

@app.get("/api/tracker")
async def list_tracker_endpoint(
    status: Optional[str] = Query(None),
    source_platform: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    rows = await TrackerService.list(db, status=status, source_platform=source_platform, search=search)
    return [TrackerService.to_dict(r) for r in rows]


@app.get("/api/tracker/stats")
async def tracker_stats_endpoint(db: AsyncSession = Depends(get_db)):
    stats = await TrackerService.stats(db)
    stats["statuses"] = TRACKER_STATUSES
    channels = {r.apply_channel for r in await TrackerService.list(db) if r.apply_channel}
    stats["clean_submits"] = {c: await TrackerService.clean_submits(db, c) for c in sorted(channels)}
    stats["trusted_after"] = TRUSTED_AFTER_CLEAN_SUBMITS
    return stats


@app.post("/api/tracker")
async def create_tracker_endpoint(req: TrackedApplicationRequest, db: AsyncSession = Depends(get_db)):
    try:
        row = await TrackerService.create(db, req.model_dump(exclude_none=True))
    except DuplicateApplicationError as dup:
        raise HTTPException(status_code=409, detail={
            "message": str(dup), "application": TrackerService.to_dict(dup.existing),
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TrackerService.to_dict(row)


@app.put("/api/tracker/{application_id}")
async def update_tracker_endpoint(
    application_id: str, req: TrackedApplicationRequest, db: AsyncSession = Depends(get_db)
):
    try:
        row = await TrackerService.update(db, application_id, req.model_dump(exclude_unset=True))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateApplicationError as dup:
        raise HTTPException(status_code=409, detail={
            "message": str(dup), "application": TrackerService.to_dict(dup.existing),
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TrackerService.to_dict(row)


@app.post("/api/tracker/{application_id}/answers")
async def answer_tracker_questions(application_id: str, req: TrackerAnswersRequest, db: AsyncSession = Depends(get_db)):
    """Answer open questions; answers are saved to the answer bank and the worker re-fills the form."""
    try:
        row = await TrackerService.submit_answers(db, application_id, req.answers)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TrackerService.to_dict(row)


@app.post("/api/tracker/{application_id}/approve")
async def approve_tracker_application(application_id: str, db: AsyncSession = Depends(get_db)):
    try:
        row = await TrackerService.approve(db, application_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TrackerService.to_dict(row)


@app.get("/api/tracker/{application_id}/evidence/{index}")
async def tracker_evidence(application_id: str, index: int, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import FileResponse
    from apps.worker.automation import EVIDENCE_DIR

    row = await TrackerService.get(db, application_id)
    if not row or not (0 <= index < len(row.evidence or [])):
        raise HTTPException(status_code=404, detail="Screenshot not found")
    path = Path(row.evidence[index]).resolve()
    if not path.is_relative_to(EVIDENCE_DIR.resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(path, media_type="image/png")


@app.get("/api/tracker/follow-ups")
async def tracker_follow_ups(db: AsyncSession = Depends(get_db)):
    intake = await IntakeService.get_or_create(db)
    return await TrackerService.follow_ups_due(db, (intake.identity or {}).get("full_name") or "")


@app.post("/api/tracker/{application_id}/follow-up")
async def tracker_mark_followed_up(application_id: str, req: FollowUpRequest, db: AsyncSession = Depends(get_db)):
    try:
        row = await TrackerService.mark_followed_up(db, application_id, req.note)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return TrackerService.to_dict(row)


@app.delete("/api/tracker/{application_id}")
async def delete_tracker_endpoint(application_id: str, db: AsyncSession = Depends(get_db)):
    if not await TrackerService.delete(db, application_id):
        raise HTTPException(status_code=404, detail="Application not found")
    return {"success": True}


# -------------------------------------------------------------------
# LinkedIn Post Studio Endpoints
# -------------------------------------------------------------------


@app.post("/api/linkedin/posts/{post_id}/publish")
async def publish_linkedin_post_endpoint(
    post_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        res = await LinkedInGrowthService.publish_content_post(db, post_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/linkedin/scraped-posts")
async def get_linkedin_scraped_posts(
    scrape_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await LinkedInGrowthService.get_or_seed_scraped_posts(db, scrape_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/linkedin/posts/{post_id}/analyze")
async def analyze_linkedin_scraped_post_endpoint(
    post_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await LinkedInGrowthService.analyze_scraped_post(db, post_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/linkedin/posts/{post_id}/synthesize-human-post")
async def synthesize_human_post_endpoint(
    post_id: str,
    req: SynthesizeHumanPostRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await LinkedInGrowthService.synthesize_human_post(
            db=db,
            post_id=post_id,
            angle_key=req.angle_key,
            custom_notes=req.custom_notes,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/linkedin/post-studio/library")
async def get_analyzed_posts_library_endpoint(
    db: AsyncSession = Depends(get_db),
):
    try:
        return await LinkedInGrowthService.get_analyzed_posts_library(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
