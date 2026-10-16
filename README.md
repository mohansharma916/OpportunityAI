# OpportunityOS

> **Remote job auto-apply + LinkedIn optimization, driven through the candidate's own browser.**
> The agent finds and fills; the candidate approves every submit.

---

## What it does

### 0. Candidate Intake (answer bank)
- Filled once: identity, job targeting, resumes, pre-approved screening answers, logged-in accounts, LinkedIn inputs.
- Every form field and profile edit is generated from it. A required question with no approved answer **pauses** the run instead of guessing.
- Passwords, cookies and tokens are never stored (they are stripped on save).

### 1. Remote jobs: discover, apply, track
- **Discovery:** platform list (user + AI added) and date-grouped opportunities.
- **Apply queue:** "Queue to Apply" adds a role to the tracker. Nothing is submitted from the API.
- **Worker (`apps/worker`):** Playwright drives your own persistent Chrome profile, so logins live in the browser, not the database. It fills forms from the answer bank with human pacing, keeps a screenshot of every run, and hands CAPTCHAs, login walls and unknown questions back to you.
- **Application tracker:** one row per application (ATS form, Easy Apply, LinkedIn post, email), de-duplicated by company + role, with status, evidence, and a follow-up date 7 days after submit.

### 2. LinkedIn
- **Profile optimizer:** reads your own profile (live, or from LinkedIn's data export), scores 12 sections
  (headline, About, experience, skills, photo, Open to Work, featured, recommendations, custom URL, banner,
  education, location) and lists what to fix. Recruiter keywords come from the jobs you've discovered.
- **Grounded drafts:** every draft is built only from your intake and work history. With `ANTHROPIC_API_KEY` set,
  Claude (`claude-opus-5-5`) polishes the headline, About and experience bullets; any number not in your facts
  is rejected and the template text is kept.
- **You approve, then it's applied:** the worker types approved headline and About changes into LinkedIn's own
  edit dialogs (dry run by default). Everything else is copy-ready text with where to paste it.
- Hiring posts can be added to the tracker ("Track in Applications"); post studio for drafting posts.
- The bulk connection bot and the credentials vault have been removed.

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

#### 2. Set up the apply worker (once, on your Mac)
```bash
uv pip install --python .venv/bin/python playwright   # uses your installed Google Chrome

# Sign in to LinkedIn and the job boards once, in the automation browser profile
PYTHONPATH=. .venv/bin/python -m apps.worker.cli login
```
Daily use:
```bash
# Fill every QUEUED application in your browser, human-paced, without submitting
PYTHONPATH=. .venv/bin/python -m apps.worker.cli queue --limit 5

# After reviewing a row marked "Awaiting approval", submit it
PYTHONPATH=. .venv/bin/python -m apps.worker.cli fill --tracker-id <id> --submit
```
LinkedIn profile:
```bash
PYTHONPATH=. .venv/bin/python -m apps.worker.cli linkedin-audit        # read, score, draft
PYTHONPATH=. .venv/bin/python -m apps.worker.cli linkedin-apply        # dry run approved headline/About
PYTHONPATH=. .venv/bin/python -m apps.worker.cli linkedin-apply --save # save them
```
Optional: `uv pip install --python .venv/bin/python anthropic` and set `ANTHROPIC_API_KEY` for Claude-polished drafts.

The browser profile and screenshots live in `~/.opportunity-os/` (override with `OPPORTUNITY_OS_HOME`).

#### 3. Launch Web Dashboard (Next.js 14)
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

| Method | Endpoint | Description |
|---|---|---|
| `GET` / `PUT` | `/api/intake` | Candidate intake (answer bank) and its completeness |
| `GET` | `/api/tracker` | Tracked applications (filter by `status`, `source_platform`, `search`) |
| `GET` | `/api/tracker/stats` | Counts by status and source, submitted today, follow-ups due, response rate |
| `POST` | `/api/tracker` | Track an application (409 if company + role is already tracked) |
| `PUT` / `DELETE` | `/api/tracker/{id}` | Update status, notes, follow-up; remove |
| `GET` / `POST` | `/api/platforms` | Platform list (no credentials) |
| `POST` | `/api/platforms/{id}/scrape`, `/api/platforms/scrape-all` | Run discovery |
| `GET` | `/api/opportunities/grouped-by-date` | Opportunities by Today, Yesterday, This Week, Earlier |
| `POST` | `/api/opportunities/{id}/human-apply` | Queue the opportunity in the tracker for the worker |
| `GET` | `/api/linkedin/optimizer` | Latest profile snapshot, audit and drafts |
| `POST` | `/api/linkedin/optimizer/import-export` | Import LinkedIn's data export, then audit |
| `POST` | `/api/linkedin/optimizer/analyze` | Re-run the audit and drafts (`?use_claude=false` for templates only) |
| `POST` | `/api/linkedin/optimizer/drafts/{id}` | `APPROVE` (optionally edited), `REJECT`, `REOPEN`, `MARK_APPLIED` |
| `GET` | `/api/linkedin/scraped-posts` | Posts, including hiring posts |
| `POST` | `/api/linkedin/posts/{id}/analyze`, `/synthesize-human-post`, `/publish` | Post studio |

---

## Running Automated Verification Tests

```bash
cd /Users/user/Documents/Projects/opportunity-os

.venv/bin/pytest tests/ -v
```

---

## Directory Architecture

```
opportunity-os/
├── apps/
│   ├── api/
│   │   ├── main.py                       # FastAPI routes
│   │   ├── models.py                     # Intake, tracker, opportunity, platform, LinkedIn models
│   │   └── services/
│   │       ├── intake_service.py         # Answer bank intake + completeness
│   │       ├── tracker_service.py        # Application tracker, de-dup, follow-ups
│   │       ├── platform_service.py       # Platform registry & discovery
│   │       ├── linkedin_optimizer_service.py # Profile snapshot, audit, drafts, approvals
│   │       ├── opportunity_service.py    # Opportunities & date grouping
│   │       └── linkedin_growth_service.py
│   ├── worker/
│   │   ├── automation.py                 # Playwright worker, guardrails, human pacing
│   │   ├── linkedin.py                   # LinkedIn profile reader & editor
│   │   └── cli.py                        # login / fill / queue / linkedin-audit / linkedin-apply
│   └── web/src/components/
│       ├── IntakeView.tsx                # Candidate intake form
│       ├── JobScraperView.tsx            # Remote jobs + apply queue
│       ├── ApplicationsTrackerView.tsx   # Application tracker
│       ├── LinkedInOptimizerView.tsx     # Profile audit + draft approvals
│       └── LinkedInGrowthAgentView.tsx   # Optimizer, hiring posts, post studio
├── packages/
│   ├── answer_bank/                      # Form field -> approved answer matching
│   ├── linkedin_optimizer/               # Export parser, audit, grounded drafts
│   ├── ai/claude_drafter.py              # Claude polish with grounding check
│   ├── matching/                         # Fit scoring
│   └── connectors/                       # Job sources
└── tests/
```
