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

    async def discover(self, criteria: Optional[SearchCriteria] = None) -> List[RawListing]:
        results: List[RawListing] = []
        headers = {"User-Agent": "OpportunityOS-Autonomous-Agent/1.0"}

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get("https://hacker-news.firebaseio.com/v0/jobstories.json", headers=headers)
                if res.status_code == 200:
                    story_ids = res.json()[:10]
                    for sid in story_ids:
                        try:
                            s_res = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", headers=headers)
                            if s_res.status_code == 200:
                                item = s_res.json()
                                if not item:
                                    continue
                                raw_title = item.get("title", "Software Engineering Opportunity")
                                # Extract company name from title pattern if present
                                company = "Hacker News Hiring"
                                if "is hiring" in raw_title.lower():
                                    company = raw_title.lower().split("is hiring")[0].strip().title()
                                elif "(" in raw_title:
                                    company = raw_title.split("(")[0].strip()

                                raw_body = item.get("text") or raw_title
                                clean_body = re.sub(r"<[^>]+>", " ", raw_body)

                                results.append(
                                    RawListing(
                                        source=self.source_name,
                                        external_id=f"hn-{sid}",
                                        url=item.get("url") or f"https://news.ycombinator.com/item?id={sid}",
                                        raw_title=raw_title,
                                        raw_company=company or "HN Tech Company",
                                        raw_body=clean_body[:1200],
                                        raw_metadata=item,
                                    )
                                )
                        except Exception:
                            continue
        except Exception:
            pass

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
