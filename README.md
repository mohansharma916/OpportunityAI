# OpportunityOS

> **Autonomous Career & Opportunity Intelligence Platform**
> Streamlined to 3 Core Pillars: Multi-Platform Job Scraper with Human-like Auto-Apply, LinkedIn Scraper & Automation Bot, and Automated Outreach & Networking CRM.

---

## The 3 Core Pillars

### 1. Job / Project Web Scraper Tool & Human-Like Auto-Apply
- **Platform List Maintenance**:
  - **User-Managed**: Add any custom job board, contract platform, or career portal with custom URLs, categories, and account credentials (User ID / Password / Auth Keys).
  - **AI Discovery**: The AI scans and automatically discovers new platforms (e.g. Arbeitnow, Jobicy, GitHub Bounties, Hacker News, Wellfound, RemoteOK, Toptal) and adds them to your active registry.
- **Multi-Platform Scraping Engine**:
  - Executes live scraping across registered platforms to discover full-time roles, contracts ($/hr), and paid bounties.
- **Date-Grouped Opportunity Tracking**:
  - Automatically groups discovered opportunities into **Today**, **Yesterday**, **This Week**, and **Earlier** with live counters.
- **User-Maintained Status Pipeline**:
  - Direct status toggling on every opportunity: `Discovered` → `Reviewing` → `Applied` → `Interviewing` → `Offer` → `Rejected` → `Archived`.
- **Human-Like Browser Automation (`Apply on Behalf of User`)**:
  - Applies to positions using user credentials (username/password/API tokens) saved in the vault or provided on-demand.
  - Simulates authentic human behavior: variable keystroke typing delays (50–120ms), cursor pauses, randomized review intervals (1.2–2.5s), and structured form completion.

---

### 2. LinkedIn Scraper & Automation Bot
- **Multi-Type LinkedIn Scraper**:
  - **Hiring in Posts**: Extracts founders and engineering managers actively hiring directly in posts (roles, compensation, direct apply instructions).
  - **Freelance & Contracts**: Scrapes short-term sprints, contract architecture needs, hourly rates ($/hr), and fixed budgets.
  - **Project Collaboration**: Discovers open-source maintainers and founders looking for co-builders, collaborators, and technical partners.
  - **Interesting Tech Posts**: Extracts high-engagement technical breakdowns, systems design debates, and architecture takeaways.
  - **Full Connection / Author Metadata**: Extracts author name, profile URL, connection degree (1st/2nd/3rd), company, headline, post text, and engagement metrics (likes, comments, reposts).
- **LinkedIn Post Studio — Human Voice Synthesizer**:
  - **Post Dynamics Analyzer**: Analyzes scraped posts from previous steps to decode the **hook technique**, **tone & voice**, and **core debate points**.
  - **Human Post Synthesizer ("Make it humanly")**: Generates authentic, non-generic related posts using real production lessons, nuanced counter-perspectives, actionable checklists, or proof-of-work pitches. Eliminates robotic AI cliches, enforces organic 1-2 sentence spacing, and ends with peer-level debate questions.
  - **Tracked Inspiration Library**: Tracks all analyzed posts, linked drafts, and publishing statuses.
- **Selenium-Style Connection Automation**:
  - Automates outreach and connection requests with human-paced execution.
  - Staggered scrolling, organic delays between actions (800ms–2200ms), and custom personalized invitation notes.
- **Encrypted Credentials Vault**:
  - Securely stores LinkedIn credentials, session cookies (`li_at`), and 2FA tokens.

---

### 3. Automated Outreach & Networking CRM
- **Recruiter & Contact Directory**:
  - Centralized contact management for recruiters, hiring managers, and founders.
- **3-Step Automated Recruiter Drip Cadences**:
  - **Step 1 (Day 1)**: Personalized Introduction & Alignment Note.
  - **Step 2 (Day 4)**: Value-Add Follow-Up (Relevant GitHub projects, architecture case studies).
  - **Step 3 (Day 9)**: Final Professional Check-In & Graceful Closure.
- **Cadence Advancement Engine**:
  - Advances sequences step-by-step with logged audit timestamps and message tracking.
- **AI Personalized Note Composer**:
  - Generates tailored outreach messages referencing the candidate's verified skills and work accomplishments without hallucinating facts.

---

## Quick Start Guide

### Prerequisites
- **Python 3.11+**
- **Node.js 20+** and **npm** / **pnpm**
- **Docker** (optional, for PostgreSQL, Redis, and Temporal)

