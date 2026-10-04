from packages.adapters.base import (
    ApplicationAdapter,
    InspectionResult,
    SubmissionResult,
    FormField,
)
from packages.adapters.email_adapter import EmailApplicationAdapter
from packages.adapters.ats_form_adapter import ATSFormApplicationAdapter
from packages.adapters.github_pr_adapter import GitHubContributionAdapter

__all__ = [
    "ApplicationAdapter",
    "InspectionResult",
    "SubmissionResult",
    "FormField",
    "EmailApplicationAdapter",
    "ATSFormApplicationAdapter",
    "GitHubContributionAdapter",
]
