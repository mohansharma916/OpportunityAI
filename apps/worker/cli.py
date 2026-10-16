"""
OpportunityOS — Worker CLI (runs on the candidate's own machine)

  python -m apps.worker.cli login                      # sign in to LinkedIn / job boards once, in the automation browser
  python -m apps.worker.cli fill URL --company X --role Y   # fill one form, dry run (no submit)
  python -m apps.worker.cli fill --tracker-id ID --submit   # submit after the candidate has approved it
  python -m apps.worker.cli queue --limit 5            # dry-run every QUEUED tracker row, human-paced
  python -m apps.worker.cli linkedin-audit             # read your LinkedIn profile, score it, draft fixes
  python -m apps.worker.cli linkedin-apply             # dry-run approved headline/About edits
  python -m apps.worker.cli linkedin-apply --save      # save approved headline/About edits
  python -m apps.worker.cli discover                   # search job boards + company boards that are due
  python -m apps.worker.cli linkedin-posts             # search LinkedIn hiring posts (max 2 runs a day)
"""

import argparse
import asyncio
import sys
from typing import Any, Dict, List, Optional

from apps.api.db import AsyncSessionLocal, init_db
from apps.api.services.intake_service import DEFAULT_DAILY_CAP, IntakeService
from apps.api.services.linkedin_optimizer_service import LinkedInOptimizerService
from apps.api.services.tracker_service import DuplicateApplicationError, TrackerService
from apps.worker.automation import AutomationResult, BrowserSession, FormAutomationWorker, HumanPacer, PlaywrightDriver
from apps.api.services.discovery_service import DiscoveryService
from apps.worker.linkedin import NeedsCandidate, apply_edit, read_profile, search_posts
from packages.connectors.linkedin_posts import parse_hiring_post, search_urls

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


async def cmd_linkedin_audit(args: argparse.Namespace) -> int:
    await init_db()
    async with BrowserSession() as session:
        page = await session.new_page()
        try:
            snapshot = await read_profile(page)
        except NeedsCandidate as exc:
            print(exc, file=sys.stderr)
            return 2
    async with AsyncSessionLocal() as db:
        await LinkedInOptimizerService.save_snapshot(db, snapshot)
        state = await LinkedInOptimizerService.analyze(db, use_claude=False if args.no_claude else None)
    audit = state["audit"]
    print(f"Profile score: {audit['overall_score']}/100 (keywords from {audit['keywords_source']})")
    for s in audit["sections"]:
        score = "  ?" if s["score"] is None else f"{s['score']:>3}"
        print(f"  {score}  {s['label']}" + (f" — {s['findings'][0]}" if s["findings"] else ""))
    print(f"{len(state['drafts'])} drafts ready to review in the LinkedIn tab.")
    return 0


async def cmd_linkedin_apply(args: argparse.Namespace) -> int:
    await init_db()
    async with AsyncSessionLocal() as db:
        drafts = [d for d in await LinkedInOptimizerService.list_drafts(db, status="APPROVED") if d.apply_mode == "AGENT"]
        drafts = drafts[: args.limit]
        if not drafts:
            print("No approved headline/About drafts. Approve them in the LinkedIn tab first.")
            return 0
        pacer = HumanPacer(min_gap_s=args.min_gap, max_gap_s=args.max_gap)
        async with BrowserSession() as session:
            page = await session.new_page()
            for i, d in enumerate(drafts):
                try:
                    shots = await apply_edit(page, d.section, d.proposed_value, d.current_value, save=args.save, pacer=pacer)
                except NeedsCandidate as exc:
                    await LinkedInOptimizerService.record_apply(db, d.id, ok=False, error=str(exc))
                    print(f"[PAUSED] {d.title}: {exc}")
                    continue
                if args.save:
                    await LinkedInOptimizerService.record_apply(db, d.id, ok=True, evidence=shots)
                    print(f"[APPLIED] {d.title}")
                else:
                    d.evidence = list(d.evidence or []) + shots
                    await db.commit()
                    print(f"[DRY RUN] {d.title}: filled and discarded. Screenshot: {shots[-1]}")
                if i < len(drafts) - 1:
                    await pacer.between_applications()
    return 0


MAX_POST_SEARCHES_PER_DAY = 2


