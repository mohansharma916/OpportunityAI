# OpportunityOS

> **AI-Powered Career Development, Opportunity Discovery, Application Automation & Networking Platform**

OpportunityOS is an autonomous personal career and business development agent engineered to continuously discover, evaluate, tailor, and execute opportunities worldwide across:
- **Remote Full-Time & Contract Roles** (Worldwide, US, EU, UK, Canada, Australia)
- **Open-Source Contributions & Paid Engineering Bounties** (GitHub / Algora)
- **Founding Engineer & Fractional Architect Engagements**
- **Consulting & High-Impact Technical Projects**

Unlike mass auto-apply bots, OpportunityOS operates with strict **zero-hallucination ground truth**, **never invents credentials or legal declarations**, **never bypasses CAPTCHAs**, and maintains an **immutable audit log** with full **human-in-the-loop oversight**.

---

## Quick Start Guide

### Prerequisites
- **Python 3.11+** (managed via `uv` or `venv`)
- **Node.js 20+** and **pnpm** (or `npm`)
- **Docker** (optional, for containerized PostgreSQL 16 + pgvector, Redis, and Temporal)

---

### Option A: Native Local Development (Recommended)

#### 1. Setup & Launch Backend API (FastAPI)
```bash
cd /Users/user/Documents/Projects/opportunity-os

# Create and activate virtual environment (if not already active)
uv venv .venv
source .venv/bin/activate

# Install dependencies (if not already installed)
uv pip install fastapi "uvicorn[standard]" pydantic "sqlalchemy[asyncio]" greenlet aiosqlite asyncpg httpx jinja2 python-multipart pytest pytest-asyncio

# Start the FastAPI server (Port 8000)
PYTHONPATH=. uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```
- **API Base:** `http://localhost:8000`
- **Interactive OpenAPI Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

