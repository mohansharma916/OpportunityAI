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
- **Discovery:** official public feeds only. Job boards: We Work Remotely, Remote OK, Himalayas, Remotive, Jobicy.
  Company job boards: 68 verified Greenhouse / Lever / Ashby boards (`packages/connectors/remote_companies.json`),
  plus any board URL you add. LinkedIn hiring posts are searched in your browser by the worker.
- **Filters and score:** remote and open to your country, salary floor, excluded companies, posted within 14 days
  (60 on company pages), title matches your targets. Score 0-100 = skills 40, title & seniority 25, salary 15,
  employer 10, freshness 10. 70+ goes to the apply queue (up to your daily cap), 50-69 to a "maybe" list.
- **Apply queue:** "Queue to Apply" adds a role to the tracker. Nothing is submitted from the API.
- **Worker (`apps/worker`):** Playwright drives your own persistent Chrome profile, so logins live in the browser, not the database. It fills forms from the answer bank with human pacing, keeps a screenshot of every run, and hands CAPTCHAs, login walls and unknown questions back to you.
- **ATS adapters:** Greenhouse and Lever (field ids/names, dropdown comboboxes, file inputs, confirmation pages), built from their live forms; Ashby and other sites use label matching.
- **Approve, then submit:** a fill pauses on questions it has no answer for (Claude suggests answers from your facts when `ANTHROPIC_API_KEY` is set). Your answers are saved to the answer bank and reused. You review the filled fields and screenshot in Applications and approve; the worker re-fills and submits only if the answers still match what you approved. A CAPTCHA on submit waits in the open window for you to solve.
- **Trusted auto-submit (opt-in):** after 20 approvals on one ATS needed no changes, queued applications there can submit without review.
- **Follow-ups:** due 7 days after submitting, with a drafted message; after 2 follow-ups it suggests marking the role ghosted.
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
# Fill queued applications, submit the ones you approved, list follow-ups
PYTHONPATH=. .venv/bin/python -m apps.worker.cli run

# Or step by step
PYTHONPATH=. .venv/bin/python -m apps.worker.cli queue          # fill (dry run)
PYTHONPATH=. .venv/bin/python -m apps.worker.cli submit         # submit approved, within the daily cap
PYTHONPATH=. .venv/bin/python -m apps.worker.cli inspect URL    # what a form would get; types nothing
```
Discovery (run twice a day, e.g. from cron or launchd):
```bash
PYTHONPATH=. .venv/bin/python -m apps.worker.cli discover          # job boards + company boards that are due
PYTHONPATH=. .venv/bin/python -m apps.worker.cli linkedin-posts    # LinkedIn hiring posts (max 2 runs a day)
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
| `POST` | `/api/tracker/{id}/answers` | Answer open questions (saved to the answer bank; row is re-filled) |
| `POST` | `/api/tracker/{id}/approve` | Approve a filled application for submission |
| `GET` | `/api/tracker/{id}/evidence/{n}` | Screenshot of a worker run |
| `GET` / `POST` | `/api/tracker/follow-ups`, `/api/tracker/{id}/follow-up` | Follow-ups due (with a drafted message); mark one done |
| `GET` / `POST` | `/api/platforms` | Sources; adding one accepts Greenhouse / Lever / Ashby / supported board URLs |
| `POST` | `/api/platforms/{id}/scrape` | Search one source now |
| `POST` | `/api/discovery/run` | Search every source that is due (`?force=true` for all) |
| `GET` | `/api/opportunities?status=MATCH` | Discovered roles: `MATCH`, `MAYBE`, `QUEUED`, `DISMISSED` |
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
│   │       ├── platform_service.py       # Sources: job boards + verified company boards
│   │       ├── discovery_service.py      # Fetch, filter, score, queue
│   │       ├── linkedin_optimizer_service.py # Profile snapshot, audit, drafts, approvals
│   │       ├── opportunity_service.py    # Opportunities & date grouping
│   │       └── linkedin_growth_service.py
│   ├── worker/
│   │   ├── automation.py                 # Playwright worker, guardrails, human pacing
│   │   ├── adapters.py                   # Greenhouse / Lever / Ashby form knowledge
│   │   ├── apply_runner.py               # One tracker row: fill, approve-gate, submit
│   │   ├── linkedin.py                   # LinkedIn profile reader & editor
│   │   └── cli.py                        # login / fill / queue / linkedin-audit / linkedin-apply
│   └── web/src/components/
│       ├── IntakeView.tsx                # Candidate intake form
│       ├── JobsView.tsx                  # Matches / maybe / queued + sources
│       ├── ApplicationsTrackerView.tsx   # Application tracker
│       ├── LinkedInOptimizerView.tsx     # Profile audit + draft approvals
│       └── LinkedInGrowthAgentView.tsx   # Optimizer, hiring posts, post studio
├── packages/
│   ├── answer_bank/                      # Form field -> approved answer matching
│   ├── linkedin_optimizer/               # Export parser, audit, grounded drafts
│   ├── ai/claude_drafter.py              # Claude polish with grounding check
│   ├── ai/claude_answers.py              # Claude suggestions for open form questions
│   ├── matching/discovery.py             # Eligibility filters + 0-100 score
│   └── connectors/                       # job_feeds.py (APIs/RSS), linkedin_posts.py, company list
└── tests/
```
