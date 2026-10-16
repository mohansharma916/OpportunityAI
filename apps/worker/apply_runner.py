"""
OpportunityOS — Apply runner: one tracker row through the worker.

QUEUED   -> fill (dry run) -> AWAITING_APPROVAL, or PAUSED with open questions (+ Claude suggestions)
APPROVED -> fill again, check the answers still match what was approved, submit -> SUBMITTED
Trusted ATS (opt-in, after 20 clean approvals): QUEUED is filled and submitted in one pass.
"""

from typing import Any, Awaitable, Callable, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.services.intake_service import DEFAULT_DAILY_CAP, IntakeService
from apps.api.services.tracker_service import TrackerService
from apps.worker.automation import AutomationResult, FormAutomationWorker, HumanPacer, PageDriver


class SkipRow(Exception):
    pass


async def daily_cap(db: AsyncSession) -> int:
    intake = await IntakeService.get_or_create(db)
    return int((intake.targeting or {}).get("daily_cap") or DEFAULT_DAILY_CAP)


async def auto_submit_enabled(db: AsyncSession) -> bool:
    intake = await IntakeService.get_or_create(db)
    return bool((intake.targeting or {}).get("auto_submit_trusted"))


async def candidate_facts(db: AsyncSession) -> Dict[str, Any]:
    from apps.api.services.linkedin_optimizer_service import LinkedInOptimizerService

    intake = await IntakeService.get_or_create(db)
    facts = (await LinkedInOptimizerService.candidate_facts(db)).model_dump()
    facts["screening"] = intake.screening or {}
    facts["targeting"] = {k: v for k, v in (intake.targeting or {}).items() if k != "daily_cap"}
    facts["location"] = {k: (intake.identity or {}).get(k) for k in ("city", "country", "timezone")}
    return facts


async def suggest(db: AsyncSession, row: Any, result: AutomationResult) -> Dict[str, Dict[str, Any]]:
    from packages.ai.claude_answers import suggest_answers
    from packages.ai.claude_drafter import claude_available

    if not result.unanswered_fields or not claude_available():
        return {}
    job: Dict[str, Any] = {"company": row.company, "title": row.role}
    if row.opportunity_id:
        from apps.api.services.opportunity_service import OpportunityService

        opp = await OpportunityService().get_opportunity_by_id(db, row.opportunity_id)
        if opp:
            job["description"] = (opp.description or "")[:5000]
    return await suggest_answers(result.unanswered_fields, await candidate_facts(db), job)


async def run_row(
    db: AsyncSession,
    row: Any,
    driver: PageDriver,
    pacer: HumanPacer,
    submit: bool,
    on_captcha: Optional[Callable[[], Awaitable[None]]] = None,
) -> AutomationResult:
    if not row.job_url:
        raise SkipRow("No job URL on this application.")
    expected = None
    if submit:
        expected = (row.form or {}).get("approved_fingerprint")
        trusted = row.status == "QUEUED" and await TrackerService.is_trusted(
            db, row.apply_channel, await auto_submit_enabled(db))
        if row.status != "APPROVED" and not trusted:
            raise SkipRow("Not approved. Review the fill and approve it first.")
        if await TrackerService.submitted_today(db) >= await daily_cap(db):
            raise SkipRow("Daily submission cap reached.")
        if row.status == "APPROVED" and not expected:
            raise SkipRow("Approval has no recorded fill. Re-run the fill and approve again.")

    bank = await IntakeService.build_answer_bank(db, resume_variant=row.resume_variant, cover_note=row.cover_note)
    worker = FormAutomationWorker(driver, pacer=pacer, on_captcha=on_captcha)
    result = await worker.apply(row.job_url, bank, submit=submit, expected_fingerprint=expected)
    suggestions = await suggest(db, row, result)
    await TrackerService.record_run(db, row.id, result.model_dump(), suggestions=suggestions, submit=submit)
    return result
