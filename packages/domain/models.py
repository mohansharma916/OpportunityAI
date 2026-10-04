"""
OpportunityOS — Canonical Domain Models
Strict Pydantic v2 schemas representing the complete candidate, opportunity,
application, and audit domain.
"""

from __future__ import annotations
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


# -------------------------------------------------------------------
# Enums
# -------------------------------------------------------------------

class OpportunityType(str, Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    FREELANCE = "FREELANCE"
    CONSULTING = "CONSULTING"
    OPEN_SOURCE = "OPEN_SOURCE"
    PAID_OPEN_SOURCE = "PAID_OPEN_SOURCE"
    COLLABORATION = "COLLABORATION"
    STARTUP = "STARTUP"
    FOUNDING_ENGINEER = "FOUNDING_ENGINEER"
    ADVISORY = "ADVISORY"
    BUG_BOUNTY = "BUG_BOUNTY"
    TECHNICAL_WRITING = "TECHNICAL_WRITING"
    PROJECT_CONTRIBUTION = "PROJECT_CONTRIBUTION"
    SHORT_TERM_PROJECT = "SHORT_TERM_PROJECT"


class RemoteType(str, Enum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"


class PipelineStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    AI_REVIEWING = "AI_REVIEWING"
    STRONG_MATCH = "STRONG_MATCH"
    PREPARED = "PREPARED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    APPLIED = "APPLIED"
    CONTACTED = "CONTACTED"
    RECRUITER_RESPONDED = "RECRUITER_RESPONDED"
    ASSESSMENT = "ASSESSMENT"
    INTERVIEW = "INTERVIEW"
    FINAL_INTERVIEW = "FINAL_INTERVIEW"
    OFFER = "OFFER"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class SkillProficiency(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class RelationshipStatus(str, Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    RESPONDED = "RESPONDED"
    CONNECTED = "CONNECTED"
    INTERVIEWING = "INTERVIEWING"
    NO_RESPONSE = "NO_RESPONSE"
    CLOSED = "CLOSED"


class AuditEventType(str, Enum):
    DISCOVERED_JOB = "DISCOVERED_JOB"
    ANALYZED_JOB = "ANALYZED_JOB"
    MATCH_SCORED = "MATCH_SCORED"
    GENERATED_RESUME = "GENERATED_RESUME"
    GENERATED_COVER_LETTER = "GENERATED_COVER_LETTER"
    APPLICATION_PREPARED = "APPLICATION_PREPARED"
    APPLICATION_APPROVED = "APPLICATION_APPROVED"
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED"
    CONTACT_FOUND = "CONTACT_FOUND"
    OUTREACH_PREPARED = "OUTREACH_PREPARED"
    OUTREACH_SENT = "OUTREACH_SENT"
    FOLLOW_UP_SCHEDULED = "FOLLOW_UP_SCHEDULED"
    EMAIL_RECEIVED = "EMAIL_RECEIVED"
    INTERVIEW_DETECTED = "INTERVIEW_DETECTED"
    STATUS_CHANGED = "STATUS_CHANGED"
    NEEDS_ATTENTION_TRIGGERED = "NEEDS_ATTENTION_TRIGGERED"


# -------------------------------------------------------------------
# Candidate Profile & Knowledge Base Schemas
# -------------------------------------------------------------------

class CandidateSkill(BaseModel):
    id: Optional[str] = None
    skill_name: str
    category: str = "TECHNICAL"  # TECHNICAL, ARCHITECTURE, LEADERSHIP
    experience_years: float
    proficiency: SkillProficiency = SkillProficiency.ADVANCED
    last_used: str = "Currently used"
    evidence: List[str] = Field(default_factory=list)
    related_projects: List[str] = Field(default_factory=list)


class KnowledgeItem(BaseModel):
    id: Optional[str] = None
    title: str
    raw_content: str
    category: str = "ACCOMPLISHMENT"  # ACCOMPLISHMENT, ARCHITECTURE, CASE_STUDY, LEADERSHIP
    associated_skills: List[str] = Field(default_factory=list)
    quantified_impact: Optional[str] = None
    created_at: Optional[datetime] = None


class WorkExperience(BaseModel):
    id: Optional[str] = None
    company: str
    role: str
    location: Optional[str] = None
    employment_type: str = "FULL_TIME"
    start_date: str
    end_date: Optional[str] = None
    is_current: bool = False
    summary: str
    key_achievements: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    id: Optional[str] = None
    full_name: str
    headline: str
    email: str
    location: str
    country: str
    timezone: str
    preferred_working_hours: str = "09:00 - 18:00 UTC"
    countries_willing_to_work: List[str] = Field(
        default_factory=lambda: ["US", "EU", "UK", "Canada", "Worldwide Remote"]
    )
    target_roles: List[str] = Field(
        default_factory=lambda: [
            "Senior Full Stack Engineer",
            "Senior Frontend Engineer",
            "Lead Software Engineer",
            "Founding Engineer",
            "Contract Software Architect"
        ]
    )
    minimum_salary_annual: float = 140000.0
    minimum_hourly_rate: float = 75.0
    preferred_currencies: List[str] = Field(default_factory=lambda: ["USD", "EUR", "GBP"])
    remote_preference: RemoteType = RemoteType.REMOTE
    timezone_overlap_hours: int = 4
    notice_period_days: int = 14
    visa_sponsorship_needed: bool = False
    authorized_countries: List[str] = Field(default_factory=lambda: ["US", "EU"])
    skills: List[CandidateSkill] = Field(default_factory=list)
    work_experiences: List[WorkExperience] = Field(default_factory=list)
    knowledge_items: List[KnowledgeItem] = Field(default_factory=list)
    automation_level: int = 3  # 0: Discovery, 3: Approval Gate, 5: Full Auto


# -------------------------------------------------------------------
# Opportunity Domain Models
# -------------------------------------------------------------------

class Opportunity(BaseModel):
    id: Optional[str] = None
    cluster_id: Optional[str] = None
    source: str  # HACKER_NEWS, GITHUB, REMOTE_OK, WE_WORK_REMOTELY, MANUAL_IMPORT
    external_id: Optional[str] = None
    url: str
    company_name: str
    company_domain: Optional[str] = None
    title: str
    description: str
    location: Optional[str] = "Worldwide Remote"
    remote_type: RemoteType = RemoteType.REMOTE
    country: Optional[str] = None
    timezone: Optional[str] = None
    employment_type: OpportunityType = OpportunityType.FULL_TIME
    contract_duration: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    hourly_rate: Optional[float] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_required_years: Optional[float] = None
    status: PipelineStatus = PipelineStatus.DISCOVERED
    date_posted: Optional[datetime] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SearchCriteria(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    target_roles: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    remote_only: bool = True
    minimum_rate: Optional[float] = None
    countries: List[str] = Field(default_factory=list)
    limit: int = 25


# -------------------------------------------------------------------
# Matching & Scoring Models
# -------------------------------------------------------------------

class MatchingScore(BaseModel):
    id: Optional[str] = None
    opportunity_id: str
    overall_match_score: float  # 0 to 100
    confidence_score: float     # 0 to 100
    technical_match: float      # 0 to 100
    experience_match: float     # 0 to 100
    remote_match: float         # 0 to 100
    timezone_match: float       # 0 to 100
    compensation_match: float   # 0 to 100
    industry_match: float       # 0 to 100
    role_match: float           # 0 to 100
    transferable_skills: Dict[str, str] = Field(default_factory=dict)
    primary_strengths: List[str] = Field(default_factory=list)
    primary_gaps: List[str] = Field(default_factory=list)
    match_rationale: str
    scored_at: Optional[datetime] = None


# -------------------------------------------------------------------
# Application, Resume & Outreach Models
# -------------------------------------------------------------------

class ResumeVariant(BaseModel):
    id: Optional[str] = None
    opportunity_id: Optional[str] = None
    variant_name: str
    headline: str
    summary: str
    selected_skills: List[str] = Field(default_factory=list)
    reordered_experiences: List[Dict[str, Any]] = Field(default_factory=list)
    emphasized_achievements: List[str] = Field(default_factory=list)
    pdf_render_url: Optional[str] = None
    content_hash: str
    generated_at: Optional[datetime] = None


class CoverLetter(BaseModel):
    id: Optional[str] = None
    opportunity_id: str
    style: str = "TECHNICAL"  # SHORT, PROFESSIONAL, TECHNICAL, STARTUP, CONVERSATIONAL
    content: str
    key_selling_points: List[str] = Field(default_factory=list)
    generated_at: Optional[datetime] = None


class ApplicationAnswer(BaseModel):
    id: Optional[str] = None
    question_canonical: str
    question_text: str
    answer_text: str
    is_verified: bool = True
    confidence: float = 1.0
    source: str = "USER_PROFILE"
    last_verified: Optional[datetime] = None


class Application(BaseModel):
    id: Optional[str] = None
    opportunity_id: str
    resume_variant_id: Optional[str] = None
    cover_letter_id: Optional[str] = None
    submission_mode: str = "APPROVAL"  # MANUAL, APPROVAL, AUTO
    status: str = "PREPARED"  # PREPARED, NEEDS_APPROVAL, SUBMITTED, REJECTED
    submission_url: Optional[str] = None
    submitted_at: Optional[datetime] = None
    error_message: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


# -------------------------------------------------------------------
# CRM & Outreach
# -------------------------------------------------------------------

class Contact(BaseModel):
    id: Optional[str] = None
    company_name: str
    full_name: str
    role: str  # RECRUITER, ENGINEERING_MANAGER, CTO, FOUNDER, MAINTAINER
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    relationship_status: RelationshipStatus = RelationshipStatus.NEW
    associated_opportunity_id: Optional[str] = None
    last_interaction_at: Optional[datetime] = None
    notes: Optional[str] = None


class OutreachMessage(BaseModel):
    id: Optional[str] = None
    step_number: int
    channel: str = "EMAIL"  # EMAIL, LINKEDIN, GITHUB
    subject: Optional[str] = None
    body: str
    scheduled_for: datetime
    sent_at: Optional[datetime] = None
    status: str = "PENDING"  # PENDING, SENT, FAILED, CANCELLED


class OutreachSequence(BaseModel):
    id: Optional[str] = None
    opportunity_id: str
    contact_id: str
    status: str = "ACTIVE"  # ACTIVE, PAUSED, COMPLETED, CANCELLED_REPLIED
    current_step: int = 0
    messages: List[OutreachMessage] = Field(default_factory=list)


# -------------------------------------------------------------------
# Audit & Activity
# -------------------------------------------------------------------

class AuditEvent(BaseModel):
    id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    entity_type: str
    entity_id: str
    action: AuditEventType
    actor: str = "SYSTEM_AGENT"
    reason: Optional[str] = None
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_payload: Dict[str, Any] = Field(default_factory=dict)
    status: str = "SUCCESS"  # SUCCESS, WARNING, FAILED, HALTED_HUMAN_ATTENTION
    latency_ms: int = 0


class SearchAgent(BaseModel):
    id: Optional[str] = None
    name: str
    keywords: List[str] = Field(default_factory=list)
    target_roles: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    excluded_keywords: List[str] = Field(default_factory=list)
    remote_only: bool = True
    minimum_compensation: Optional[float] = None
    schedule_cron: str = "0 */6 * * *"
    is_active: bool = True
    last_run_at: Optional[datetime] = None


class DailyBriefing(BaseModel):
    date: str
    summary_text: str
    opportunities_discovered_count: int
    strong_matches_count: int
    applications_prepared_count: int
    applications_submitted_count: int
    interviews_detected_count: int
    contacts_identified_count: int
    needs_attention_count: int
    top_recommended_opportunities: List[Dict[str, Any]] = Field(default_factory=list)
