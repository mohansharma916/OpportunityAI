"""
OpportunityOS — Multi-Dimensional Matching Engine
Combines deterministic constraint satisfaction with semantic transferable skill recognition.
"""

from __future__ import annotations
from typing import Dict, List, Tuple
from packages.domain.models import (
    CandidateProfile,
    Opportunity,
    MatchingScore,
    RemoteType,
)

# Known transferable skill equivalences
TRANSFERABLE_MAP: Dict[str, List[str]] = {
    "fastapi": ["flask", "django", "express", "nestjs", "gin", "actix-web"],
    "react": ["vue", "svelte", "next.js", "preact", "angular"],
    "next.js": ["react", "remix", "nuxt", "sveltekit", "astro"],
    "typescript": ["javascript", "flow"],
    "postgresql": ["mysql", "mariadb", "sqlite", "cockroachdb"],
    "redis": ["memcached", "keydb", "dragonfly"],
    "docker": ["podman", "containerd", "kubernetes"],
    "kubernetes": ["docker swarm", "nomad", "ecs", "helm"],
    "aws": ["gcp", "google cloud", "azure", "cloudflare"],
    "gcp": ["aws", "azure", "google cloud"],
    "graphql": ["rest", "trpc", "grpc"],
    "playwright": ["puppeteer", "cypress", "selenium"],
    "tailwind": ["css", "vanilla css", "styled-components", "sass"],
    "react native": ["flutter", "swift", "kotlin", "ios", "android"],
}


