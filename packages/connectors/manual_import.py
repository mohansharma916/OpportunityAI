"""
OpportunityOS — Manual / Universal Import Connector
Allows immediate ingestion and normalization of arbitrary pasted job descriptions,
recruiter emails, or job board URLs.
"""

from __future__ import annotations
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any

from packages.connectors.base import OpportunitySource, RawListing
from packages.domain.models import (
    Opportunity,
    OpportunityType,
    RemoteType,
    PipelineStatus,
    SearchCriteria,
)


class ManualImportConnector(OpportunitySource):
    source_name: str = "MANUAL_IMPORT"

    async def discover(self, criteria: Optional[SearchCriteria] = None) -> List[RawListing]:
        return []

    async def normalize(self, raw: RawListing) -> Opportunity:
        body = raw.raw_body
        title = raw.raw_title
        company = raw.raw_company

        # If title or company missing, heuristically extract from body
        if not company or company == "Unknown":
            comp_match = re.search(r"(?:at|@|for|join)\s+([A-Z][A-Za-z0-9\s]{2,25})", body)
            company = comp_match.group(1).strip() if comp_match else "Target Company"

        if not title or title == "Pasted Role":
            role_match = re.search(
                r"(Senior|Staff|Lead|Principal|Full Stack|Frontend|Backend|DevOps|Platform|Founding)\s+([A-Za-z\s/]{3,35})(?:Engineer|Developer|Architect|Lead)",
                body,
                re.IGNORECASE,
            )
            title = role_match.group(0).strip() if role_match else "Software Engineer"

        # Extract salary/rate if present
        salary_min = None
        salary_max = None
        hourly_rate = None

        hourly_match = re.search(r"\$(\d{2,3})\s*(?:-|to)?\s*\$?(\d{2,3})?\s*(?:/hr|per hour|hr)", body, re.IGNORECASE)
        if hourly_match:
            hourly_rate = float(hourly_match.group(2) or hourly_match.group(1))

        annual_match = re.search(r"\$(\d{2,3})k?\s*(?:-|to)?\s*\$?(\d{2,3})k?", body, re.IGNORECASE)
        if annual_match and not hourly_rate:
            v1 = float(annual_match.group(1))
            v2 = float(annual_match.group(2)) if annual_match.group(2) else v1
            if v1 < 1000:
                v1 *= 1000
            if v2 < 1000:
                v2 *= 1000
            salary_min = min(v1, v2)
            salary_max = max(v1, v2)

        # Detect tech skills mentioned in body
        known_techs = [
            "React", "TypeScript", "Python", "FastAPI", "Next.js", "Node.js", "PostgreSQL",
            "Redis", "Docker", "Kubernetes", "AWS", "GCP", "GraphQL", "Tailwind",
            "Go", "Rust", "Vue", "Playwright", "Temporal"
        ]
        detected_skills = [tech for tech in known_techs if re.search(r"\b" + re.escape(tech) + r"\b", body, re.IGNORECASE)]
        if not detected_skills:
            detected_skills = ["Software Engineering", "Full Stack"]

        # Detect remote status
        remote_type = RemoteType.REMOTE
        if "hybrid" in body.lower():
            remote_type = RemoteType.HYBRID
        elif "onsite" in body.lower() or "in-office" in body.lower():
            remote_type = RemoteType.ONSITE

        # Detect employment type
        emp_type = OpportunityType.FULL_TIME
        if "contract" in body.lower() or hourly_rate:
            emp_type = OpportunityType.CONTRACT
        elif "freelance" in body.lower():
            emp_type = OpportunityType.FREELANCE
        elif "founding" in body.lower():
            emp_type = OpportunityType.FOUNDING_ENGINEER
        elif "part-time" in body.lower():
            emp_type = OpportunityType.PART_TIME

        return Opportunity(
            id=str(uuid.uuid4()),
            source=self.source_name,
            external_id=raw.external_id or str(uuid.uuid4())[:8],
            url=raw.url or "https://manual-import.local",
            company_name=company,
            company_domain=f"{company.lower().replace(' ', '')}.com",
            title=title,
            description=body,
            location="Remote" if remote_type == RemoteType.REMOTE else "Hybrid / Specified",
            remote_type=remote_type,
            country="Worldwide",
            employment_type=emp_type,
            salary_min=salary_min,
            salary_max=salary_max,
            hourly_rate=hourly_rate,
            salary_currency="USD",
            required_skills=detected_skills,
            preferred_skills=["Distributed Systems", "Testing"],
            experience_required_years=4.0,
            status=PipelineStatus.DISCOVERED,
            date_posted=datetime.utcnow(),
            raw_metadata=raw.raw_metadata,
            created_at=datetime.utcnow(),
        )

    async def get_application_method(self, opportunity: Opportunity) -> str:
        return "EXTERNAL_LINK"
