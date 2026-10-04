"""
OpportunityOS — Live Web Remote Tech Opportunities Connector
Searches the web in real-time across public global engineering feeds (Arbeitnow & Jobicy)
with seamless fallback to baseline cache when offline.
"""

from __future__ import annotations
import uuid
import re
from datetime import datetime
from typing import List, Optional
import httpx

from packages.connectors.base import OpportunitySource, RawListing
from packages.domain.models import Opportunity, OpportunityType, RemoteType, PipelineStatus, SearchCriteria


class RemoteTechConnector(OpportunitySource):
    source_name: str = "LIVE_WEB_REMOTE"

    SAMPLE_JOBS = [
        {
            "id": "rt-101",
            "company": "Linear",
            "title": "Senior Product Systems Engineer (React, TypeScript)",
            "body": "Linear is looking for a senior systems engineer to build high-performance, offline-tolerant real-time collaborative interfaces. You will work on desktop and web synchronization engines using TypeScript, React, and local-first SQLite.",
            "url": "https://linear.app/careers/senior-systems-engineer",
            "skills": ["React", "TypeScript", "WebSockets", "Performance", "SQLite"],
            "salary_min": 170000,
            "salary_max": 220000,
            "type": OpportunityType.FULL_TIME,
        },
        {
            "id": "rt-102",
            "company": "Modal Labs",
            "title": "Cloud Runtime & Infrastructure Architect (Python, Rust, Docker)",
            "body": "Modal runs containerized AI workloads in the cloud with sub-second cold starts. We need engineers with deep container runtime, Linux kernel, and distributed Python experience to scale our infrastructure worldwide.",
            "url": "https://modal.com/careers/infra-architect",
            "skills": ["Python", "Docker", "Linux", "Distributed Systems", "Kubernetes"],
            "salary_min": 190000,
            "salary_max": 250000,
            "type": OpportunityType.FULL_TIME,
        },
        {
            "id": "rt-103",
            "company": "Chronosphere",
            "title": "Staff Observability & Distributed Tracing Engineer",
            "body": "Chronosphere is hiring a Staff Engineer to architect petabyte-scale telemetry ingestion pipelines. Experience with Go, Kafka, OpenTelemetry, and high-throughput databases required.",
            "url": "https://chronosphere.io/careers/staff-tracing",
            "skills": ["Go", "Kafka", "Distributed Systems", "OpenTelemetry", "PostgreSQL"],
            "salary_min": 185000,
            "salary_max": 235000,
            "type": OpportunityType.FULL_TIME,
        },
    ]

    async def discover(self, criteria: Optional[SearchCriteria] = None) -> List[RawListing]:
        results: List[RawListing] = []
        headers = {"User-Agent": "OpportunityOS-Autonomous-Agent/1.0"}

        # 1. Fetch live jobs from Arbeitnow Global API
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get("https://www.arbeitnow.com/api/job-board-api", headers=headers)
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    tech_keywords = ["engineer", "developer", "architect", "full stack", "frontend", "backend", "python", "react", "systems"]
                    for item in data:
                        title = item.get("title", "")
                        # Filter for technical roles
                        if any(kw in title.lower() for kw in tech_keywords):
                            clean_desc = re.sub(r"<[^>]+>", " ", item.get("description", ""))
                            results.append(
                                RawListing(
                                    source="ARBEITNOW_LIVE_WEB",
                                    external_id=str(item.get("slug") or uuid.uuid4())[:20],
                                    url=item.get("url") or "https://arbeitnow.com",
                                    raw_title=title,
                                    raw_company=item.get("company_name", "Global Tech Company"),
                                    raw_body=clean_desc[:1200],
                                    raw_metadata={
                                        "tags": item.get("tags", []),
                                        "location": item.get("location", "Remote"),
                                        "remote": item.get("remote", True),
                                        "job_types": item.get("job_types", []),
                                    },
                                )
                            )
                        if len(results) >= 8:
                            break
        except Exception:
            pass

        # 2. Fetch live engineering jobs from Jobicy API
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res2 = await client.get("https://jobicy.com/api/v2/remote-jobs?count=15&industry=engineering", headers=headers)
                if res2.status_code == 200:
                    jobs = res2.json().get("jobs", [])
                    for j in jobs:
                        clean_desc = re.sub(r"<[^>]+>", " ", j.get("jobDescription", "") or j.get("jobExcerpt", ""))
                        results.append(
                            RawListing(
                                source="JOBICY_LIVE_WEB",
                                external_id=str(j.get("id") or uuid.uuid4())[:20],
                                url=j.get("url") or "https://jobicy.com",
                                raw_title=j.get("jobTitle", "Remote Software Engineer"),
                                raw_company=j.get("companyName", "Tech Employer"),
                                raw_body=clean_desc[:1200],
                                raw_metadata={
                                    "salary_min": j.get("annualSalaryMin"),
                                    "salary_max": j.get("annualSalaryMax"),
                                    "currency": j.get("salaryCurrency", "USD"),
                                    "geo": j.get("jobGeo", "Worldwide"),
                                    "type": j.get("jobType", ["Full-Time"]),
                                },
                            )
                        )
                        if len(results) >= 15:
                            break
        except Exception:
            pass

        # If live web returned listings, return them!
        if results:
            return results

        # Fallback to curated samples if completely offline
        for sample in self.SAMPLE_JOBS:
            results.append(
                RawListing(
                    source=self.source_name,
                    external_id=sample["id"],
                    url=sample["url"],
                    raw_title=sample["title"],
                    raw_company=sample["company"],
                    raw_body=sample["body"],
                    raw_metadata=sample,
                )
            )
        return results

    async def normalize(self, raw: RawListing) -> Opportunity:
        meta = raw.raw_metadata

        # Extract salary if provided or parse from text
        salary_min = meta.get("salary_min")
        salary_max = meta.get("salary_max")
        hourly_rate = meta.get("hourly_rate")

        body = raw.raw_body
        if not salary_min and not hourly_rate:
            annual_match = re.search(r"\$(\d{2,3})k?\s*(?:-|to)?\s*\$?(\d{2,3})k?", body, re.IGNORECASE)
            if annual_match:
                v1 = float(annual_match.group(1)) * (1000 if float(annual_match.group(1)) < 1000 else 1)
                v2 = float(annual_match.group(2)) * (1000 if float(annual_match.group(2)) < 1000 else 1) if annual_match.group(2) else v1
                salary_min = min(v1, v2)
                salary_max = max(v1, v2)

        # Detect technical skills mentioned
        known_techs = [
            "React", "TypeScript", "Python", "FastAPI", "Next.js", "Node.js", "PostgreSQL",
            "Redis", "Docker", "Kubernetes", "AWS", "GCP", "GraphQL", "Tailwind",
            "Go", "Rust", "Vue", "Playwright", "Distributed Systems", "SQL"
        ]
        detected = [t for t in known_techs if re.search(r"\b" + re.escape(t) + r"\b", body + " " + raw.raw_title, re.IGNORECASE)]
        if not detected:
            detected = meta.get("tags", [])[:5] or ["Software Engineering"]

        location = meta.get("geo") or meta.get("location") or "Remote Worldwide"

        return Opportunity(
            id=str(uuid.uuid4()),
            source=raw.source,
            external_id=raw.external_id,
            url=raw.url,
            company_name=raw.raw_company,
            company_domain=f"{raw.raw_company.lower().replace(' ', '').replace(',', '')}.com",
            title=raw.raw_title,
            description=raw.raw_body,
            location=location,
            remote_type=RemoteType.REMOTE,
            country="Worldwide",
            employment_type=OpportunityType.FULL_TIME,
            salary_min=salary_min,
            salary_max=salary_max,
            hourly_rate=hourly_rate,
            salary_currency="USD",
            required_skills=detected,
            preferred_skills=["Distributed Systems", "Testing", "CI/CD"],
            experience_required_years=4.0,
            status=PipelineStatus.DISCOVERED,
            date_posted=datetime.utcnow(),
            raw_metadata=meta,
            created_at=datetime.utcnow(),
        )

    async def get_application_method(self, opportunity: Opportunity) -> str:
        return "EXTERNAL_LINK"
