"""
OpportunityOS — Pluggable Opportunity Connector Interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from packages.domain.models import Opportunity, SearchCriteria


class RawListing(BaseModel):
    source: str
    external_id: str
    url: str
    raw_title: str
    raw_company: str
    raw_body: str
    raw_metadata: Dict[str, Any] = {}


class OpportunitySource(ABC):
    source_name: str

    @abstractmethod
    async def discover(self, criteria: Optional[SearchCriteria] = None) -> List[RawListing]:
        """Fetch raw listings from external source."""
        pass

    @abstractmethod
    async def normalize(self, raw: RawListing) -> Opportunity:
        """Parse raw content into canonical Opportunity schema."""
        pass

    @abstractmethod
    async def get_application_method(self, opportunity: Opportunity) -> str:
        """Returns: EMAIL, EXTERNAL_LINK, ATS_FORM, or GITHUB_ISSUE."""
        pass
