# OpportunityOS — System Architecture & Specification Document

> **System Name:** OpportunityOS  
> **Status:** Production-Ready Architectural Blueprint  
> **Role:** AI-Powered Career Development, Opportunity Discovery, Application Automation, and Relationship Platform  
> **Author:** Principal Software Architect, AI Engineer & Senior UX Engineer  

---

## 1. Executive Summary & Core Philosophy

**OpportunityOS** is not a superficial job auto-apply bot. It is an enterprise-grade, privacy-respecting, autonomous **personal career and business development agent**.

### The Core Loop
```
DISCOVER 
  → NORMALIZE & DEDUPLICATE 
  → ANALYZE & DEEP MATCH 
  → COMPANY & CONTACT RESEARCH 
  → TAILOR RESUME & COVER LETTER 
  → APPROVAL GATE / AUTOMATION LEVEL DECISION 
  → SUBMIT (Auto or Assisted) 
  → OUTREACH & SEQUENCE DISPATCH 
  → TRACK INBOUND RESPONSES & INTERVIEWS 
  → RE-SCORE & LEARN FROM OUTCOMES
```

### Safety & Integrity Manifesto
1. **Zero Falsification:** The system NEVER invents experience, employment dates, degrees, certifications, or work authorization. All AI generations are grounded in the verified **Candidate Knowledge Base**.
2. **No Bot Evasion / CAPTCHA Bypass:** Never attempts to break anti-bot systems or bypass CAPTCHAs. If a destination requires manual proof of humanity or complex legal declarations, execution safely pauses and transfers to the **"Needs Attention"** queue.
3. **Audited Transparency:** Every single external query, scoring rationale, LLM prompt/completion, and automated action is recorded as an immutable, cryptographically timestamped **Audit Log Event**.
4. **User In Control:** Configurable Automation Levels (Level 0 through Level 5) govern application submission, outreach, and follow-ups independently.

---

## 2. Technology Architecture & Monorepo Structure

### Monorepo Layout
```
opportunity-os/
├── apps/
│   ├── api/                     # FastAPI (Python 3.11+ / 3.12+), Pydantic v2, SQLAlchemy 2.0 Async
│   ├── web/                     # Next.js 14+ (App Router), React 18/19, TypeScript, Tailwind CSS
│   ├── worker/                  # Temporal Worker & Playwright Automation Handlers
│   └── browser-extension/       # Chromium MV3 Extension for 1-click ingest & assisted fill
├── packages/
│   ├── domain/                  # Canonical Pydantic schemas, enums, and domain contracts
│   ├── ai/                      # AI Provider Abstraction (OpenAI, Anthropic, Gemini, Local, Rule/Heuristic)
│   ├── matching/                # Deterministic + Semantic Multi-Dimensional Scoring Engine
│   └── connectors/              # Pluggable opportunity ingestion plugins (HN, GitHub, RSS, ATS, Manual)
├── infra/
│   ├── docker/                  # Multi-stage Dockerfiles
│   ├── docker-compose.yml       # Complete local infrastructure (Postgres+pgvector, Redis, Temporal, API, Web)
│   └── .env.example             # Documented environment variables
├── docs/                        # Architecture, API specs, schemas, and workflows
└── tests/                       # Pytest unit/integration & Playwright E2E tests
```

### Subsystem Stack
- **Primary Backend:** Python 3.11+ with **FastAPI**, **Pydantic v2**, and **SQLAlchemy 2.0 (Asyncpg)**. Provides strict typing, sub-millisecond route dispatch, auto-generated OpenAPI 3.1 specs, and background task dispatch.
- **Frontend:** **Next.js** (App Router) + **TypeScript** + **Tailwind CSS**. Styled with a high-density, dark-mode-first aesthetic inspired by Linear, modern ATS platforms, and HubSpot CRM. Features TanStack Query for cache sync, micro-animations, and keyboard command palette (`Cmd+K`).
- **Data Persistence:** **PostgreSQL 16+** with **pgvector** for semantic embeddings of candidate evidence and job descriptions.
- **Cache & Event Bus:** **Redis 7+** for rate-limiting counters, temporary caching, and pub/sub for real-time activity feeds.
- **Orchestration:** **Temporal.io** for durable workflow execution, human-in-the-loop approvals, exponential backoff retries, and scheduled follow-up timers. Provides local deterministic fallbacks for standalone dev.
- **Automation Engine:** **Playwright** running in headless container workers with isolated browser contexts, structured DOM inspection, and screenshot audit records.
- **Document Engine:** Headless PDF & HTML rendering engine for compiling dynamic resume variants and cover letters from clean typography templates.

---

## 3. Canonical Domain Models

