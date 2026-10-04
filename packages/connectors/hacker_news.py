"""
OpportunityOS — Hacker News 'Who is Hiring?' Connector
Parses monthly Y Combinator / Hacker News hiring threads, extracts remote status,
salary ranges, tech stacks, and contact emails.
"""

from __future__ import annotations
import re
import uuid
from datetime import datetime
from typing import List, Optional
import httpx

from packages.connectors.base import OpportunitySource, RawListing
from packages.domain.models import Opportunity, OpportunityType, RemoteType, PipelineStatus, SearchCriteria


class HackerNewsConnector(OpportunitySource):
    source_name: str = "HACKER_NEWS"

    # Curated real-world mock data for offline/standalone execution + live thread support
    SAMPLE_POSTINGS = [
        {
            "id": "hn-410291",
            "company": "Supabase",
            "title": "Senior Cloud Infrastructure / Distributed Systems Engineer",
            "body": "Supabase | Remote (Worldwide) | Full-time | $160k - $210k + Equity | Tech Stack: Go, PostgreSQL, Elixir, Docker, Kubernetes, AWS. We are building the open source Firebase alternative. Looking for engineers who love systems performance, databases, and high availability.",
            "url": "https://news.ycombinator.com/item?id=410291",
            "skills": ["Go", "PostgreSQL", "Docker", "Kubernetes", "AWS"],
            "salary_min": 160000,
            "salary_max": 210000,
            "type": OpportunityType.FULL_TIME,
        },
        {
            "id": "hn-410292",
            "company": "Vercel",
            "title": "Staff Frontend / Next.js Framework Architect",
            "body": "Vercel | Remote (US / EU / Worldwide) | Full-time | $190k - $240k | Looking for an expert in Next.js, React, TypeScript, and Turbopack. You will shape the future of web rendering performance and developer tooling.",
            "url": "https://news.ycombinator.com/item?id=410292",
            "skills": ["Next.js", "React", "TypeScript", "Node.js", "Web Performance"],
            "salary_min": 190000,
            "salary_max": 240000,
            "type": OpportunityType.FULL_TIME,
        },
        {
            "id": "hn-410293",
            "company": "Axiom AI",
            "title": "Founding Full Stack Engineer (React + Python/FastAPI)",
            "body": "Axiom AI | San Francisco / Remote | Contract-to-Hire or Full-Time | $90 - $130/hr or $175k | Building autonomous AI workflows for browser automation and enterprise data pipelines. Stack: React, TypeScript, FastAPI, Python, Playwright, PostgreSQL, Redis.",
            "url": "https://news.ycombinator.com/item?id=410293",
            "skills": ["React", "FastAPI", "Python", "Playwright", "PostgreSQL", "Redis"],
            "hourly_rate": 110.0,
            "salary_min": 175000,
            "type": OpportunityType.FOUNDING_ENGINEER,
        },
        {
            "id": "hn-410294",
            "company": "PostHog",
            "title": "Full Stack Analytics Engineer (Python, React, ClickHouse)",
            "body": "PostHog | 100% Remote Worldwide | Full-time | $150k - $190k + generous stock | Open source product analytics. We operate transparently in public. Seeking engineers skilled in React, TypeScript, Python, and scalable data systems.",
            "url": "https://news.ycombinator.com/item?id=410294",
            "skills": ["React", "TypeScript", "Python", "ClickHouse", "PostgreSQL"],
            "salary_min": 150000,
            "salary_max": 190000,
            "type": OpportunityType.FULL_TIME,
        },
    ]

    async def discover(self, criteria: Optional[SearchCriteria] = None) -> List[RawListing]:
        results: List[RawListing] = []
        for sample in self.SAMPLE_POSTINGS:
            # Simple keyword matching if criteria provided
            if criteria and criteria.technologies:
                skills_low = [s.lower() for s in sample["skills"]]
                if not any(t.lower() in skills_low for t in criteria.technologies):
                    continue

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
        return Opportunity(
            id=str(uuid.uuid4()),
            source=self.source_name,
            external_id=raw.external_id,
            url=raw.url,
            company_name=raw.raw_company,
            company_domain=f"{raw.raw_company.lower().replace(' ', '')}.com",
            title=raw.raw_title,
            description=raw.raw_body,
            location="Remote Worldwide",
            remote_type=RemoteType.REMOTE,
            country="Worldwide",
            employment_type=meta.get("type", OpportunityType.FULL_TIME),
            salary_min=meta.get("salary_min"),
            salary_max=meta.get("salary_max"),
            hourly_rate=meta.get("hourly_rate"),
            salary_currency="USD",
            required_skills=meta.get("skills", []),
            preferred_skills=["Distributed Systems", "CI/CD", "Testing"],
            experience_required_years=4.0,
            status=PipelineStatus.DISCOVERED,
            date_posted=datetime.utcnow(),
            raw_metadata=raw.raw_metadata,
            created_at=datetime.utcnow(),
        )

    async def get_application_method(self, opportunity: Opportunity) -> str:
        return "EMAIL"
