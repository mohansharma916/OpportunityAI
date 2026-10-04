"""
OpportunityOS — Live GitHub Open-Source & Paid Bounty Connector
Searches the live web on GitHub for open issues, feature requests, and bounties matching candidate skills.
"""

from __future__ import annotations
import uuid
import re
from datetime import datetime
from typing import List, Optional
import httpx

from packages.connectors.base import OpportunitySource, RawListing
from packages.domain.models import Opportunity, OpportunityType, RemoteType, PipelineStatus, SearchCriteria


class GitHubContributionConnector(OpportunitySource):
    source_name: str = "GITHUB_LIVE_CONTRIBUTIONS"



    async def discover(self, criteria: Optional[SearchCriteria] = None) -> List[RawListing]:
        results: List[RawListing] = []
        headers = {"User-Agent": "OpportunityOS-Agent/1.0"}

        # Live web search on GitHub
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                query = 'label:"good first issue",help-wanted state:open language:typescript language:python'
                url = f"https://api.github.com/search/issues?q={query}&sort=updated&order=desc&per_page=10"
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    items = res.json().get("items", [])
                    for item in items:
                        repo_name = item.get("repository_url", "").replace("https://api.github.com/repos/", "")
                        body = (item.get("body") or "")[:800]
                        results.append(
                            RawListing(
                                source="GITHUB_LIVE_WEB",
                                external_id=str(item.get("id"))[:20],
                                url=item.get("html_url") or "https://github.com",
                                raw_title=item.get("title", "Open Source Issue"),
                                raw_company=repo_name or "Open Source Repository",
                                raw_body=body,
                                raw_metadata={
                                    "repo": repo_name,
                                    "labels": [lbl.get("name") for lbl in item.get("labels", [])],
                                    "comments_count": item.get("comments", 0),
                                    "author": item.get("user", {}).get("login"),
                                },
                            )
                        )
                        if len(results) >= 8:
                            break
        except Exception:
            pass

        return results

    async def normalize(self, raw: RawListing) -> Opportunity:
        meta = raw.raw_metadata
        labels = [l.lower() for l in meta.get("labels", [])]

        # Check for bounty labels
        bounty = None
        for lbl in labels:
            b_match = re.search(r"\$(\d+)", lbl)
            if b_match:
                bounty = float(b_match.group(1))
                break

        # Detect tech stack
        detected = ["Git", "GitHub"]
        body_lower = (raw.raw_body + " " + raw.raw_title).lower()
        if "python" in body_lower or "fastapi" in body_lower or "django" in body_lower:
            detected.append("Python")
        if "react" in body_lower or "next" in body_lower:
            detected.append("React")
        if "typescript" in body_lower or "javascript" in body_lower:
            detected.append("TypeScript")

        opp_type = OpportunityType.PAID_OPEN_SOURCE if bounty else OpportunityType.OPEN_SOURCE

        return Opportunity(
            id=str(uuid.uuid4()),
            source=raw.source,
            external_id=raw.external_id,
            url=raw.url,
            company_name=raw.raw_company,
            company_domain="github.com",
            title=raw.raw_title,
            description=raw.raw_body,
            location="Worldwide Open Source",
            remote_type=RemoteType.REMOTE,
            country="Worldwide",
            employment_type=opp_type,
            hourly_rate=bounty,
            salary_currency="USD",
            required_skills=detected,
            preferred_skills=["Open Source Etiquette", "CI/CD", "Pull Requests"],
            experience_required_years=2.0,
            status=PipelineStatus.DISCOVERED,
            date_posted=datetime.utcnow(),
            raw_metadata=raw.raw_metadata,
            created_at=datetime.utcnow(),
        )

    async def get_application_method(self, opportunity: Opportunity) -> str:
        return "GITHUB_ISSUE"
