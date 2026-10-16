"""
OpportunityOS — Worker CLI (runs on the candidate's own machine)

  python -m apps.worker.cli login                      # sign in to LinkedIn / job boards once, in the automation browser
  python -m apps.worker.cli fill URL --company X --role Y   # fill one form, dry run (no submit)
  python -m apps.worker.cli fill --tracker-id ID --submit   # submit after the candidate has approved it
  python -m apps.worker.cli queue --limit 5            # dry-run every QUEUED tracker row, human-paced
"""

import argparse
import asyncio
import sys
from typing import Any, Dict, List, Optional

from apps.api.db import AsyncSessionLocal, init_db
from apps.api.services.intake_service import DEFAULT_DAILY_CAP, IntakeService
from apps.api.services.tracker_service import DuplicateApplicationError, TrackerService
from apps.worker.automation import AutomationResult, BrowserSession, FormAutomationWorker, HumanPacer, PlaywrightDriver

LOGIN_URLS = [
    "https://www.linkedin.com/login",
    "https://wellfound.com/login",
    "https://weworkremotely.com",
    "https://remoteok.com",
    "https://www.workatastartup.com",
]


def tracker_update_for(result: AutomationResult) -> Dict[str, Any]:
    """Translate a worker run into tracker fields."""
    if result.status == "SUBMITTED":
        return {"status": "SUBMITTED", "last_error": None}
    if result.status == "FILLED":
        return {"status": "AWAITING_APPROVAL", "last_error": None, "next_action": "Review and approve submit"}
    if result.status == "NEEDS_CANDIDATE":
        return {"status": "PAUSED", "last_error": result.details, "next_action": "Candidate action needed"}
    return {"last_error": result.details}


async def _daily_cap(db, user_id: Optional[str] = None) -> int:
    intake = await IntakeService.get_or_create(db, user_id=user_id)
    return int((intake.targeting or {}).get("daily_cap") or DEFAULT_DAILY_CAP)


async def _run_one(session: BrowserSession, db, row, submit: bool, pacer: HumanPacer) -> AutomationResult:
    bank = await IntakeService.build_answer_bank(
        db, resume_variant=row.resume_variant if row else None, cover_note=row.cover_note if row else None
    )
    page = await session.new_page()
    worker = FormAutomationWorker(PlaywrightDriver(page), pacer=pacer)
    result = await worker.apply(row.job_url, bank, submit=submit)
    update = tracker_update_for(result)
    update["evidence"] = list(row.evidence or []) + result.screenshots
    await TrackerService.update(db, row.id, update)
    return result


def _print(result: AutomationResult) -> None:
    print(f"[{result.status}] {result.step_reached} — {result.details}")
    for s in result.screenshots:
        print(f"  evidence: {s}")


async def cmd_login(args: argparse.Namespace) -> int:
    async with BrowserSession() as session:
        for url in args.url or LOGIN_URLS:
            page = await session.new_page()
            await page.goto(url)
        print("Sign in to each site in the browser window (2FA stays on). Close the browser when done.")
        await session.wait_until_closed()
    print("Logins are saved in the automation browser profile. No passwords were stored.")
    return 0


async def cmd_fill(args: argparse.Namespace) -> int:
    await init_db()
    async with AsyncSessionLocal() as db:
        if args.tracker_id:
            row = await TrackerService.get(db, args.tracker_id)
            if not row:
                print(f"No tracked application {args.tracker_id}", file=sys.stderr)
                return 1
        else:
            if not (args.url and args.company and args.role):
                print("Give --tracker-id, or a URL with --company and --role", file=sys.stderr)
                return 1
            try:
                row = await TrackerService.create(db, {
                    "company": args.company, "role": args.role, "job_url": args.url,
                    "source_platform": args.source or "MANUAL", "resume_variant": args.resume_variant,
                })
            except DuplicateApplicationError as dup:
                print(f"Already tracked ({dup.existing.status}); using that row.")
                row = dup.existing
        if not row.job_url:
            print("This application has no job URL.", file=sys.stderr)
            return 1

        if args.submit:
            if row.status not in ("AWAITING_APPROVAL", "PAUSED"):
                print("Submit only after a dry run has filled the form and you have reviewed it.", file=sys.stderr)
                return 1
            cap = await _daily_cap(db)
            if await TrackerService.submitted_today(db) >= cap:
                print(f"Daily cap of {cap} submissions reached. Try again tomorrow.", file=sys.stderr)
                return 1

        async with BrowserSession() as session:
            result = await _run_one(session, db, row, submit=args.submit, pacer=HumanPacer())
            _print(result)
            if args.keep_open:
                print("Browser left open for review. Close it when done.")
                await session.wait_until_closed()
    return 0 if result.status in ("FILLED", "SUBMITTED") else 2


async def cmd_queue(args: argparse.Namespace) -> int:
    await init_db()
    async with AsyncSessionLocal() as db:
        rows: List = [r for r in await TrackerService.list(db, status="QUEUED") if r.job_url][: args.limit]
        if not rows:
            print("Nothing queued.")
            return 0
        pacer = HumanPacer(min_gap_s=args.min_gap, max_gap_s=args.max_gap)
        async with BrowserSession() as session:
            for i, row in enumerate(rows):
                print(f"({i + 1}/{len(rows)}) {row.company} — {row.role}")
                _print(await _run_one(session, db, row, submit=False, pacer=pacer))
                if i < len(rows) - 1:
                    gap = await pacer.between_applications()
                    print(f"  waited {gap:.0f}s")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="opportunity-os-worker")
    sub = parser.add_subparsers(dest="command", required=True)

    p_login = sub.add_parser("login", help="Open the automation browser to sign in to sites once")
    p_login.add_argument("--url", action="append", help="Site to open (repeatable); defaults to LinkedIn + main boards")
    p_login.set_defaults(func=cmd_login)

    p_fill = sub.add_parser("fill", help="Fill one application form")
    p_fill.add_argument("url", nargs="?")
    p_fill.add_argument("--tracker-id")
    p_fill.add_argument("--company")
    p_fill.add_argument("--role")
    p_fill.add_argument("--source")
    p_fill.add_argument("--resume-variant")
    p_fill.add_argument("--submit", action="store_true", help="Submit (only after reviewing a dry run)")
    p_fill.add_argument("--keep-open", action="store_true", help="Leave the browser open to review the form")
    p_fill.set_defaults(func=cmd_fill)

    p_queue = sub.add_parser("queue", help="Dry-run fill every QUEUED application")
    p_queue.add_argument("--limit", type=int, default=5)
    p_queue.add_argument("--min-gap", type=float, default=30)
    p_queue.add_argument("--max-gap", type=float, default=120)
    p_queue.set_defaults(func=cmd_queue)

    args = parser.parse_args(argv)
    return asyncio.run(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
