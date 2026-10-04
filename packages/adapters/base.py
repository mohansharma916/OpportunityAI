"""
OpportunityOS — Application Adapter Interface
Pluggable adapters for different destination formats (Email, ATS forms, GitHub Issues, etc.)
with strict safety circuit breakers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class FormField(BaseModel):
    field_name: str
    label: str
    field_type: str  # text, email, select, file, checkbox, textarea
    required: bool
    current_value: Optional[str] = None


class InspectionResult(BaseModel):
    url: str
    supported: bool
    fields: List[FormField] = []
    requires_captcha: bool = False
    requires_security_challenge: bool = False
    unknown_questions: List[str] = []
    can_auto_submit: bool = True
    reason: Optional[str] = None


class SubmissionResult(BaseModel):
    success: bool
    status: str  # SUBMITTED, REQUIRES_HUMAN_ATTENTION, FAILED
    step_reached: str
    confirmation_reference: Optional[str] = None
    circuit_breaker_triggered: bool = False
    reason: str
    fields_filled: Dict[str, Any] = {}


class ApplicationAdapter(ABC):
    adapter_name: str

    @abstractmethod
    async def can_handle(self, url: str, method: str) -> bool:
        """Determine if this adapter recognizes the destination format."""
        pass

    @abstractmethod
    async def inspect(self, url: str, opportunity: Any) -> InspectionResult:
        """Inspect destination form/endpoint for challenges or unknown questions."""
        pass

    @abstractmethod
    async def submit(
        self,
        opportunity: Any,
        candidate_profile: Any,
        resume_variant: Any,
        cover_letter: Any,
        verified_answers: List[Any],
    ) -> SubmissionResult:
        """Safely fill verified values and submit."""
        pass