def _print_discovery(summary: Dict[str, Any]) -> None:
    print(f"{summary.get('platforms_run', 0)} sources: {summary.get('fetched', 0)} fetched, "
          f"{summary.get('eligible', 0)} eligible, {summary.get('new', 0)} new "
          f"({summary.get('match', 0)} match, {summary.get('maybe', 0)} maybe), {summary.get('queued', 0)} queued")
    for p in summary.get("platforms", []):
        if p.get("error"):
            print(f"  ! {p['platform']}: {p['error']}")


async def cmd_discover(args: argparse.Namespace) -> int:
    await init_db()
    async with AsyncSessionLocal() as db:
        _print_discovery(await DiscoveryService.run(db, force=args.force))
    return 0


async def _post_searches_today(db) -> int:
    from datetime import datetime
    from sqlalchemy import func, select
    from apps.api.models import AuditEventModel
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    res = await db.execute(select(func.count(AuditEventModel.id)).where(
        AuditEventModel.action == "LINKEDIN_POST_SEARCH", AuditEventModel.timestamp >= start))
    return int(res.scalar() or 0)


async def cmd_linkedin_posts(args: argparse.Namespace) -> int:
    await init_db()
    async with AsyncSessionLocal() as db:
        if await _post_searches_today(db) >= MAX_POST_SEARCHES_PER_DAY and not args.force:
            print(f"Already searched LinkedIn posts {MAX_POST_SEARCHES_PER_DAY} times today. Try again tomorrow.")
            return 0
        prefs = await DiscoveryService.prefs(db)
        if not prefs.target_titles:
            print("Set target titles in the intake first (section B).", file=sys.stderr)
            return 1
        urls = search_urls(prefs.target_titles, prefs.skills, limit=args.queries)
    pacer = HumanPacer(min_gap_s=args.min_gap, max_gap_s=args.max_gap)
    async with BrowserSession() as session:
        page = await session.new_page()
        try:
            raw = await search_posts(page, urls, pacer)
        except NeedsCandidate as exc:
            print(exc, file=sys.stderr)
            return 2
    postings = [p for p in (parse_hiring_post(r, prefs.target_titles) for r in raw) if p]
    async with AsyncSessionLocal() as db:
        stats = await DiscoveryService.ingest_linkedin_posts(db, postings)
        from apps.api.services.activity_service import ActivityService
        await ActivityService.record_event(
            db=db, entity_type="DISCOVERY", entity_id="linkedin-posts", action="LINKEDIN_POST_SEARCH",
            reason=f"{len(urls)} searches, {len(raw)} posts read, {len(postings)} hiring posts",
            output_payload=stats,
        )
    print(f"{len(urls)} searches, {len(raw)} posts read, {len(postings)} hiring posts: "
          f"{stats['eligible']} eligible, {stats['new']} new ({stats['match']} match, {stats['maybe']} maybe), "
          f"{stats['queued']} queued")
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

    p_li_audit = sub.add_parser("linkedin-audit", help="Read your LinkedIn profile, score it and draft fixes")
    p_li_audit.add_argument("--no-claude", action="store_true", help="Use template drafts only")
    p_li_audit.set_defaults(func=cmd_linkedin_audit)

    p_li_apply = sub.add_parser("linkedin-apply", help="Apply approved headline/About drafts")
    p_li_apply.add_argument("--save", action="store_true", help="Click Save (default: fill, screenshot, discard)")
    p_li_apply.add_argument("--limit", type=int, default=2)
    p_li_apply.add_argument("--min-gap", type=float, default=30)
    p_li_apply.add_argument("--max-gap", type=float, default=90)
    p_li_apply.set_defaults(func=cmd_linkedin_apply)

    p_disc = sub.add_parser("discover", help="Search job boards and company boards that are due")
    p_disc.add_argument("--force", action="store_true", help="Search every source now, even if not due")
    p_disc.set_defaults(func=cmd_discover)

    p_posts = sub.add_parser("linkedin-posts", help="Search LinkedIn hiring posts in your browser")
    p_posts.add_argument("--queries", type=int, default=5)
    p_posts.add_argument("--min-gap", type=float, default=20)
    p_posts.add_argument("--max-gap", type=float, default=60)
    p_posts.add_argument("--force", action="store_true", help="Ignore the 2-runs-a-day limit")
    p_posts.set_defaults(func=cmd_linkedin_posts)

    args = parser.parse_args(argv)
    return asyncio.run(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
