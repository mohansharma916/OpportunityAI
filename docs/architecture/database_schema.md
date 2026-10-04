# OpportunityOS — Domain Models & PostgreSQL Schema Specification

## 1. Domain Entities & Schemas

### 1.1 Candidate Profile & Career Knowledge
```sql
-- Core user entity
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rich candidate profile
CREATE TABLE candidate_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    headline VARCHAR(255),
    location VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    timezone VARCHAR(100) NOT NULL,
    preferred_working_hours VARCHAR(100) DEFAULT '09:00 - 18:00 UTC',
    countries_willing_to_work JSONB DEFAULT '["US", "EU", "UK", "CA", "Worldwide Remote"]'::jsonb,
    target_roles JSONB DEFAULT '["Senior Frontend Engineer", "Staff Engineer", "Full Stack Architect"]'::jsonb,
    minimum_salary_annual NUMERIC(12, 2) DEFAULT 140000,
    minimum_hourly_rate NUMERIC(8, 2) DEFAULT 75.00,
    preferred_currencies JSONB DEFAULT '["USD", "EUR", "GBP"]'::jsonb,
    remote_preference VARCHAR(50) DEFAULT 'REMOTE_ONLY',
    timezone_overlap_hours INT DEFAULT 4,
    notice_period_days INT DEFAULT 14,
    visa_sponsorship_needed BOOLEAN DEFAULT FALSE,
    authorized_countries JSONB DEFAULT '["US", "EU"]'::jsonb,
    automation_level INT DEFAULT 3, -- 0: Discovery, 3: Approval, 5: Full Auto
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reusable granular skills with evidence
CREATE TABLE candidate_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    skill_name VARCHAR(100) NOT NULL,
    category VARCHAR(100) DEFAULT 'TECHNICAL', -- TECHNICAL, ARCHITECTURE, LEADERSHIP
    experience_years NUMERIC(4, 1) NOT NULL,
    proficiency VARCHAR(50) NOT NULL, -- BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
    last_used VARCHAR(50) DEFAULT 'Currently used',
    evidence TEXT[],
    related_projects TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Granular evidence items
CREATE TABLE knowledge_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    raw_content TEXT NOT NULL,
    category VARCHAR(100) NOT NULL, -- ACCOMPLISHMENT, ARCHITECTURE, LEADERSHIP, CASE_STUDY
    associated_skills TEXT[] DEFAULT '{}',
    quantified_impact VARCHAR(255),
    embedding vector(1536), -- pgvector for semantic retrieval
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Work experiences
CREATE TABLE work_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    company VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    employment_type VARCHAR(50) DEFAULT 'FULL_TIME',
    start_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    summary TEXT,
    key_achievements TEXT[] DEFAULT '{}',
    technologies TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 1.2 Opportunities, Deduplication & Scoring
```sql
-- Deduplication clusters
CREATE TABLE opportunity_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_title VARCHAR(255) NOT NULL,
    canonical_company VARCHAR(255) NOT NULL,
    first_discovered_at TIMESTAMPTZ DEFAULT NOW()
);

-- Normalized Opportunities
CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id UUID REFERENCES opportunity_clusters(id) ON DELETE SET NULL,
    source VARCHAR(100) NOT NULL, -- HACKER_NEWS, GITHUB, REMOTE_OK, MANUAL, GREENHOUSE, etc.
    external_id VARCHAR(255),
    url TEXT NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    company_domain VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(255),
    remote_type VARCHAR(50) DEFAULT 'REMOTE', -- REMOTE, HYBRID, ONSITE
    country VARCHAR(100),
    timezone VARCHAR(100),
    employment_type VARCHAR(50) DEFAULT 'FULL_TIME', -- FULL_TIME, CONTRACT, FREELANCE, OPEN_SOURCE, FOUNDING_ENGINEER, etc.
    contract_duration VARCHAR(100),
    salary_min NUMERIC(12, 2),
    salary_max NUMERIC(12, 2),
    salary_currency VARCHAR(10) DEFAULT 'USD',
    hourly_rate NUMERIC(8, 2),
    required_skills TEXT[] DEFAULT '{}',
    preferred_skills TEXT[] DEFAULT '{}',
    experience_required_years NUMERIC(4, 1),
    date_posted TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'DISCOVERED', -- DISCOVERED, AI_REVIEWING, STRONG_MATCH, PREPARED, NEEDS_APPROVAL, APPLIED, CONTACTED, INTERVIEWING, OFFER, REJECTED, ARCHIVED
    raw_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_company ON opportunities(company_name);
CREATE INDEX idx_opportunities_source ON opportunities(source);

