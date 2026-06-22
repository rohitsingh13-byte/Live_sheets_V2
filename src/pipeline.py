"""
Main pipeline orchestrator for Live Sheets V2.

Flow per run:
  1. Load (or create) today's checkpoint for this time slot
  2. Skip sheets already marked done in the checkpoint
  3. Connect to Snowflake (browser opens only if SSO token expired)
  4. For each pending sheet:
       a. Run SQL query → DataFrame
       b. Write via Apps Script webhook
       c. Save checkpoint immediately (crash-safe)
       d. If auth expired → stop early, report partial results to Slack
  5. Send full Slack report
  6. Clean up old checkpoint files

Re-running after a failure automatically resumes from the last checkpoint.
"""

import time
import logging
from datetime import datetime, timezone, timedelta

from src.config_reader  import load_for_slot
from src.snowflake_conn import connect, query as sf_query
from src.sheets_writer  import write as sheets_write
import src.checkpoint   as ckpt
from src.slack_notifier import send as slack_send
from src.errors         import classify, suggest

log = logging.getLogger(__name__)
IST = timezone(timedelta(hours=5, minutes=30))


def run(slot: str, force: bool = False) -> None:
    today = datetime.now(IST).strftime('%Y-%m-%d')
    log.info('═' * 60)
    log.info(f'Live Sheets V2  ·  slot={slot}  ·  {today}')
    log.info('═' * 60)

    # ── Load or create checkpoint ────────────────────────────────────
    checkpoint = ckpt.load(today, slot)

    if checkpoint and checkpoint.get('status') == 'complete' and not force:
        log.info("Today's run already complete. Use --force to re-run.")
        return

    is_resume = False
    skipped   = 0

    if checkpoint and checkpoint.get('status') == 'in_progress':
        skipped   = len(checkpoint.get('completed', []))
        is_resume = True
        log.info(f'Resuming — {skipped} sheet(s) already done, picking up from the next one')
    else:
        checkpoint = ckpt.create(today, slot)
        ckpt.save(today, slot, checkpoint)

    # ── Load mappings ────────────────────────────────────────────────
    mappings = load_for_slot(slot)
    if not mappings:
        log.warning(f'No active mappings for slot {slot}. Add rows to config/mappings.json')
        return

    pending = [m for m in mappings if not ckpt.is_done(checkpoint, m['name'])]
    log.info(f'{len(mappings)} total  ·  {len(pending)} pending  ·  {skipped} already done')

    if not pending:
        log.info('Nothing pending — finalising')
        _finalise(checkpoint, today, slot, is_resume, skipped)
        return

    # ── Connect to Snowflake ─────────────────────────────────────────
    log.info('Connecting to Snowflake…')
    try:
        conn = connect()
        log.info('  ✅ Connected')
    except Exception as e:
        error_type = classify(e)
        log.error(f'  ❌ Connection failed ({error_type}): {e}')
        checkpoint['status']     = 'auth_failed'
        checkpoint['last_error'] = str(e)
        ckpt.save(today, slot, checkpoint)
        slack_send(
            checkpoint['results'], slot,
            is_resume=is_resume, skipped=skipped, auth_failed=True,
        )
        raise

    # ── Process each pending mapping ─────────────────────────────────
    auth_failed = False

    for mapping in pending:
        name    = mapping['name']
        t_start = time.time()
        result  = {'name': name}
        log.info(f'  ┌─ [{name}]')

        try:
            # 1. Query Snowflake
            log.info('  │  querying Snowflake…')
            df = sf_query(conn, mapping['snowflake_query'])
            log.info(f'  │  {len(df):,} rows fetched')

            # 2. Write to Google Sheets
            log.info(f'  │  writing → {mapping["tab_name"]}…')
            rows_written = sheets_write(
                mapping['sheet_url'],
                mapping['tab_name'],
                mapping.get('range', 'A:Z'),
                df,
            )
            runtime = round(time.time() - t_start, 1)
            result.update({'status': 'success', 'rows': rows_written, 'runtime_s': runtime})
            log.info(f'  └─ ✅  {rows_written:,} rows · {runtime}s')

        except Exception as e:
            runtime    = round(time.time() - t_start, 1)
            error_type = classify(e)
            action     = suggest(error_type)
            result.update({
                'status':     'failed',
                'error':      str(e),
                'error_type': error_type,
                'action':     action,
                'runtime_s':  runtime,
            })
            log.error(f'  └─ ❌  [{error_type}] {e}')
            log.error(f'     Action: {action}')

            if error_type == 'auth_expired':
                auth_failed = True

        # Save checkpoint after every sheet — success or failure
        checkpoint = ckpt.add_result(checkpoint, name, result)
        ckpt.save(today, slot, checkpoint)

        if auth_failed:
            remaining = len(pending) - pending.index(mapping) - 1
            log.warning(
                f'Auth token expired — stopping early. '
                f'{remaining} sheet(s) not yet processed.\n'
                f'  → Re-run: python run.py --slot {slot}  '
                f'(browser will prompt for SSO, then resumes automatically)'
            )
            break

    try:
        conn.close()
    except Exception:
        pass

    # ── Finalise ─────────────────────────────────────────────────────
    _finalise(checkpoint, today, slot, is_resume, skipped, auth_failed)


def _finalise(checkpoint, today, slot, is_resume, skipped, auth_failed=False):
    if not auth_failed:
        checkpoint['status']      = 'complete'
        checkpoint['finished_at'] = datetime.now(timezone.utc).isoformat()
        ckpt.save(today, slot, checkpoint)

    s = sum(1 for r in checkpoint['results'] if r['status'] == 'success')
    f = sum(1 for r in checkpoint['results'] if r['status'] == 'failed')
    log.info(f'═══ {s} succeeded · {f} failed {"· PARTIAL (auth expired)" if auth_failed else ""} ═══')

    slack_send(
        checkpoint['results'], slot,
        is_resume=is_resume, skipped=skipped, auth_failed=auth_failed,
    )

    ckpt.cleanup_old(keep_days=7)