#### 2. Setup & Launch Frontend (Next.js 14+)
In a separate terminal window:
```bash
cd /Users/user/Documents/Projects/opportunity-os/apps/web

# Install dependencies
pnpm install

# Start the Next.js dev server (Port 3000)
pnpm dev

# Or run the production build
# pnpm build && pnpm start
```
- **Web Dashboard:** [http://localhost:3000](http://localhost:3000)

---

### Option B: Docker Compose (All-in-One)

To spin up the entire infrastructure (PostgreSQL 16 with pgvector, Redis, Temporal, API, and Web) with a single command:

```bash
cd /Users/user/Documents/Projects/opportunity-os

# Start all containers in the background
docker compose up -d
```

| Service | Local Port | Notes |
|---|---|---|
| **Web Dashboard** | `http://localhost:3000` | Next.js 14 Dark Theme |
| **FastAPI Backend** | `http://localhost:8000` | Swagger UI at `/docs` |
| **PostgreSQL + pgvector** | `localhost:5434` | Configured to avoid port 5432 collision |
| **Redis 7** | `localhost:6380` | Cache & Rate Limiting |

To stop all services:
```bash
docker compose down
```

---

## Running Automated Tests

Run the full integration test suites covering the entire end-to-end lifecycle:

```bash
cd /Users/user/Documents/Projects/opportunity-os

# 1. Run Candidate Onboarding, Resume Parsing & Auth Test
.venv/bin/pytest tests/test_onboarding_and_auth.py -v

# 2. Run Auto-Apply Decision Engine & Safety Circuit Breakers Test
.venv/bin/pytest tests/test_auto_apply.py -v

# 3. Run Full 11-Stage Pipeline Vertical Slice Integration Test
.venv/bin/pytest tests/test_api_and_pipeline.py -v

# Run all suites together:
.venv/bin/pytest tests/ -v
```

---

## Key Features & How to Use the Platform

### 1. Candidate Authentication & Adaptive Onboarding Flow
- **Sign In / Sign Up**: On first visit, register an account or click **"Quick Demo Login"** to inspect pre-seeded data.
- **Candidate Onboarding Wizard**:
  1. **Step 1: Resume Ingestion**: Paste or upload raw resume text, markdown, or export. Includes a 1-click **"Load Sample Resume"** button for immediate testing.
  2. **Step 2: AI Parsing & Missing Info Prompt**: The AI extracts verified technical skills, architecture accomplishments, and work history, and prompts for missing critical parameters:
     - Target roles (e.g. Staff Full Stack, Distributed Systems, Founding Engineer)
     - Minimum annual salary floor & minimum hourly contract rate floor
     - Authorized countries without sponsorship & visa requirements
     - Notice period & desired automation level (Level 2 to Level 5)
  3. **Step 3: Multi-Section Verification**: The candidate reviews and can edit all parsed details, add/remove custom skills, and inspect verified accomplishments.
  4. **Step 4: Global Web Scraping & Autonomous Execution**: Upon clicking **"Verify Profile & Launch Global Discovery"**:
     - The backend locks in verified candidate memory (zero-hallucination ground truth).
     - Crawlers instantly scrape live global feeds (Jobicy worldwide engineering, Arbeitnow European/international remote, GitHub Issues with `good first issue` / `help-wanted` tags).
     - Multi-dimensional fit scoring evaluates all opportunities against the candidate's verified profile.
     - If Automation Level 4 or 5 is configured, qualifying opportunities (≥80% match, safe channels) are auto-applied with tailored resumes and cover letters.
     - Displays discovery metrics before redirecting into the Command Center.

### 2. Daily AI Briefing & Command Center
- Open [http://localhost:3000](http://localhost:3000).
- View the executive daily briefing answering **"What happened today?"** (e.g. opportunities discovered, high-fit matches, applications prepared, interviews detected).
- Click **"Run Discovery Cycle"** to scan live sources.

### 3. Interactive Kanban Pipeline
- Track opportunities through stages: `Discovered` → `AI Reviewing` → `Strong Match` → `Prepared` → `Needs Approval` → `Needs Attention` → `Applied` → `Interviewing`.
- Filter by **High Fit (≥80%)**, **Contracts ($/hr)**, or **Open Source Contributions**.
- Click **"Auto-Apply (L4/L5)"** on the board header to trigger automated submission runs for high-fit roles.
- Click any card to view the multi-dimensional match breakdown and natural language rationale.

### 4. Multi-Dimensional Matching Engine
- Evaluates fit across **Technical Skills** (with transferable skill mapping like FastAPI ↔ Express, PostgreSQL ↔ SQLite), **Experience Depth**, **Role Alignment**, **Remote Setup**, **Timezone Overlap**, and **Compensation Floor**.
- Clearly highlights **transferable skills** and **potential skill deltas**.

### 5. Application Package Review & Approval
- Click **"Prepare Application"** on any opportunity card.
- The engine compiles a **targeted resume variant** and **tailored cover letter** (Technical, Startup, or Consulting styles) without inventing facts.
- Review the side-by-side evidence comparison and click **"Approve & Submit"**.

### 6. Natural Language AI Command Bar (`⌘K`)
- Press `⌘K` or click the search bar at the top to run agent commands:
  - `"Prepare applications for everything above 85% match"`
  - `"Increase minimum contract rate to $95/hour"`
  - `"Discover new global opportunities"`
  - `"Find open source projects and paid bounties"`
  - `"Set automation level to 4"`

### 7. Universal Manual Ingestion
- Click **"+ Import URL/Text"** in the top navigation.
- Paste any arbitrary job URL, markdown text, or recruiter email. The engine parses requirements, compensation, and remote terms automatically.

### 8. Hiring Contacts & Outreach CRM
- Maps recruiters, engineering managers, and maintainers.
- Stages respectful 3-step drip outreach cadences (Day 1 intro, Day 4 follow-up, Day 9 closure) that automatically pause when a response is received.

### 9. Immutable Audit Trail
- Every external query, scoring calculation, generation, and submission is recorded cryptographically with timestamps, actor IDs, and input/output payloads.

---

## Repository Structure

```
opportunity-os/
├── apps/
│   ├── api/                      # FastAPI, Pydantic v2, SQLAlchemy 2.0 Async
│   │   ├── main.py               # REST endpoints & startup lifecycle
│   │   ├── models.py             # ORM models (Opportunities, Profiles, Scores, Applications)
│   │   ├── db.py                 # Async database session engine
│   │   └── services/             # Profile, Opportunity, Matching, Application, CRM, AI
│   ├── web/                      # Next.js 14+ (App Router), React 18, Tailwind CSS, TypeScript
│   │   ├── src/app/              # Layout, page.tsx, globals.css (Linear dark aesthetic)
│   │   └── src/components/       # Navigation, DailyBriefing, KanbanBoard, Modals, Analytics
│   └── worker/                   # Playwright automation worker with safety circuit breakers
├── packages/
│   ├── domain/                   # Canonical Pydantic schemas, enums, and data contracts
│   ├── ai/                       # AI Provider Abstraction (OpenAI, Anthropic, Gemini, Heuristic)
│   ├── matching/                 # Multi-dimensional deterministic + semantic scoring engine
│   └── connectors/               # Pluggable opportunity feeds (HN Hiring, GitHub, RemoteTech, Manual)
├── infra/
│   ├── docker/Dockerfile.api     # Python 3.11 multi-stage Dockerfile
│   ├── docker-compose.yml        # PostgreSQL 16+pgvector, Redis 7, Temporal, API, Web
│   └── .env.example              # Documented environment variables
├── tests/
│   └── test_api_and_pipeline.py  # End-to-end integration test suite
└── docs/
    └── architecture/             # Complete architecture blueprints and schema specifications
```

---

## Architecture Documentation

- [`docs/architecture/architecture.md`](docs/architecture/architecture.md): Complete system architectural blueprint.
- [`docs/architecture/database_schema.md`](docs/architecture/database_schema.md): PostgreSQL schema & domain models.
- [`docs/architecture/workflows_and_interfaces.md`](docs/architecture/workflows_and_interfaces.md): Workflows, connectors, adapter interfaces, and security model.