---

### Local Development Setup

#### 1. Launch Backend API (FastAPI)
```bash
cd /Users/user/Documents/Projects/opportunity-os

# Activate virtual environment
source .venv/bin/activate

# Start the FastAPI server (Port 8000)
PYTHONPATH=. uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```
- **API Base:** `http://localhost:8000`
- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

#### 2. Launch Web Dashboard (Next.js 14)
```bash
cd /Users/user/Documents/Projects/opportunity-os/apps/web

# Install dependencies
npm install

# Start Next.js dev server (Port 3000)
npm run dev
```
- **Web App:** [http://localhost:3000](http://localhost:3000)

---

## REST API Endpoints Overview

### Pillar 1: Platform & Opportunity Scraper
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/platforms` | List registered platforms (seeded + user + AI added) |
| `POST` | `/api/platforms` | Register a new platform with login credentials |
| `POST` | `/api/platforms/discover` | AI platform discovery engine |
| `POST` | `/api/platforms/{id}/scrape` | Scrape a specific platform |
| `POST` | `/api/platforms/scrape-all` | Execute multi-platform crawl |
| `GET` | `/api/opportunities/grouped-by-date` | Opportunities categorized by Today, Yesterday, This Week, Earlier |
| `POST` | `/api/opportunities/{id}/status` | Update tracking status (`Reviewing`, `Applied`, `Interviewing`, etc.) |
| `POST` | `/api/opportunities/{id}/human-apply` | Human-like browser automation apply with credentials |

### Pillar 2: LinkedIn Growth Agent
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/linkedin/scrape` | Scrape LinkedIn opportunities and creator posts |
| `POST` | `/api/linkedin/connect-automate` | Selenium-style human connection automation |
| `POST` | `/api/linkedin/publish` | Publish post to LinkedIn profile |
| `GET` | `/api/linkedin/credentials` | Check configured credentials status |
| `POST` | `/api/linkedin/credentials` | Save LinkedIn credentials to secure vault |

### Pillar 3: Outreach & Networking CRM
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/crm/contacts` | List recruiter & hiring manager contacts |
| `POST` | `/api/crm/contacts` | Add a hiring contact |
| `GET` | `/api/crm/sequences` | List active 3-step outreach cadences |
| `POST` | `/api/crm/sequences` | Initialize 3-step cadence for a contact |
| `POST` | `/api/crm/sequences/{id}/advance` | Dispatch next step in cadence |
| `POST` | `/api/crm/generate-message` | AI generate tailored outreach note |

---

## Running Automated Verification Tests

```bash
cd /Users/user/Documents/Projects/opportunity-os

# Run the 3 core features test suite:
.venv/bin/pytest tests/test_three_core_features.py -v

# Run full project test suite (10 tests, 100% passing):
.venv/bin/pytest tests/ -v
```

---

## Directory Architecture

```
opportunity-os/
├── apps/
│   ├── api/
│   │   ├── main.py                     # FastAPI routes for Scrapers, LinkedIn Bot & CRM
│   │   ├── models.py                   # Platform, Credential, Opportunity & CRM models
│   │   └── services/
│   │       ├── platform_service.py     # Multi-platform registry, AI discovery & scrapers
│   │       ├── opportunity_service.py  # Date grouping & human-like auto-apply engine
│   │       ├── linkedin_growth_service.py # LinkedIn scraper & Selenium human automation
│   │       └── crm_service.py          # 3-step recruiter cadences & note generation
│   └── web/
│       └── src/
│           ├── app/page.tsx            # Main layout hosting the 3 pillars
│           └── components/
│               ├── Navigation.tsx      # Sidebar navigation for the 3 core features
│               ├── JobScraperView.tsx  # Pillar 1: Platforms, Date Groups, Human Apply
│               ├── LinkedInGrowthAgentView.tsx # Pillar 2: LinkedIn Scraper, Bot, Vault
│               └── CRMView.tsx         # Pillar 3: Recruiter Directory & 3-Step Drip CRM
├── packages/
│   ├── domain/                         # Core schemas & data models
│   ├── matching/                       # Multi-dimensional fit scoring engine
│   └── connectors/                     # Feeds & scrapers
└── tests/
    ├── test_three_core_features.py     # Dedicated suite for all 3 features
    └── ...                             # Full integration suites (10 passed)
```