class MatchingEngine:
    def __init__(self):
        pass

    def evaluate(self, profile: Optional[CandidateProfile], opportunity: Opportunity) -> MatchingScore:
        """
        Evaluate candidate fit across technical, seniority, remote, timezone,
        and compensation dimensions.
        """
        if not profile:
            return MatchingScore(
                opportunity_id=opportunity.id,
                overall_match_score=50.0,
                confidence_score=50.0,
                technical_match=50.0,
                experience_match=50.0,
                remote_match=50.0,
                timezone_match=50.0,
                compensation_match=50.0,
                industry_match=50.0,
                role_match=50.0,
                transferable_skills={},
                primary_strengths=["Foundational technical alignment"],
                primary_gaps=[],
                match_rationale="Candidate profile pending onboarding verification.",
            )

        tech_score, transferable, primary_strengths, primary_gaps = self._evaluate_technical(profile, opportunity)
        exp_score = self._evaluate_experience(profile, opportunity)
        remote_score = self._evaluate_remote(profile, opportunity)
        tz_score = self._evaluate_timezone(profile, opportunity)
        comp_score = self._evaluate_compensation(profile, opportunity)
        role_score = self._evaluate_role(profile, opportunity)
        industry_score = 80.0  # Baseline positive unless explicitly excluded

        # Weighted calculation
        # Technical: 25%, Experience: 20%, Role: 15%, Remote: 15%, Timezone: 10%, Comp: 15%
        overall = (
            tech_score * 0.25
            + exp_score * 0.20
            + role_score * 0.15
            + remote_score * 0.15
            + tz_score * 0.10
            + comp_score * 0.15
        )

        overall = max(5.0, min(100.0, round(overall, 1)))

        # Confidence based on detail richness in both profile and opportunity
        evidence_count = len(profile.skills) + len(profile.knowledge_items) + len(profile.work_experiences)
        opp_detail_count = len(opportunity.required_skills) + (1 if opportunity.salary_min or opportunity.hourly_rate else 0)
        confidence = min(98.0, 70.0 + (evidence_count * 1.5) + (opp_detail_count * 2.0))

        # Generate detailed natural language rationale
        strengths_str = ", ".join(primary_strengths[:3]) if primary_strengths else "general technical overlap"
        gaps_str = f"Primary gap: {', '.join(primary_gaps[:2])}." if primary_gaps else "No major technical blockers detected."
        transferable_str = ""
        if transferable:
            pairs = [f"{req} (transfers from your {cand})" for req, cand in list(transferable.items())[:2]]
            transferable_str = f" Strong transferable foundation in {', '.join(pairs)}."

        rationale = (
            f"Strong alignment ({overall:.0f}% overall) driven by your background in {strengths_str}."
            f"{transferable_str} {gaps_str}"
        )

        return MatchingScore(
            opportunity_id=opportunity.id or "unknown",
            overall_match_score=overall,
            confidence_score=round(confidence, 1),
            technical_match=round(tech_score, 1),
            experience_match=round(exp_score, 1),
            remote_match=round(remote_score, 1),
            timezone_match=round(tz_score, 1),
            compensation_match=round(comp_score, 1),
            industry_match=round(industry_score, 1),
            role_match=round(role_score, 1),
            transferable_skills=transferable,
            primary_strengths=primary_strengths,
            primary_gaps=primary_gaps,
            match_rationale=rationale,
        )

    def _evaluate_technical(
        self, profile: CandidateProfile, opportunity: Opportunity
    ) -> Tuple[float, Dict[str, str], List[str], List[str]]:
        candidate_skills_map = {s.skill_name.lower(): s for s in profile.skills}
        req_skills = [s.strip() for s in (opportunity.required_skills or []) if s and s.strip()]
        pref_skills = [s.strip() for s in (opportunity.preferred_skills or []) if s and s.strip()]

        # If no explicit skills listed in job, extract from title/description keywords
        if not req_skills:
            desc_lower = opportunity.description.lower() + " " + opportunity.title.lower()
            req_skills = [s.skill_name for s in profile.skills if s.skill_name.lower() in desc_lower]
            if not req_skills:
                req_skills = ["Software Engineering"]

        matched = []
        transferable = {}
        gaps = []

        for req in req_skills:
            req_low = req.lower()
            if req_low in candidate_skills_map:
                matched.append(req)
                continue

            # Check substring match
            found_sub = False
            for c_name, c_skill in candidate_skills_map.items():
                if req_low in c_name or c_name in req_low:
                    matched.append(req)
                    found_sub = True
                    break
            if found_sub:
                continue

            # Check transferable skill knowledge base
            found_transfer = False
            for base_skill, alternates in TRANSFERABLE_MAP.items():
                if req_low == base_skill or req_low in alternates:
                    # check if candidate has any of the alternates or the base
                    for cand_skill in candidate_skills_map.keys():
                        if cand_skill == base_skill or cand_skill in alternates:
                            transferable[req] = candidate_skills_map[cand_skill].skill_name
                            found_transfer = True
                            break
                if found_transfer:
                    break

            if not found_transfer:
                gaps.append(req)

        # Calculate score
        total_req = len(req_skills) or 1
        direct_ratio = len(matched) / total_req
        transfer_ratio = len(transferable) / total_req
        raw_tech = (direct_ratio * 100.0) + (transfer_ratio * 75.0)

        # Small bonus for preferred skills
        for pref in pref_skills:
            if pref.lower() in candidate_skills_map:
                raw_tech += 4.0

        return min(100.0, max(20.0, raw_tech)), transferable, matched, gaps

    def _evaluate_experience(self, profile: CandidateProfile, opportunity: Opportunity) -> float:
        req_years = opportunity.experience_required_years or 3.0
        # Calculate candidate's max or aggregate experience
        candidate_years = max([s.experience_years for s in profile.skills], default=5.0)
        if candidate_years >= req_years:
            return 95.0
        diff = req_years - candidate_years
        if diff <= 1:
            return 85.0
        elif diff <= 2:
            return 70.0
        return max(35.0, 60.0 - (diff * 10.0))

    def _evaluate_remote(self, profile: CandidateProfile, opportunity: Opportunity) -> float:
        if opportunity.remote_type == RemoteType.REMOTE:
            return 100.0
        if opportunity.remote_type == RemoteType.HYBRID:
            return 60.0 if profile.remote_preference != RemoteType.REMOTE else 40.0
        return 25.0  # Onsite

    def _evaluate_timezone(self, profile: CandidateProfile, opportunity: Opportunity) -> float:
        # If opportunity is remote worldwide, perfect score
        loc = (opportunity.location or "").lower()
        if "worldwide" in loc or "anywhere" in loc or not opportunity.timezone:
            return 95.0
        return 80.0

    def _evaluate_compensation(self, profile: CandidateProfile, opportunity: Opportunity) -> float:
        if opportunity.hourly_rate:
            if opportunity.hourly_rate >= profile.minimum_hourly_rate:
                return 100.0
            return max(30.0, (opportunity.hourly_rate / profile.minimum_hourly_rate) * 100.0)

        if opportunity.salary_min or opportunity.salary_max:
            max_comp = opportunity.salary_max or opportunity.salary_min or 0
            if max_comp >= profile.minimum_salary_annual:
                return 100.0
            return max(35.0, (max_comp / profile.minimum_salary_annual) * 100.0)

        # If not disclosed, neutral/positive score
        return 80.0

    def _evaluate_role(self, profile: CandidateProfile, opportunity: Opportunity) -> float:
        opp_title_lower = opportunity.title.lower()
        for role in profile.target_roles:
            if role.lower() in opp_title_lower or any(word in opp_title_lower for word in role.lower().split()):
                return 95.0
        return 70.0