-- Multi-Dimensional Matching Scores
CREATE TABLE matching_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    overall_match_score NUMERIC(5, 2) NOT NULL, -- 0 to 100
    confidence_score NUMERIC(5, 2) NOT NULL,   -- 0 to 100
    technical_match NUMERIC(5, 2) NOT NULL,
    experience_match NUMERIC(5, 2) NOT NULL,
    remote_match NUMERIC(5, 2) NOT NULL,
    timezone_match NUMERIC(5, 2) NOT NULL,
    compensation_match NUMERIC(5, 2) NOT NULL,
    industry_match NUMERIC(5, 2) NOT NULL,
    role_match NUMERIC(5, 2) NOT NULL,
    transferable_skills JSONB DEFAULT '{}'::jsonb,
    primary_strengths TEXT[] DEFAULT '{}',
    primary_gaps TEXT[] DEFAULT '{}',
    match_rationale TEXT NOT NULL,
    scored_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 1.3 Tailored Application Packages & Verified Q&A Memory
```sql
-- Generated Tailored Resumes
CREATE TABLE resume_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    variant_name VARCHAR(255) NOT NULL, -- e.g. "Senior React & Node.js Tailored Resume"
    headline VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    selected_skills TEXT[] DEFAULT '{}',
    reordered_experiences JSONB NOT NULL,
    emphasized_achievements TEXT[] DEFAULT '{}',
    pdf_render_url TEXT,
    content_hash VARCHAR(64) NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cover letters
CREATE TABLE cover_letters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    style VARCHAR(50) DEFAULT 'TECHNICAL', -- SHORT, PROFESSIONAL, TECHNICAL, STARTUP, CONVERSATIONAL, CONSULTING
    content TEXT NOT NULL,
    key_selling_points TEXT[] DEFAULT '{}',
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Verified Q&A Memory
CREATE TABLE application_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    question_canonical VARCHAR(255) NOT NULL, -- e.g. "work_authorization_us"
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    is_verified BOOLEAN DEFAULT TRUE,
    confidence NUMERIC(4, 2) DEFAULT 1.0,
    source VARCHAR(100) DEFAULT 'USER_PROFILE',
    last_verified TIMESTAMPTZ DEFAULT NOW()
);

-- Active Applications
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    resume_variant_id UUID REFERENCES resume_variants(id) ON DELETE SET NULL,
    cover_letter_id UUID REFERENCES cover_letters(id) ON DELETE SET NULL,
    submission_mode VARCHAR(50) DEFAULT 'APPROVAL', -- MANUAL, APPROVAL, AUTO
    status VARCHAR(50) DEFAULT 'PREPARED', -- PREPARED, NEEDS_APPROVAL, SUBMITTED, REJECTED, WITHDRAWN
    submission_url TEXT,
    submitted_at TIMESTAMPTZ,
    error_message TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 1.4 CRM, Contacts, Outreach & Audit
```sql
-- Hiring Contacts & Networking Mini-CRM
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL, -- RECRUITER, ENGINEERING_MANAGER, CTO, FOUNDER, MAINTAINER
    email VARCHAR(255),
    linkedin_url TEXT,
    github_url TEXT,
    relationship_status VARCHAR(50) DEFAULT 'NEW', -- NEW, CONTACTED, RESPONDED, CONNECTED, INTERVIEWING, CLOSED
    associated_opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    last_interaction_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Outreach Sequences & Follow-up Cadence
CREATE TABLE outreach_sequences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'ACTIVE', -- ACTIVE, PAUSED, COMPLETED, CANCELLED_REPLIED
    current_step INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE outreach_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sequence_id UUID REFERENCES outreach_sequences(id) ON DELETE CASCADE,
    step_number INT NOT NULL,
    channel VARCHAR(50) DEFAULT 'EMAIL', -- EMAIL, LINKEDIN, GITHUB
    subject VARCHAR(255),
    body TEXT NOT NULL,
    scheduled_for TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, SENT, FAILED, CANCELLED
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Immutable Real-Time Audit Log
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    entity_type VARCHAR(100) NOT NULL, -- OPPORTUNITY, APPLICATION, RESUME, OUTREACH, AGENT
    entity_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,      -- DISCOVERED, SCORED, PREPARED, SUBMITTED, OUTREACH_SENT
    actor VARCHAR(100) DEFAULT 'SYSTEM_AGENT',
    reason TEXT,
    input_payload JSONB DEFAULT '{}'::jsonb,
    output_payload JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'SUCCESS', -- SUCCESS, WARNING, FAILED, HALTED_HUMAN_ATTENTION
    latency_ms INT DEFAULT 0
);

CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);

-- Persistent Smart Search Agents
CREATE TABLE search_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    target_roles TEXT[] DEFAULT '{}',
    technologies TEXT[] DEFAULT '{}',
    excluded_keywords TEXT[] DEFAULT '{}',
    remote_only BOOLEAN DEFAULT TRUE,
    minimum_compensation NUMERIC(10, 2),
    schedule_cron VARCHAR(100) DEFAULT '0 */6 * * *',
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```
