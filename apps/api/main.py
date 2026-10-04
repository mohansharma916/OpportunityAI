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
from apps.api.models import OpportunityModel, ResumeVariantModel, UserModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema
    await init_db()
    # Seed initial candidate profile & baseline opportunities if empty
    async for db in get_db():
        profile = await ProfileService.get_or_create_profile(db)
        opp_stmt = select(OpportunityModel).limit(1)
        opp_res = await db.execute(opp_stmt)
        if not opp_res.scalar_one_or_none():
            opp_svc = OpportunityService()
            await opp_svc.run_discovery(db)
        break
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
    allow_origins=["*"],
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
        user = await AuthService.get_or_create_demo_user(db)
    else:
        user = await AuthService.get_user_by_id(db, user_id)
        if not user:
            user = await AuthService.get_or_create_demo_user(db)
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


@app.get("/api/profile/answers")
async def get_answers(db: AsyncSession = Depends(get_db)):
    answers = await ProfileService.get_verified_answers(db)
    return answers


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
        sub = await app_service.approve_and_submit(db, application_id, user_notes=req.user_notes)
        return sub
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
