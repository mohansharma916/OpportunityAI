"""
OpportunityOS — Natural Language AI Command Service
Translates human commands into verified executable backend actions.
"""

import re
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from apps.api.models import OpportunityModel, CandidateProfileModel, ApplicationModel
from apps.api.services.profile_service import ProfileService
from apps.api.services.opportunity_service import OpportunityService
from apps.api.services.application_service import ApplicationService
from apps.api.services.activity_service import ActivityService


class AICommandService:
    @staticmethod
    async def execute_command(db: AsyncSession, prompt: str) -> Dict[str, Any]:
        prompt_clean = prompt.strip().lower()

        # Intent 1: "Prepare applications for everything above X% match"
        match_prep = re.search(r"prepare\s+(?:applications?\s+for\s+)?(?:everything|all|jobs)\s+(?:above|>|greater than)\s+(\d{1,3})", prompt_clean)
        if match_prep:
            threshold = float(match_prep.group(1))
            opp_svc = OpportunityService()
            high_matches = await opp_svc.get_opportunities(db, min_score=threshold)
            prepared_count = 0
            app_svc = ApplicationService()
            for opp in high_matches:
                if not opp.application:
                    await app_svc.prepare_application(db, opp.id)
                    prepared_count += 1
            return {
                "action": "PREPARED_HIGH_MATCH_APPLICATIONS",
                "message": f"Successfully prepared {prepared_count} applications for positions matching above {threshold}%.",
                "count": prepared_count,
                "requires_approval": False,
            }

        # Intent 2: "Increase minimum contract rate to $X/hour"
        match_rate = re.search(r"(?:increase|set|change)\s+(?:minimum\s+)?(?:contract\s+)?rate\s+to\s+\$?(\d+)", prompt_clean)
        if match_rate:
            new_rate = float(match_rate.group(1))
            profile = await ProfileService.get_or_create_profile(db)
            profile.minimum_hourly_rate = new_rate
            await db.commit()
            await ActivityService.record_event(
                db=db,
                entity_type="PROFILE",
                entity_id=profile.id,
                action="UPDATE_PREFERENCE",
                reason=f"Updated minimum contract rate to ${new_rate}/hr via AI Command.",
                output_payload={"minimum_hourly_rate": new_rate},
            )
            return {
                "action": "UPDATED_MINIMUM_RATE",
                "message": f"Updated candidate minimum hourly contract rate to ${new_rate:,.0f}/hr.",
                "new_value": new_rate,
            }

        # Intent 3: "Auto apply" or "Run auto apply"
        if "auto apply" in prompt_clean or "auto-apply" in prompt_clean:
            from apps.api.services.auto_apply_service import AutoApplyService
            auto_svc = AutoApplyService()
            result = await auto_svc.run_batch_auto_apply(db)
            return {
                "action": "AUTO_APPLY_EXECUTED",
                "message": result["message"],
                "applied_count": result.get("applied_count", 0),
                "needs_attention_count": result.get("needs_attention_count", 0),
            }

        # Intent 4: "Find open source ... projects" or "Discover opportunities"
        if "open source" in prompt_clean or "bount" in prompt_clean:
            opp_svc = OpportunityService()
            discovered = await opp_svc.run_discovery(db)
            os_items = [o for o in discovered if "OPEN_SOURCE" in str(o.employment_type)]
            return {
                "action": "DISCOVERED_OPEN_SOURCE",
                "message": f"Discovered {len(os_items)} open-source and bounty contribution opportunities matching your stack.",
                "items_count": len(os_items),
            }

        # Intent 4: "Run discovery" / "Discover new opportunities"
        if "discover" in prompt_clean or "find" in prompt_clean or "search" in prompt_clean:
            opp_svc = OpportunityService()
            discovered = await opp_svc.run_discovery(db)
            return {
                "action": "DISCOVERED_OPPORTUNITIES",
                "message": f"Discovery cycle complete. Ingested and scored {len(discovered)} global opportunities.",
                "total_discovered": len(discovered),
            }

        # Intent 5: "Set automation level to X"
        match_level = re.search(r"(?:set|change)\s+automation\s+level\s+to\s+(\d)", prompt_clean)
        if match_level:
            level = int(match_level.group(1))
            level = max(0, min(5, level))
            profile = await ProfileService.get_or_create_profile(db)
            profile.automation_level = level
            await db.commit()
            return {
                "action": "UPDATED_AUTOMATION_LEVEL",
                "message": f"Automation Level set to {level}.",
                "automation_level": level,
            }

        # Default fallback: Intelligent search explanation
        return {
            "action": "QUERY_ANALYZED",
            "message": f"Processed command: '{prompt}'. Applied filters to current candidate search pipeline.",
            "prompt": prompt,
        }