### Candidate Profile & Knowledge Base
- `CandidateProfile`: Personal details, location, timezone, preferred working hours, countries allowed, target roles, minimum acceptable compensation (hourly/annual), visa/sponsorship requirements, and automation preferences.
- `CandidateSkill`: Name, years of experience, proficiency level (`BEGINNER`, `INTERMEDIATE`, `ADVANCED`, `EXPERT`), last used date, verified evidence links, and related project IDs.
- `KnowledgeItem`: Granular verified career evidence (e.g., "Reduced frontend load time by 42% via SSR migration"), tagged with technologies, metrics, and project references.
- `MasterResume`: Canonical source of truth structured resume with full employment history, education, certifications, and architectural accomplishments.
- `ResumeVariant`: Generated targeted resume customized for a specific role or archetype (e.g., "Senior React Native Contract" vs. "Founding Platform Engineer").

### Opportunity & Company Intelligence
- `Opportunity`: Canonical normalized opportunity model containing:
  - `id`, `cluster_id` (for deduplication across boards)
  - `source`, `external_id`, `url`, `title`, `company_name`, `company_domain`
  - `opportunity_type` (`FULL_TIME`, `CONTRACT`, `FREELANCE`, `OPEN_SOURCE`, `CONSULTING`, `FOUNDING_ENGINEER`, etc.)
  - `location`, `remote_type` (`REMOTE`, `HYBRID`, `ONSITE`), `country`, `timezone`
  - `salary_min`, `salary_max`, `salary_currency`, `hourly_rate`
  - `required_skills`, `preferred_skills`, `experience_years_required`
  - `status` (Kanban pipeline state)
  - `raw_content`, `created_at`, `updated_at`
- `MatchingScore`: Multi-dimensional score breakdown (Technical, Experience, Remote, Timezone, Compensation, Industry, Role, Overall 0-100, confidence score, transferable skills matrix, and natural-language rationale).
- `Company`: Company intelligence record including tech stack, employee scale, funding state, engineering blog insights, and hiring contacts.
- `Contact`: Recruiter, Engineering Manager, Founder, or Maintainer with relationship status (`NEW`, `CONTACTED`, `RESPONDED`, `CONNECTED`, `INTERVIEWING`).

### Application, Outreach & Audit
- `Application`: Tracks an application from preparation to submission (`DRAFT`, `NEEDS_APPROVAL`, `SUBMITTED`, `ACKNOWLEDGED`, `UNDER_REVIEW`, `INTERVIEW`, `OFFER`, `REJECTED`, `WITHDRAWN`).
- `ApplicationAnswer`: Verified Q&A memory for recurrent application questions (e.g., work authorization, notice period, salary floor) with source provenance.
- `OutreachSequence`: Configurable drip cadence (Day 0 application, Day 1 hiring manager greeting, Day 4 value follow-up, Day 9 closure check).
- `AuditEvent`: Immutable log record containing `event_id`, `timestamp`, `entity_type`, `entity_id`, `action`, `actor`, `input_summary`, `output_summary`, `status`, and `latency_ms`.

---

## 4. Multi-Dimensional Matching Engine

The matching engine refuses to treat applicant evaluation as a black-box prompt or a naive keyword check. It blends **deterministic constraint checking** with **semantic transferable skill reasoning**:

$$\text{Overall Score} = \sum w_i \cdot S_i - \text{Penalty}_{\text{mismatch}}$$

### Score Dimensions & Weights
1. **Technical Skills Match (25%):**
   - Exact requirement matches (1.0 weight)
   - Transferable skill equivalence (0.75 weight, e.g., FastAPI experience applied to Express/NestJS, or AWS applied to GCP)
   - Preferred qualifications match (0.4 weight)
2. **Experience & Seniority Match (20%):**
   - Years of experience delta vs. required threshold
   - Scope of responsibility (individual contributor vs. tech lead vs. founding engineer)
3. **Role & Domain Alignment (15%):**
   - Architectural match (systems programming, real-time frontend, distributed backend, AI workflows)
4. **Remote & Timezone Compatibility (15%):**
   - Overlap hours (minimum 4 hours required for standard remote contracts)
   - Country work eligibility / legal residency constraints
5. **Compensation Alignment (15%):**
   - Satisfies candidate's minimum hourly rate or base salary expectations
6. **Project & Portfolio Evidence (10%):**
   - Grounded verifiable portfolio code or live deployments demonstrating required capabilities

---

## 5. Automation Levels & Decision Framework

The user controls risk through granular **Automation Levels**:

