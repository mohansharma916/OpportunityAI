# OpportunityOS — Workflows, Interfaces & Security Specifications

## 1. Workflow Architecture (Temporal & Local Runner)

OpportunityOS coordinates durable long-running processes through Temporal workflows with resilient local async fallback executors:

### 1.1 Ingestion & Discovery Workflow (`DiscoverAndIngestWorkflow`)
1. **Trigger:** Search Agent timer or manual trigger.
2. **Steps:**
   - Execute registered `OpportunitySource` connectors concurrently (HN Who is Hiring, GitHub Open Source/Paid Issues, Tech RSS feeds).
   - Ingest raw items into `raw_metadata`.
   - Cluster check: Calculate URL canonical hash, company + title similarity, and semantic embedding distance.
   - If duplicate: Link to existing `opportunity_cluster_id`, update `last_seen_at`.
   - If new: Insert canonical `Opportunity` with status `DISCOVERED`.
   - Record `AUDIT_EVENT: DISCOVERED_OPPORTUNITY`.

### 1.2 Opportunity Evaluation Workflow (`EvaluateOpportunityWorkflow`)
1. **Trigger:** State change to `DISCOVERED`.
2. **Steps:**
   - Fetch active `CandidateProfile` and verified `KnowledgeItem` evidence.
   - Execute `CandidateMatcher`:
     - Deterministic checks (Country authorization, compensation floor, remote policy).
     - Multi-dimensional scoring (Technical, Experience, Timezone, Industry).
     - Calculate `overall_match_score` (0-100) and `confidence_score`.
   - Apply Decision Rules:
     - Score $\ge 88$: Transition to `STRONG_MATCH`. Trigger auto-preparation.
     - Score $75 - 87$: Transition to `PREPARED` (await approval).
     - Score $60 - 74$: Keep in review backlog.
     - Score $< 60$: Mark as `ARCHIVED` (non-destructive).
   - Record `AUDIT_EVENT: SCORED_OPPORTUNITY`.

### 1.3 Application Package Workflow (`PrepareApplicationWorkflow`)
1. **Trigger:** Opportunity marked for preparation.
2. **Steps:**
   - **Resume Variant Generation:**
     - Select relevant projects and achievements from candidate knowledge base.
     - Reorder skill priorities to match job requirements without inventing facts.
     - Produce structured resume JSON and render preview HTML.
   - **Cover Letter Generation:**
     - Formulate concise, high-signal letter tailored to the specific team, stack, and problem domain.
   - **Form Field Resolution:**
     - Match known application questions against `ApplicationAnswer` verified Q&A memory.
     - If any required question is ambiguous, legal, or unverified: Route to `NEEDS_ATTENTION` queue.
   - Set status to `NEEDS_APPROVAL` (or auto-submit if Level 4/5 configured).
   - Record `AUDIT_EVENT: APPLICATION_PREPARED`.

### 1.4 Outreach & Follow-up Cadence Workflow (`OutreachCadenceWorkflow`)
1. **Trigger:** Application approved or submitted.
2. **Steps:**
   - Execute `ContactResearcher` to discover Engineering Manager, Recruiter, or Founder.
   - Draft Step 1 Intro message.
   - Drip schedule:
     - Day 0: Initial submission confirmation.
     - Day 1: Outreach message sent (if approved).
     - Wait 4 days (Temporal durable timer).
     - Condition check: Has recipient replied? (Check inbox / CRM status).
       - If YES: Cancel remaining sequence, transition status to `RECRUITER_RESPONDED`.
       - If NO: Send polite follow-up.
     - Wait 5 days: Final check-in.
   - Record `AUDIT_EVENT: OUTREACH_SENT` / `OUTREACH_CANCELLED_ON_REPLY`.

---

## 2. Connector Interface (`packages/connectors`)

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel
from packages.domain.models import Opportunity, SearchCriteria

class RawListing(BaseModel):
    source: str
    external_id: str
    url: str
    raw_title: str
    raw_company: str
    raw_body: str
    raw_metadata: dict

class OpportunitySource(ABC):
    source_name: str
    
    @abstractmethod
    async def discover(self, criteria: SearchCriteria) -> List[RawListing]:
        """Fetch raw postings from the source."""
        pass
        
    @abstractmethod
    async def normalize(self, raw: RawListing) -> Opportunity:
        """Parse raw HTML/text into standard Opportunity model."""
        pass
        
    @abstractmethod
    async def get_application_method(self, opportunity: Opportunity) -> str:
        """Returns: EMAIL, EXTERNAL_LINK, ATS_FORM, or GITHUB_ISSUE."""
        pass
```

---

## 3. Application Adapter Interface (`packages/adapters`)

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Dict, Any

class FormField(BaseModel):
    field_name: str
    label: str
    field_type: str  # text, email, select, file, checkbox
    required: bool
    current_value: Optional[str] = None

class FormInspectionResult(BaseModel):
    url: str
    supported: bool
    fields: List[FormField]
    requires_captcha: bool
    requires_auth: bool

class ApplicationAdapter(ABC):
    adapter_name: str

    @abstractmethod
    async def can_handle(self, url: str) -> bool:
        """Determine if this adapter recognizes the ATS or site."""
        pass

    @abstractmethod
    async def inspect_form(self, page_context: Any, url: str) -> FormInspectionResult:
        """Inspect form fields and check for anti-bot or CAPTCHA challenges."""
        pass

    @abstractmethod
    async def fill_and_submit(self, page_context: Any, form_data: Dict[str, Any], resume_path: str) -> bool:
        """Safely fill verified values and submit when approved."""
        pass
```

---

## 4. AI Provider Interface (`packages/ai`)

```python
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class AIResponseMetadata(BaseModel):
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    cost_usd: float

class LLMProvider(ABC):
    provider_name: str

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> tuple[T, AIResponseMetadata]:
        """Generate structured, strictly validated Pydantic models."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> tuple[str, AIResponseMetadata]:
        """Generate unstructured text with streaming or completion."""
        pass
```

---

## 5. Security & Isolation Model

1. **Authentication:**
   - JWT tokens signed with SHA-256 for API session state.
   - HttpOnly, SameSite=Strict cookies to guard against XSS.
2. **Encrypted Vault for Integration Credentials:**
   - Sensitive credentials (e.g. SMTP password, GitHub personal token) are encrypted at rest using AES-256-GCM.
3. **Execution Sandboxing:**
   - Playwright runs in headless workers with disabled web security features restricted to target origins.
   - All network traffic from automation workers is logged with request method, target host, and response code.
4. **Data Privacy Guardrails:**
   - User profile data is never passed to public LLM training datasets.
   - Clear separation between verified candidate facts and AI-generated text.
