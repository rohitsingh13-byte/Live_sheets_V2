import os
import logging
import requests
from datetime import datetime, timezone, timedelta

log = logging.getLogger(__name__)
IST = timezone(timedelta(hours=5, minutes=30))


def _fmt_time(seconds: float) -> str:
    s = int(seconds)
    return f'{s // 60}:{s % 60:02d}'


def send(results: list, slot: str, is_resume: bool = False,
         skipped: int = 0, auth_failed: bool = False) -> None:
    """
    Post a Slack run report.
    Does nothing (silently) if SLACK_WEBHOOK_URL is not configured.
    """
    webhook = os.environ.get('SLACK_WEBHOOK_URL', '').strip()
    if not webhook:
        log.info('SLACK_WEBHOOK_URL not set — skipping Slack notification')
        return

    success_list = [r for r in results if r.get('status') == 'success']
    failed_list  = [r for r in results if r.get('status') == 'failed']
    total_rows   = sum(r.get('rows', 0) for r in success_list)
    total_secs   = sum(r.get('runtime_s', 0) for r in results)

    now_ist   = datetime.now(IST)
    date_str  = now_ist.strftime('%a, %d %b %Y')
    all_ok    = not failed_list and not auth_failed
    icon      = '🟢' if all_ok else ('🟡' if not all_ok and success_list else '🔴')

    # ── Header line ──────────────────────────────────────────────────
    header_parts = [f'{len(results)} sheet(s)', f'{total_rows:,} rows', f'{_fmt_time(total_secs)} total']
    header = (
        f'{icon}  *Live Sheets V2 — {slot} IST*\n'
        f'{date_str}   {" · ".join(header_parts)}'
    )

    # ── Optional notes ───────────────────────────────────────────────
    notes = []
    if is_resume and skipped > 0:
        notes.append(f'_Resumed from checkpoint — {skipped} sheet(s) were already done._')
    if auth_failed:
        notes.append(
            ':warning: *Auth token expired mid-run. '
            f'{len(success_list)}/{len(results) + skipped} sheets completed.*\n'
            '>Run `python run.py` on the PC — browser will open for SSO login, then auto-resume.'
        )

    # ── Results table ────────────────────────────────────────────────
    rows_lines = []
    for r in results:
        s    = '✅' if r['status'] == 'success' else '❌'
        name = r['name'][:26]
        cols = f"{r.get('rows', 0):>7,}" if r['status'] == 'success' else '      —'
        time = _fmt_time(r.get('runtime_s', 0)) if r['status'] == 'success' else '   —'
        rows_lines.append(f'{name:<26} {s}  {cols}  {time:>5}')

    table = (
        '```'
        'Name                       Status     Rows   Time\n'
        + '─' * 52 + '\n'
        + '\n'.join(rows_lines)
        + '```'
    )

    # ── Failure detail ───────────────────────────────────────────────
    fail_detail = ''
    for r in failed_list:
        fail_detail += (
            f'\n*❌ {r["name"]}*\n'
            f'>Type: `{r.get("error_type", "unknown")}`\n'
            f'>Detail: {str(r.get("error", ""))[:200]}\n'
            f'>Action: _{r.get("action", "Check logs")}_\n'
        )

    # ── Assemble & send ──────────────────────────────────────────────
    parts = [header]
    if notes:
        parts.append('\n'.join(notes))
    parts.append(table)
    if fail_detail:
        parts.append(fail_detail)

    text = '\n\n'.join(parts)

    try:
        resp = requests.post(webhook, json={'text': text, 'mrkdwn': True}, timeout=15)
        resp.raise_for_status()
        log.info('Slack notification sent')
    except Exception as e:
        log.warning(f'Slack notification failed (non-fatal): {e}')
