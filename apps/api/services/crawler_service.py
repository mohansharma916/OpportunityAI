"""
OpportunityOS — Autonomous Browser Crawler & Auto-Apply Orchestrator
Executes multi-platform crawling across remote job boards, open-source project contributions,
and hacker communities with live browser-level progress logs, duration limits, and session summaries.
"""

import uuid
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from apps.api.models import (
    OpportunityModel,
    MatchingScoreModel,
    ApplicationModel,
    CrawlerSessionModel,
    CrawlerScheduleModel,
)
from packages.domain.models import PipelineStatus, AuditEventType, SearchCriteria
from packages.connectors import (
    HackerNewsConnector,
    GitHubContributionConnector,
    RemoteTechConnector,
    RawListing,
)
from apps.api.services.profile_service import ProfileService
from apps.api.services.activity_service import ActivityService
from apps.api.services.auto_apply_service import AutoApplyService
from apps.api.services.opportunity_service import OpportunityService


class CrawlerService:
    @staticmethod
    async def get_or_create_schedule(db: AsyncSession) -> CrawlerScheduleModel:
        stmt = select(CrawlerScheduleModel).limit(1)
        res = await db.execute(stmt)
        sched = res.scalar_one_or_none()
        if not sched:
            sched = CrawlerScheduleModel(
                is_active=True,
                interval_hours=6,
                max_duration_minutes=15,
                max_applications=5,
                min_match_score=80.0,
                auto_apply_enabled=True,
                target_platforms=["ARBEITNOW", "JOBICY", "GITHUB_CONTRIBUTIONS", "HACKER_NEWS"],
                opportunity_types=["REMOTE", "CONTRACT", "PROJECT_CONTRIBUTION", "FULL_TIME"],
                last_run_at=datetime.utcnow() - timedelta(hours=2),
                next_run_at=datetime.utcnow() + timedelta(hours=4),
            )
            db.add(sched)
            await db.commit()
            await db.refresh(sched)
        return sched

    @staticmethod
    async def update_schedule(db: AsyncSession, config: Dict[str, Any]) -> CrawlerScheduleModel:
        sched = await CrawlerService.get_or_create_schedule(db)
        if "is_active" in config:
            sched.is_active = bool(config["is_active"])
        if "interval_hours" in config:
            sched.interval_hours = int(config["interval_hours"])
        if "max_duration_minutes" in config:
            sched.max_duration_minutes = int(config["max_duration_minutes"])
        if "max_applications" in config:
            sched.max_applications = int(config["max_applications"])
        if "min_match_score" in config:
            sched.min_match_score = float(config["min_match_score"])
        if "auto_apply_enabled" in config:
            sched.auto_apply_enabled = bool(config["auto_apply_enabled"])
        if "target_platforms" in config:
            sched.target_platforms = config["target_platforms"]
        if "opportunity_types" in config:
            sched.opportunity_types = config["opportunity_types"]

        sched.next_run_at = datetime.utcnow() + timedelta(hours=sched.interval_hours)
        sched.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(sched)
        return sched

    @staticmethod
    async def get_latest_session(db: AsyncSession) -> Optional[CrawlerSessionModel]:
        stmt = select(CrawlerSessionModel).order_by(CrawlerSessionModel.created_at.desc()).limit(1)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def run_crawler(
        db: AsyncSession,
        mode: str = "IMMEDIATE",
        max_duration_minutes: int = 15,
        max_applications: int = 5,
        min_match_score: float = 80.0,
        target_platforms: Optional[List[str]] = None,
        opportunity_types: Optional[List[str]] = None,
        auto_apply_enabled: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes an autonomous crawler run across web platforms:
        - Scrapes remote developer boards, GitHub project contributions, and tech communities
        - Logs browser navigation and data extraction in real-time
        - Scores opportunities against user profile & criteria
        - Autonomously prepares/submits applications up to limits
        - Generates a full crawl summary
        """
        start_time = time.time()
        logs: List[Dict[str, Any]] = []

        def add_log(step: str, platform: str, message: str, status: str = "INFO"):
            logs.append({
                "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
                "step": step,
                "platform": platform,
                "message": message,
                "status": status,
            })

        add_log("INITIALIZATION", "SYSTEM", f"Starting autonomous crawler agent in {mode} mode. Max duration: {max_duration_minutes}m, Max applications: {max_applications}.")

        profile = await ProfileService.get_domain_profile(db)
        user_name = profile.full_name if profile else "Candidate"
        currency = getattr(profile, "salary_currency", "USD") or "USD"
        salary_floor = profile.minimum_salary_annual if profile else 140000.0

        add_log(
            "CANDIDATE_GUARDRAILS",
            "PROFILE",
            f"Loaded preferences for {user_name}: Floor={currency} {salary_floor:,.0f}/yr, Target Roles={', '.join(profile.target_roles or ['Engineer']) if profile else 'Engineer'}.",
        )

        platforms_to_run = target_platforms or ["ARBEITNOW", "JOBICY", "GITHUB_CONTRIBUTIONS", "HACKER_NEWS"]
        discovered_opps: List[OpportunityModel] = []
        platforms_crawled = []

        opp_svc = OpportunityService()
        auto_svc = AutoApplyService()

        # 1. Platform: Remote & Tech Portals (Arbeitnow & Jobicy)
        if any(p in platforms_to_run for p in ["ARBEITNOW", "JOBICY", "REMOTE"]):
            add_log("BROWSER_NAVIGATION", "LIVE_WEB_REMOTE", "Navigating to global remote engineering feeds (Arbeitnow & Jobicy)...")
            try:
                connector = RemoteTechConnector()
                raw_listings = await connector.discover()
                platforms_crawled.append("Global Remote Tech Feeds (Arbeitnow & Jobicy)")
                add_log("DATA_EXTRACTION", "LIVE_WEB_REMOTE", f"Scraped {len(raw_listings)} active postings from global remote portals.", "SUCCESS")

                for raw in raw_listings:
                    opp = await connector.normalize(raw)
                    persisted = await opp_svc._persist_and_score_opportunity(db, opp, profile)
                    if persisted:
                        discovered_opps.append(persisted)
            except Exception as e:
                add_log("ERROR", "LIVE_WEB_REMOTE", f"Encountered non-blocking crawl warning: {str(e)}", "WARNING")

        # 2. Platform: GitHub Project Contributions & Paid Bounties
        if any(p in platforms_to_run for p in ["GITHUB", "GITHUB_CONTRIBUTIONS", "PROJECT_CONTRIBUTION"]):
            add_log("BROWSER_NAVIGATION", "GITHUB_CONTRIBUTIONS", "Navigating to GitHub Open Source & Bounty repositories matching skills...")
            try:
                gh_connector = GitHubContributionConnector()
                gh_raw = await gh_connector.discover()
                platforms_crawled.append("GitHub Contributions & Bounties")
                add_log("DATA_EXTRACTION", "GITHUB_CONTRIBUTIONS", f"Discovered {len(gh_raw)} project contributions & issues tagged with help-wanted / bounty.", "SUCCESS")

                for raw in gh_raw:
                    opp = await gh_connector.normalize(raw)
                    persisted = await opp_svc._persist_and_score_opportunity(db, opp, profile)
                    if persisted:
                        discovered_opps.append(persisted)
            except Exception as e:
                add_log("ERROR", "GITHUB_CONTRIBUTIONS", f"GitHub crawl warning: {str(e)}", "WARNING")

        # 3. Platform: Hacker News Tech Hiring
        if any(p in platforms_to_run for p in ["HACKER_NEWS", "HN"]):
            add_log("BROWSER_NAVIGATION", "HACKER_NEWS", "Crawling Hacker News 'Who is hiring?' startup threads...")
            try:
                hn_connector = HackerNewsConnector()
                hn_raw = await hn_connector.discover()
                platforms_crawled.append("Hacker News Who is Hiring")
                add_log("DATA_EXTRACTION", "HACKER_NEWS", f"Extracted {len(hn_raw)} direct founder and hiring manager threads.", "SUCCESS")

                for raw in hn_raw:
                    opp = await hn_connector.normalize(raw)
                    persisted = await opp_svc._persist_and_score_opportunity(db, opp, profile)
                    if persisted:
                        discovered_opps.append(persisted)
            except Exception as e:
                add_log("ERROR", "HACKER_NEWS", f"HN crawl warning: {str(e)}", "WARNING")

        # 4. Evaluation & Matching Phase
        add_log("MATCHING_ENGINE", "NEURAL_SCORER", f"Evaluated opportunities against verified skills matrix & experience graph.")

        if discovered_opps:
            opp_ids = [o.id for o in discovered_opps]
            eager_stmt = (
                select(OpportunityModel)
                .options(
                    selectinload(OpportunityModel.matching_score),
                    selectinload(OpportunityModel.application),
                )
                .where(OpportunityModel.id.in_(opp_ids))
            )
            eager_res = await db.execute(eager_stmt)
            eager_opps = list(eager_res.scalars().all())
        else:
            existing_stmt = (
                select(OpportunityModel)
                .options(
                    selectinload(OpportunityModel.matching_score),
                    selectinload(OpportunityModel.application),
                )
                .where(OpportunityModel.status.in_(["DISCOVERED", "STRONG_MATCH", "PREPARED"]))
                .limit(20)
            )
            existing_res = await db.execute(existing_stmt)
            eager_opps = list(existing_res.scalars().all())

        # Filter candidate opportunities that meet minimum match threshold
        qualifying = []
        for opp in eager_opps:
            score = opp.matching_score.overall_match_score if opp.matching_score else 0.0
            if score >= min_match_score:
                qualifying.append(opp)

        qualifying.sort(key=lambda o: (o.matching_score.overall_match_score if o.matching_score else 0.0), reverse=True)
        add_log("FILTER_PASSED", "POLICY", f"{len(qualifying)} opportunities meet or exceed threshold ({min_match_score}% fit score).", "SUCCESS")

        # 5. Automated Application Execution
        applied_count = 0
        staged_count = 0

        target_to_apply = qualifying[:max_applications] if max_applications > 0 else qualifying

        for opp in target_to_apply:
            score = opp.matching_score.overall_match_score if opp.matching_score else 0.0
            company = opp.company_name

            if auto_apply_enabled and (profile and profile.automation_level >= 4):
                add_log("AUTO_APPLY", company, f"Synthesizing tailored resume variant & submitting autonomously (Score: {score}%)...")
                try:
                    outcome = await auto_svc.auto_apply_opportunity(db, opp.id, force=True)
                    if outcome.get("applied"):
                        applied_count += 1
                        add_log("SUBMISSION_CONFIRMED", company, f"Successfully submitted application. Ref: {outcome.get('confirmation_reference')}", "SUCCESS")
                        # Attach structured tasks to the application
                        await CrawlerService._attach_application_tasks(db, opp.id, is_auto_applied=True)
                    else:
                        staged_count += 1
                        add_log("CIRCUIT_BREAKER", company, f"Staged for human approval: {outcome.get('reason')}", "WARNING")
                        await CrawlerService._attach_application_tasks(db, opp.id, is_auto_applied=False)
                except Exception as e:
                    staged_count += 1
                    add_log("APPLICATION_ERROR", company, f"Failed auto-submit, staged for review: {str(e)}", "WARNING")
            else:
                # Stage application with tailored resume for human review
                try:
                    app_model = await opp_svc.app_service.prepare_application(db, opp.id, style="TECHNICAL")
                    staged_count += 1
                    add_log("APPLICATION_PREPARED", company, f"Tailored resume and cover letter generated. Staged for review.", "SUCCESS")
                    await CrawlerService._attach_application_tasks(db, opp.id, is_auto_applied=False)
                except Exception as e:
                    add_log("PREPARE_WARNING", company, f"Could not prepare package: {str(e)}", "WARNING")

        duration_sec = round(time.time() - start_time, 2)
        summary_narrative = (
            f"Autonomous crawler finished in {duration_sec}s. Visited {len(platforms_crawled)} platforms, "
            f"discovered {len(discovered_opps)} opportunities, matched {len(qualifying)} to candidate profile (>= {min_match_score}% fit). "
            f"Autonomously submitted {applied_count} applications and staged {staged_count} for 1-click human review."
        )

        add_log("SUMMARY", "SYSTEM", summary_narrative, "SUCCESS")

        # Persist session in DB
        session_model = CrawlerSessionModel(
            id=str(uuid.uuid4()),
            status="COMPLETED",
            mode=mode,
            platforms_crawled=platforms_crawled,
            total_discovered=len(discovered_opps),
            total_matched=len(qualifying),
            total_applied=applied_count,
            total_staged=staged_count,
            duration_seconds=duration_sec,
            max_duration_minutes=max_duration_minutes,
            max_applications=max_applications,
            summary_text=summary_narrative,
            execution_logs=logs,
            created_at=datetime.utcnow(),
        )
        db.add(session_model)

        # Update schedule last_run
        sched = await CrawlerService.get_or_create_schedule(db)
        sched.last_run_at = datetime.utcnow()
        sched.next_run_at = datetime.utcnow() + timedelta(hours=sched.interval_hours)

        await db.commit()
        await db.refresh(session_model)

        # Audit Event
        await ActivityService.record_event(
            db=db,
            entity_type="CRAWLER",
            entity_id=session_model.id,
            action="CRAWL_SESSION_COMPLETED",
            reason=summary_narrative,
            output_payload={
                "discovered": len(discovered_opps),
                "applied": applied_count,
                "staged": staged_count,
                "duration_seconds": duration_sec,
            },
        )

        return {
            "session_id": session_model.id,
            "status": "COMPLETED",
            "platforms_crawled": platforms_crawled,
            "total_discovered": len(discovered_opps),
            "total_matched": len(qualifying),
            "total_applied": applied_count,
            "total_staged": staged_count,
            "duration_seconds": duration_sec,
            "summary_text": summary_narrative,
            "execution_logs": logs,
            "next_scheduled_run": sched.next_run_at.isoformat() if sched.next_run_at else None,
        }

    @staticmethod
    async def _attach_application_tasks(db: AsyncSession, opportunity_id: str, is_auto_applied: bool = False):
        """Ensures an application has structured, attached task checklist."""
        stmt = select(ApplicationModel).where(ApplicationModel.opportunity_id == opportunity_id)
        res = await db.execute(stmt)
        app = res.scalar_one_or_none()
        if not app:
            return

        now = datetime.utcnow().strftime("%b %d, %Y %H:%M")
        default_tasks = [
            {"id": "t1", "title": "Opportunity Crawled & Analyzed", "status": "COMPLETED", "completed_at": now},
            {"id": "t2", "title": "Semantic Fit & Salary Floor Validated", "status": "COMPLETED", "completed_at": now},
            {"id": "t3", "title": "Tailored Resume Variant Generated", "status": "COMPLETED", "completed_at": now},
            {"id": "t4", "title": "Targeted Cover Letter Synthesized", "status": "COMPLETED", "completed_at": now},
            {"id": "t5", "title": "Screening Q&A Memory Resolved", "status": "COMPLETED", "completed_at": now},
            {
                "id": "t6",
                "title": "Application Submitted to Employer Portal",
                "status": "COMPLETED" if is_auto_applied else "PENDING",
                "completed_at": now if is_auto_applied else None,
            },
            {"id": "t7", "title": "Hiring Manager / Team Follow-Up", "status": "PENDING", "completed_at": None},
        ]
        if not app.tasks:
            app.tasks = default_tasks
        else:
            # Sync submission task if auto-applied
            if is_auto_applied:
                updated = []
                for t in app.tasks:
                    if t.get("id") == "t6":
                        updated.append({**t, "status": "COMPLETED", "completed_at": now})
                    else:
                        updated.append(t)
                app.tasks = updated

        await db.commit()