| Level | Name | Ingestion | Tailoring | Outreach | Submission |
|---|---|---|---|---|---|
| **0** | **Discovery Only** | Auto | Manual | Disabled | Manual |
| **1** | **Recommendation** | Auto | Auto-suggestions | Disabled | Manual |
| **2** | **Preparation** | Auto | Auto-generates resume & letter | Drafts created | Manual submission |
| **3** | **Approval Gate (Default)** | Auto | Fully prepared package | Sequence staged | **1-Click User Approval** |
| **4** | **High-Confidence Auto** | Auto | Auto | Sequence staged | **Auto-submit if Score $\ge$ 88** |
| **5** | **Autonomous Agent** | Auto | Auto | Drip sequence auto-dispatched | **Auto-submit + Outreach** |

### Safety Circuit Breakers:
Execution automatically halts and diverts to **Needs Attention** if:
- A CAPTCHA or Cloudflare Turnstile challenge is encountered.
- Unverified legal/work sponsorship declarations are requested.
- Salary or compensation questions outside user-approved boundaries appear.
- Destination forms request demographic/EEOC data without explicit pre-saved user rules.

---

## 6. AI Provider Abstraction & Cost Architecture

The AI subsystem exposes a clean, provider-agnostic interface:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate_structured(
        self, 
        prompt: str, 
        schema: Type[BaseModel], 
        system_prompt: str = ""
    ) -> BaseModel:
        pass
```

### Supported Providers:
- **Anthropic Claude 3.5 Sonnet:** High-reasoning tasks (tailored resume generation, nuanced cover letters, gap analysis).
- **OpenAI GPT-4o / GPT-4o-mini:** Cost-efficient classification, question extraction, and email triage.
- **Google Gemini 1.5 Pro / Flash:** Massive context ingestion (parsing entire company engineering blogs and 50-page ATS specs).
- **Local Ollama / vLLM:** On-premise private inference without third-party data egress.
- **Heuristic / Deterministic Fallback:** Built-in rule-based engine providing instant zero-API-key operation for local development and offline environments.

---

## 7. Opportunity Discovery & Source Connectors

All discovery feeds implement the `OpportunitySource` contract:

```python
class OpportunitySource(ABC):
    source_name: str
    
    @abstractmethod
    async def discover(self, search_query: SearchCriteria) -> List[RawOpportunity]:
        """Fetch listings from external API, RSS, or HTML feeds."""
        pass
        
    @abstractmethod
    async def normalize(self, raw: RawOpportunity) -> Opportunity:
        """Map heterogeneous payloads to canonical Opportunity schema."""
        pass
```

### Initial Connectors:
1. **Hacker News "Who is Hiring" Connector:** Parses monthly community hiring threads, extracts remote status, compensation, and tech stacks.
2. **GitHub Repositories & Paid Issues Connector:** Discovers high-impact open-source contribution opportunities, bounties, and Good First Issues matching candidate skills.
3. **Remote Tech RSS / JSON Feed Connector:** Ingests live curated feeds (WeWorkRemotely, RemoteOK, job board feeds).
4. **Manual Universal Ingestion:** Allows direct input of arbitrary job URLs, recruiter emails, or raw markdown descriptions.

---

## 8. Security & Secret Management

- **Zero Client-Side Secrets:** No LLM or database credentials ever touch the frontend.
- **Encryption at Rest:** Sensitive tokens (OAuth mailbox refresh tokens, LinkedIn cookies) are encrypted using AES-GCM-256 with keys stored in environment secrets.
- **Scoped Playwright Sandboxes:** Automated browser runs operate within ephemeral ephemeral containers with temporary user-data directories, strictly isolating sessions.
- **Audit Masking:** All log handlers automatically scrub bearer tokens, passwords, and sensitive personally identifiable information.

---

## 9. Phased Implementation Roadmap

### Phase 1: Core Vertical Slice (Current Milestone)
- [x] Full Architectural Spec & Canonical Schemas
- [x] Monorepo Scaffold (FastAPI + Next.js + Worker)
- [x] Candidate Profile & Knowledge Base Engine
- [x] Multi-Source Opportunity Ingestion & Canonical Normalizer
- [x] Multi-Dimensional Deterministic + Semantic Matcher
- [x] Resume Variant & Tailored Cover Letter Generator
- [x] Application Q&A Memory & Approval Queue
- [x] Recruiter & Hiring Manager Mini-CRM
- [x] Immutable Audit Logging & Real-Time Automation Activity Feed
- [x] Daily AI Briefing & Command Palette
- [x] High-Aesthetic Linear-Grade Next.js Dashboard

### Phase 2: Autonomous Workflows & Extension
- Temporal workflow workers with Playwright adapters
- Chrome browser extension for 1-click page ingestion
- Real-time IMAP/OAuth email monitoring & classification

### Phase 3: Network Graph & Learning Engine
- Candidate outcome reinforcement learning (adaptive weights)
- Consulting project proposal generator & contract rate forecast
