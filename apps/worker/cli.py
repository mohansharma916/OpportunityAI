"""
OpportunityOS — Worker CLI (runs on the candidate's own machine)

  python -m apps.worker.cli login                      # sign in to LinkedIn / job boards once, in the automation browser
  python -m apps.worker.cli inspect URL                # what would be filled on a form (types nothing)
  python -m apps.worker.cli fill URL --company X --role Y   # fill one form, dry run (no submit)
  python -m apps.worker.cli queue --limit 5            # fill every QUEUED row (dry run), human-paced
  python -m apps.worker.cli approve ID                 # approve a filled application (or use the Applications tab)
  python -m apps.worker.cli submit                     # submit approved applications, within the daily cap
  python -m apps.worker.cli run                        # queue + submit + follow-ups due
  python -m apps.worker.cli follow-ups                 # follow-ups due, with a drafted message
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
from apps.api.services.intake_service import IntakeService
from apps.api.services.linkedin_optimizer_service import LinkedInOptimizerService
from apps.api.services.tracker_service import DuplicateApplicationError, TrackerService
from apps.worker.apply_runner import SkipRow, auto_submit_enabled, run_row
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


def _print(result: AutomationResult) -> None:
    print(f"[{result.status}] {result.step_reached} — {result.details}")
    for q in result.unanswered_fields:
        print(f"  ? {q['label']}" + (f"  options: {', '.join(q['options'][:6])}" if q.get("options") else ""))
    for s in result.screenshots:
        print(f"  evidence: {s}")


async def _announce_captcha() -> None:
    print("  A CAPTCHA appeared after submit. Solve it in the browser window; waiting up to 5 minutes…")


async def _process(rows: List, submit_rule, pacer: HumanPacer, keep_open: bool = False) -> None:
    """Run rows in one browser session, human-paced; submit_rule(db, row) decides dry run vs submit."""
    async with BrowserSession() as session:
        for i, row_id in enumerate(rows):
            async with AsyncSessionLocal() as db:
                row = await TrackerService.get(db, row_id)
                submit = await submit_rule(db, row)
                print(f"({i + 1}/{len(rows)}) {row.company} — {row.role} [{'submit' if submit else 'fill'}]")
                page = await session.new_page()
                try:
                    _print(await run_row(db, row, PlaywrightDriver(page), pacer, submit, on_captcha=_announce_captcha))
                except SkipRow as exc:
                    print(f"  skipped: {exc}")
                    await page.close()
                    continue
            if i < len(rows) - 1:
                print(f"  waited {await pacer.between_applications():.0f}s")
        if keep_open:
            print("Browser left open for review. Close it when done.")
            await session.wait_until_closed()


async def _queued_ids(db, limit: int) -> List[str]:
    return [r.id for r in await TrackerService.list(db, status="QUEUED") if r.job_url][:limit]


async def _approved_ids(db, limit: int) -> List[str]:
    return [r.id for r in await TrackerService.list(db, status="APPROVED") if r.job_url][:limit]


async def _trusted_rule(db, row) -> bool:
    return await TrackerService.is_trusted(db, row.apply_channel, await auto_submit_enabled(db))


async def _always_submit(db, row) -> bool:
    return True


async def _never_submit(db, row) -> bool:
    return False


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
    await _process([row.id], _always_submit if args.submit else _never_submit, HumanPacer(), keep_open=args.keep_open)
    return 0


async def cmd_queue(args: argparse.Namespace) -> int:
    """Fill every QUEUED application (dry run; trusted job sites submit directly if you opted in)."""
    await init_db()
    async with AsyncSessionLocal() as db:
        ids = await _queued_ids(db, args.limit)
    if not ids:
        print("Nothing queued.")
        return 0
    await _process(ids, _trusted_rule, HumanPacer(min_gap_s=args.min_gap, max_gap_s=args.max_gap))
    return 0


async def cmd_submit(args: argparse.Namespace) -> int:
    """Submit every application you approved, within the daily cap."""
    await init_db()
    async with AsyncSessionLocal() as db:
        ids = await _approved_ids(db, args.limit)
    if not ids:
        print("Nothing approved. Review filled applications in the Applications tab and approve them.")
        return 0
    await _process(ids, _always_submit, HumanPacer(min_gap_s=args.min_gap, max_gap_s=args.max_gap))
    return 0


async def cmd_approve(args: argparse.Namespace) -> int:
    await init_db()
    async with AsyncSessionLocal() as db:
        try:
            row = await TrackerService.approve(db, args.tracker_id)
        except (LookupError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 1
    print(f"Approved {row.company} — {row.role}. Run `submit` to send it.")
    return 0


async def cmd_inspect(args: argparse.Namespace) -> int:
    """Show what would be filled on a form, and what's missing. Types nothing."""
    await init_db()
    async with AsyncSessionLocal() as db:
        bank = await IntakeService.build_answer_bank(db)
    async with BrowserSession() as session:
        page = await session.new_page()
        result = await FormAutomationWorker(PlaywrightDriver(page), pacer=HumanPacer()).inspect(args.url, bank)
    print(f"{result.adapter}: {result.details}")
    for f in result.fields:
        print(f"  fill  {f['label'][:60]:60} <- {str(f['value'])[:40]!r}")
    for q in result.unanswered_fields:
        print(f"  ASK   {q['label'][:60]:60}" + (f" options: {', '.join(q['options'][:5])}" if q.get("options") else ""))
    return 0


async def cmd_follow_ups(args: argparse.Namespace) -> int:
    await init_db()
    async with AsyncSessionLocal() as db:
        intake = await IntakeService.get_or_create(db)
        due = await TrackerService.follow_ups_due(db, (intake.identity or {}).get("full_name") or "")
    if not due:
        print("No follow-ups due.")
    for d in due:
        print(f"- {d['company']} — {d['role']} (submitted {(d['submitted_at'] or '')[:10]})\n    {d['message']}")
    return 0


async def cmd_run(args: argparse.Namespace) -> int:
    """Daily loop: fill queued, submit approved, list follow-ups."""
    await cmd_queue(args)
    await cmd_submit(args)
    return await cmd_follow_ups(args)


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
    p_fill.add_argument("--submit", action="store_true", help="Submit (only if approved)")
    p_fill.add_argument("--keep-open", action="store_true", help="Leave the browser open to review the form")
    p_fill.set_defaults(func=cmd_fill)

    for name, func, help_text in (
        ("queue", cmd_queue, "Fill every QUEUED application (dry run)"),
        ("submit", cmd_submit, "Submit approved applications within the daily cap"),
        ("run", cmd_run, "Fill queued, submit approved, list follow-ups"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--limit", type=int, default=5)
        p.add_argument("--min-gap", type=float, default=30)
        p.add_argument("--max-gap", type=float, default=120)
        p.set_defaults(func=func)

    p_approve = sub.add_parser("approve", help="Approve a filled application for submission")
    p_approve.add_argument("tracker_id")
    p_approve.set_defaults(func=cmd_approve)

    p_inspect = sub.add_parser("inspect", help="Show what would be filled on a form; types nothing")
    p_inspect.add_argument("url")
    p_inspect.set_defaults(func=cmd_inspect)

    p_fu = sub.add_parser("follow-ups", help="Follow-ups due, with a drafted message")
    p_fu.set_defaults(func=cmd_follow_ups)

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
