"""
OpportunityOS — SQLAlchemy Async ORM Models
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from apps.api.db import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CandidateProfileModel(Base):
    __tablename__ = "candidate_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    full_name = Column(String(255), nullable=False)
    headline = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    timezone = Column(String(100), nullable=False)
    preferred_working_hours = Column(String(100), default="09:00 - 18:00 UTC")
    countries_willing_to_work = Column(JSON, default=list)
    target_roles = Column(JSON, default=list)
    minimum_salary_annual = Column(Float, default=140000.0)
    minimum_hourly_rate = Column(Float, default=75.0)
    salary_currency = Column(String(10), default="USD")
    preferred_currencies = Column(JSON, default=list)
    remote_preference = Column(String(50), default="REMOTE")
    timezone_overlap_hours = Column(Integer, default=4)
    notice_period_days = Column(Integer, default=14)
    visa_sponsorship_needed = Column(Boolean, default=False)
    authorized_countries = Column(JSON, default=list)
    automation_level = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    skills = relationship("CandidateSkillModel", back_populates="profile", cascade="all, delete-orphan")
    knowledge_items = relationship("KnowledgeItemModel", back_populates="profile", cascade="all, delete-orphan")
    work_experiences = relationship("WorkExperienceModel", back_populates="profile", cascade="all, delete-orphan")


class CandidateSkillModel(Base):
    __tablename__ = "candidate_skills"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    category = Column(String(100), default="TECHNICAL")
    experience_years = Column(Float, nullable=False)
    proficiency = Column(String(50), default="ADVANCED")
    last_used = Column(String(100), default="Currently used")
    evidence = Column(JSON, default=list)
    related_projects = Column(JSON, default=list)

    profile = relationship("CandidateProfileModel", back_populates="skills")


class KnowledgeItemModel(Base):
    __tablename__ = "knowledge_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    raw_content = Column(Text, nullable=False)
    category = Column(String(100), default="ACCOMPLISHMENT")
    associated_skills = Column(JSON, default=list)
    quantified_impact = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("CandidateProfileModel", back_populates="knowledge_items")


class WorkExperienceModel(Base):
    __tablename__ = "work_experiences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    employment_type = Column(String(50), default="FULL_TIME")
    start_date = Column(String(50), nullable=False)
    end_date = Column(String(50), nullable=True)
    is_current = Column(Boolean, default=False)
    summary = Column(Text, nullable=False)
    key_achievements = Column(JSON, default=list)
    technologies = Column(JSON, default=list)

    profile = relationship("CandidateProfileModel", back_populates="work_experiences")


class OpportunityModel(Base):
    __tablename__ = "opportunities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    cluster_id = Column(String(36), nullable=True)
    source = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=True)
    url = Column(Text, nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    company_domain = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    location = Column(String(255), default="Remote")
    remote_type = Column(String(50), default="REMOTE")
    country = Column(String(100), default="Worldwide")
    timezone = Column(String(100), nullable=True)
    employment_type = Column(String(50), default="FULL_TIME")
    contract_duration = Column(String(100), nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(10), default="USD")
    hourly_rate = Column(Float, nullable=True)
    required_skills = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)
    experience_required_years = Column(Float, default=3.0)
    status = Column(String(50), default="DISCOVERED", index=True)
    date_posted = Column(DateTime, default=datetime.utcnow)
    raw_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    matching_score = relationship("MatchingScoreModel", back_populates="opportunity", uselist=False, cascade="all, delete-orphan")
    application = relationship("ApplicationModel", back_populates="opportunity", uselist=False, cascade="all, delete-orphan")
    contacts = relationship("ContactModel", back_populates="opportunity")


class MatchingScoreModel(Base):
    __tablename__ = "matching_scores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    opportunity_id = Column(String(36), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, unique=True)
    overall_match_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    technical_match = Column(Float, nullable=False)
    experience_match = Column(Float, nullable=False)
    remote_match = Column(Float, nullable=False)
    timezone_match = Column(Float, nullable=False)
    compensation_match = Column(Float, nullable=False)
    industry_match = Column(Float, nullable=False)
    role_match = Column(Float, nullable=False)
    transferable_skills = Column(JSON, default=dict)
    primary_strengths = Column(JSON, default=list)
    primary_gaps = Column(JSON, default=list)
    match_rationale = Column(Text, nullable=False)
    scored_at = Column(DateTime, default=datetime.utcnow)

    opportunity = relationship("OpportunityModel", back_populates="matching_score")


class ResumeVariantModel(Base):
    __tablename__ = "resume_variants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    opportunity_id = Column(String(36), nullable=True)
    variant_name = Column(String(255), nullable=False)
    headline = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    selected_skills = Column(JSON, default=list)
    reordered_experiences = Column(JSON, default=list)
    emphasized_achievements = Column(JSON, default=list)
    pdf_render_url = Column(String(255), nullable=True)
    content_hash = Column(String(64), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)


class CoverLetterModel(Base):
    __tablename__ = "cover_letters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    opportunity_id = Column(String(36), nullable=False)
    style = Column(String(50), default="TECHNICAL")
    content = Column(Text, nullable=False)
    key_selling_points = Column(JSON, default=list)
    generated_at = Column(DateTime, default=datetime.utcnow)


class ApplicationAnswerModel(Base):
    __tablename__ = "application_answers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_canonical = Column(String(255), nullable=False, unique=True)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    is_verified = Column(Boolean, default=True)
    confidence = Column(Float, default=1.0)
    source = Column(String(100), default="USER_PROFILE")
    last_verified = Column(DateTime, default=datetime.utcnow)


class ApplicationModel(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    opportunity_id = Column(String(36), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, unique=True)
    resume_variant_id = Column(String(36), ForeignKey("resume_variants.id"), nullable=True)
    cover_letter_id = Column(String(36), ForeignKey("cover_letters.id"), nullable=True)
    submission_mode = Column(String(50), default="APPROVAL")
    status = Column(String(50), default="PREPARED")  # PREPARED, NEEDS_APPROVAL, SUBMITTED, REJECTED
    submission_url = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    tasks = Column(JSON, default=list)  # Attached application tasks & status tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    opportunity = relationship("OpportunityModel", back_populates="application")
    resume_variant = relationship("ResumeVariantModel")
    cover_letter = relationship("CoverLetterModel")


class ContactModel(Base):
    __tablename__ = "contacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_name = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    linkedin_url = Column(Text, nullable=True)
    github_url = Column(Text, nullable=True)
    relationship_status = Column(String(50), default="NEW")
    associated_opportunity_id = Column(String(36), ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True)
    last_interaction_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    opportunity = relationship("OpportunityModel", back_populates="contacts")


class OutreachSequenceModel(Base):
    __tablename__ = "outreach_sequences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    opportunity_id = Column(String(36), nullable=False)
    contact_id = Column(String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="ACTIVE")
    current_step = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("OutreachMessageModel", back_populates="sequence", cascade="all, delete-orphan")


class OutreachMessageModel(Base):
    __tablename__ = "outreach_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sequence_id = Column(String(36), ForeignKey("outreach_sequences.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    channel = Column(String(50), default="EMAIL")
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    scheduled_for = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="PENDING")

    sequence = relationship("OutreachSequenceModel", back_populates="messages")


class AuditEventModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    actor = Column(String(100), default="SYSTEM_AGENT")
    reason = Column(Text, nullable=True)
    input_payload = Column(JSON, default=dict)
    output_payload = Column(JSON, default=dict)
    status = Column(String(50), default="SUCCESS")
    latency_ms = Column(Integer, default=0)


class SearchAgentModel(Base):
    __tablename__ = "search_agents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    keywords = Column(JSON, default=list)
    target_roles = Column(JSON, default=list)
    technologies = Column(JSON, default=list)
    excluded_keywords = Column(JSON, default=list)
    remote_only = Column(Boolean, default=True)
    minimum_compensation = Column(Float, nullable=True)
    schedule_cron = Column(String(100), default="0 */6 * * *")
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CrawlerSessionModel(Base):
    __tablename__ = "crawler_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    status = Column(String(50), default="COMPLETED")  # RUNNING, COMPLETED, FAILED
    mode = Column(String(50), default="IMMEDIATE")  # IMMEDIATE, SCHEDULED
    platforms_crawled = Column(JSON, default=list)
    total_discovered = Column(Integer, default=0)
    total_matched = Column(Integer, default=0)
    total_applied = Column(Integer, default=0)
    total_staged = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    max_duration_minutes = Column(Integer, default=15)
    max_applications = Column(Integer, default=5)
    summary_text = Column(Text, nullable=True)
    execution_logs = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class CrawlerScheduleModel(Base):
    __tablename__ = "crawler_schedules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    is_active = Column(Boolean, default=False)
    interval_hours = Column(Integer, default=6)
    max_duration_minutes = Column(Integer, default=15)
    max_applications = Column(Integer, default=5)
    min_match_score = Column(Float, default=80.0)
    auto_apply_enabled = Column(Boolean, default=True)
    target_platforms = Column(JSON, default=list)
    opportunity_types = Column(JSON, default=list)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


# -------------------------------------------------------------------
# Scraping Platform & Credentials Models
# -------------------------------------------------------------------

class ScrapingPlatformModel(Base):
    __tablename__ = "scraping_platforms"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    category = Column(String(50), default="JOB_BOARD")  # JOB_BOARD, PROJECT_CONTRIBUTIONS, FREELANCE, STARTUPS, COMMUNITY
    added_by = Column(String(50), default="USER")       # USER, AI
    requires_auth = Column(Boolean, default=False)
    auth_username = Column(String(255), nullable=True)  # User ID or Email for login
    auth_password = Column(String(255), nullable=True)  # Password for login
    auth_notes = Column(Text, nullable=True)            # Notes / instructions / 2FA hint
    status = Column(String(50), default="ACTIVE")       # ACTIVE, PAUSED
    crawl_frequency_hours = Column(Integer, default=6)
    last_scraped_at = Column(DateTime, nullable=True)
    total_opportunities_found = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AccountCredentialModel(Base):
    __tablename__ = "account_credentials"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    platform_name = Column(String(100), nullable=False, unique=True)  # e.g. "LINKEDIN", "WELLFOUND", "INDEED", "REMOTEOK", "GITHUB"
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    cookies = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# -------------------------------------------------------------------
# LinkedIn AI Growth Agent Models
# -------------------------------------------------------------------

class LinkedInProfileIntelligenceModel(Base):
    __tablename__ = "linkedin_profile_intelligences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, unique=True)
    overall_score = Column(Float, default=74.0)
    headline_score = Column(Float, default=72.0)
    about_score = Column(Float, default=68.0)
    experience_score = Column(Float, default=82.0)
    skills_score = Column(Float, default=64.0)
    projects_score = Column(Float, default=88.0)
    recruiter_discoverability_score = Column(Float, default=70.0)

    # Concrete optimization recommendations
    headline_current = Column(Text, nullable=True)
    headline_suggested = Column(Text, nullable=True)
    about_current = Column(Text, nullable=True)
    about_suggested = Column(Text, nullable=True)
    recommendations = Column(JSON, default=list)

    # Strategic configuration
    target_audience = Column(JSON, default=lambda: ["Recruiters", "Engineering Managers", "CTOs", "Founders"])
    target_geographies = Column(JSON, default=lambda: ["United States", "Europe", "India", "Remote Worldwide"])
    tone_preference = Column(String(50), default="Technical & Authoritative")
    content_preferences = Column(JSON, default=lambda: ["System Design", "Engineering Lessons", "Architecture", "Open Source"])

    # Personal Writing Style & Voice
    writing_style = Column(JSON, default=lambda: {
        "formality": "Professional yet conversational",
        "sentence_length": "Punchy and direct",
        "technical_depth": "High - architecture & code level",
        "emoji_usage": "Minimal / Structured",
        "storytelling": "Engineering problem -> real root cause -> architectural resolution"
    })
    writing_samples = Column(JSON, default=list)

    # Strategy Roadmaps & Topic Pillars
    topic_pillars = Column(JSON, default=lambda: [
        {"name": "Technical Deep-Dives", "percentage": 40, "color": "blue"},
        {"name": "Real Engineering Experiences", "percentage": 20, "color": "emerald"},
        {"name": "System Design & Architecture", "percentage": 15, "color": "purple"},
        {"name": "Career & Engineering Lessons", "percentage": 10, "color": "amber"},
        {"name": "Open-Source & Projects", "percentage": 10, "color": "cyan"},
        {"name": "Personal Professional Insights", "percentage": 5, "color": "rose"},
    ])
    seven_day_plan = Column(JSON, default=list)
    thirty_day_plan = Column(JSON, default=list)
    ninety_day_plan = Column(JSON, default=list)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LinkedInContentPostModel(Base):
    __tablename__ = "linkedin_content_posts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=False)
    post_type = Column(String(50), default="TECHNICAL_BREAKDOWN")  # TECHNICAL_BREAKDOWN, CASE_STUDY, ARCHITECTURE_LESSON, MINI_TUTORIAL, LESSONS_LEARNED, POLL_IDEA
    topic_pillar = Column(String(100), default="Technical Deep-Dives")
    grounded_sources = Column(JSON, default=list)  # e.g., ["GitHub Commit: Implemented Redis distributed lock", "Production Incident #402"]
    quality_checks = Column(JSON, default=lambda: {
        "fact_check_passed": True,
        "confidential_data_cleared": True,
        "tone_aligned": True,
        "anti_generic_score": 94,
        "originality_score": 96
    })
    status = Column(String(50), default="DRAFT")  # DRAFT, SCHEDULED, APPROVAL_REQUIRED, PUBLISHED, SKIPPED
    scheduled_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    metrics = Column(JSON, default=lambda: {
        "impressions": 0,
        "comments": 0,
        "meaningful_replies": 0,
        "inbound_opportunities": 0
    })
    created_at = Column(DateTime, default=datetime.utcnow)


class LinkedInRelationshipModel(Base):
    __tablename__ = "linkedin_relationships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    headline = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    category = Column(String(50), default="ENGINEERING_LEADER")  # RECRUITER, HIRING_MANAGER, CTO, ENGINEERING_LEADER, FOUNDER, PEER_ENGINEER
    relationship_score = Column(Float, default=85.0)  # 0-100
    relationship_stage = Column(String(50), default="DISCOVERED")  # DISCOVERED, INTERESTING, CONNECTION_PROPOSED, CONNECTED, CONVERSATION_STARTED, WARM_RELATIONSHIP, OPPORTUNITY, INACTIVE
    score_reasons = Column(JSON, default=list)
    why_connect = Column(Text, nullable=True)
    potential_conversation_topic = Column(Text, nullable=True)
    suggested_connection_message = Column(Text, nullable=True)
    connection_sent_at = Column(DateTime, nullable=True)
    connected_at = Column(DateTime, nullable=True)
    last_interaction_at = Column(DateTime, nullable=True)
    conversation_summary = Column(Text, nullable=True)
    topics_discussed = Column(JSON, default=list)
    follow_up_recommendation = Column(Text, nullable=True)
    next_action = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LinkedInConversationModel(Base):
    __tablename__ = "linkedin_conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    relationship_id = Column(String(36), ForeignKey("linkedin_relationships.id", ondelete="CASCADE"), nullable=False)
    participant_name = Column(String(255), nullable=False)
    participant_role = Column(String(255), nullable=False)
    classification = Column(String(50), default="JOB_OPPORTUNITY")  # RECRUITER, JOB_OPPORTUNITY, CLIENT, COLLABORATION, NETWORKING, TECHNICAL_DISCUSSION, SALES, SPAM
    messages = Column(JSON, default=list)
    suggested_reply = Column(Text, nullable=True)
    requires_human_approval = Column(Boolean, default=True)  # True for salary, job commitments, interview scheduling
    follow_up_due_at = Column(DateTime, nullable=True)
    follow_up_status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LinkedInCommentOpportunityModel(Base):
    __tablename__ = "linkedin_comment_opportunities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    post_author = Column(String(255), nullable=False)
    post_author_role = Column(String(255), nullable=False)
    post_author_company = Column(String(255), nullable=False)
    post_url = Column(String(500), nullable=True)
    post_topic = Column(String(255), nullable=False)
    post_snippet = Column(Text, nullable=False)
    relevance_score = Column(Float, default=90.0)
    expertise_fit_score = Column(Float, default=92.0)
    suggested_comment = Column(Text, nullable=False)
    status = Column(String(50), default="SUGGESTED")  # SUGGESTED, APPROVED, POSTED, DISMISSED
    created_at = Column(DateTime, default=datetime.utcnow)


class LinkedInAgentActionModel(Base):
    __tablename__ = "linkedin_agent_actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(50), nullable=False)  # CONNECTION_RECOMMENDATION, CONTENT_PUBLISH, CONVERSATION_REPLY, FOLLOW_UP_TRIGGER, COMMENT_OPPORTUNITY, PROFILE_UPDATE, NO_ACTION
    target_id = Column(String(255), nullable=True)
    target_name = Column(String(255), nullable=True)
    expected_value = Column(Float, default=0.85)  # 0.0 - 1.0
    risk_score = Column(Float, default=0.10)      # 0.0 - 1.0
    execution_mode = Column(String(50), default="COPILOT")  # AUTOPILOT, COPILOT, MANUAL
    approval_status = Column(String(50), default="PENDING_APPROVAL")  # AUTO, PENDING_APPROVAL, APPROVED, REJECTED, BLOCKED, EXECUTED
    policy_check_passed = Column(Boolean, default=True)
    risk_assessment_passed = Column(Boolean, default=True)
    action_payload = Column(JSON, default=dict)
    reasoning = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)


class TargetCompanyIntelligenceModel(Base):
    __tablename__ = "target_company_intelligences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True)
    industry = Column(String(100), default="Technology")
    target_priority = Column(String(50), default="HIGH")  # HIGH, MEDIUM, LOW
    open_roles = Column(JSON, default=list)
    key_leaders = Column(JSON, default=list)
    recruiters = Column(JSON, default=list)
    tech_stack = Column(JSON, default=list)
    networking_plan = Column(JSON, default=list)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

