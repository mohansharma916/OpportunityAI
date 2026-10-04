"""
OpportunityOS — Primary FastAPI Application
Production REST API with async database sessions, OpenAPI docs, and domain services.
"""

from contextlib import asynccontextmanager
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
from apps.api.services.crm_service import CRMService
from apps.api.services.activity_service import ActivityService
from apps.api.services.analytics_service import AnalyticsService
from apps.api.services.ai_command_service import AICommandService
from apps.api.services.briefing_service import BriefingService
from apps.api.services.auto_apply_service import AutoApplyService
from apps.api.services.auth_service import AuthService
from apps.api.services.onboarding_service import OnboardingService
from apps.api.services.crawler_service import CrawlerService
from apps.api.services.linkedin_growth_service import LinkedInGrowthService
from apps.api.models import OpportunityModel, ResumeVariantModel, UserModel


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


class RunCrawlerRequest(BaseModel):
    mode: Optional[str] = "IMMEDIATE"
    max_duration_minutes: Optional[int] = 15
    max_applications: Optional[int] = 5
    min_match_score: Optional[float] = 80.0
    target_platforms: Optional[List[str]] = None
    opportunity_types: Optional[List[str]] = None
    auto_apply_enabled: Optional[bool] = True


class UpdateScheduleRequest(BaseModel):
    is_active: Optional[bool] = None
    interval_hours: Optional[int] = None
    max_duration_minutes: Optional[int] = None
    max_applications: Optional[int] = None
    min_match_score: Optional[float] = None
    auto_apply_enabled: Optional[bool] = None
    target_platforms: Optional[List[str]] = None
    opportunity_types: Optional[List[str]] = None


class UpdateAppStatusRequest(BaseModel):
    status: str


class CreateTaskRequest(BaseModel):
    title: str


class ToggleTaskRequest(BaseModel):
    status: Optional[str] = None


class AICommandRequest(BaseModel):
    command: str


class CreateContactRequest(BaseModel):
    company_name: str
    full_name: str
    role: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None
    opportunity_id: Optional[str] = None


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


class ApplyProfileOptRequest(BaseModel):
    field: str
    value: str


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
async def get_profile(db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_domain_profile(db)
    return profile


@app.put("/api/profile")
async def update_profile(req: UpdateProfileRequest, db: AsyncSession = Depends(get_db)):
    try:
        updated = await ProfileService.update_profile(db, req.dict(exclude_unset=True))
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


# -------------------------------------------------------------------
# Autonomous Crawler & Auto-Apply Control Endpoints
# -------------------------------------------------------------------

@app.post("/api/crawler/run")
async def run_crawler_endpoint(
    req: RunCrawlerRequest = RunCrawlerRequest(), db: AsyncSession = Depends(get_db)
):
    try:
        result = await CrawlerService.run_crawler(
            db,
            mode=req.mode or "IMMEDIATE",
            max_duration_minutes=req.max_duration_minutes or 15,
            max_applications=req.max_applications or 5,
            min_match_score=req.min_match_score or 80.0,
            target_platforms=req.target_platforms,
            opportunity_types=req.opportunity_types,
            auto_apply_enabled=req.auto_apply_enabled if req.auto_apply_enabled is not None else True,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/crawler/status")
async def get_crawler_status_endpoint(db: AsyncSession = Depends(get_db)):
    try:
        latest = await CrawlerService.get_latest_session(db)
        sched = await CrawlerService.get_or_create_schedule(db)
        return {
            "latest_session": latest,
            "schedule": sched,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/crawler/schedule")
async def update_crawler_schedule_endpoint(
    req: UpdateScheduleRequest, db: AsyncSession = Depends(get_db)
):
    try:
        sched = await CrawlerService.update_schedule(db, req.dict(exclude_unset=True))
        return sched
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/contacts")
async def list_contacts(db: AsyncSession = Depends(get_db)):
    contacts = await CRMService.get_contacts(db)
    return contacts


@app.post("/api/contacts")
async def create_contact(req: CreateContactRequest, db: AsyncSession = Depends(get_db)):
    contact = await CRMService.create_contact(
        db,
        company_name=req.company_name,
        full_name=req.full_name,
        role=req.role,
        email=req.email,
        linkedin_url=req.linkedin_url,
        notes=req.notes,
        associated_opportunity_id=req.opportunity_id,
    )
    return contact


@app.post("/api/opportunities/{opportunity_id}/outreach/{contact_id}")
async def stage_outreach(
    opportunity_id: str, contact_id: str, db: AsyncSession = Depends(get_db)
):
    seq = await CRMService.create_outreach_sequence(db, opportunity_id, contact_id)
    return seq


@app.get("/api/outreach")
async def list_outreach(db: AsyncSession = Depends(get_db)):
    seqs = await CRMService.get_outreach_sequences(db)
    return seqs


@app.post("/api/outreach/messages/{message_id}/send")
async def send_outreach_message(message_id: str, db: AsyncSession = Depends(get_db)):
    try:
        msg = await CRMService.send_message(db, message_id)
        return {"status": "SUCCESS", "message": f"Outreach email dispatched: '{msg.subject}'", "data": msg}
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


@app.get("/api/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db)):
    data = await AnalyticsService.get_dashboard_metrics(db)
    return data


@app.post("/api/ai/command")
async def run_ai_command(req: AICommandRequest, db: AsyncSession = Depends(get_db)):
    res = await AICommandService.execute_command(db, req.command)
    return res


@app.get("/api/briefing")
async def get_daily_briefing(db: AsyncSession = Depends(get_db)):
    briefing = await BriefingService.generate_daily_briefing(db)
    return briefing


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


@app.get("/api/linkedin/profile-optimizer")
async def get_profile_optimizer(db: AsyncSession = Depends(get_db)):
    try:
        data = await LinkedInGrowthService.analyze_and_optimize_profile(db)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/linkedin/profile-optimizer/apply")
async def apply_profile_opt(req: ApplyProfileOptRequest, db: AsyncSession = Depends(get_db)):
    try:
        res = await LinkedInGrowthService.apply_profile_recommendation(db, req.field, req.value)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
