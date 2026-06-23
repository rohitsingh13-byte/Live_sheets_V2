"""
Live Sheets V2 — Entry Point

Usage:
  python run.py                # auto-detect current IST time slot
  python run.py --slot 09:30   # run a specific slot

Environment variables (set as GitHub Secrets or in a local .env file):
  APPSSCRIPT_URL      — Apps Script Web App URL
  APPSSCRIPT_SECRET   — Secret key set in apps_script_code.js
  SLACK_WEBHOOK_URL   — (optional) Slack Incoming Webhook URL
  SNOWFLAKE_PAT       — (optional) Snowflake PAT if IT enables it
  SCHEDULE_SLOT       — (optional) overrides --slot; used by GitHub Actions
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def _setup_logging():
    os.makedirs('logs', exist_ok=True)
    date_tag = datetime.now(IST).strftime('%Y%m%d')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s  %(levelname)-8s  %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'logs/run_{date_tag}.log', encoding='utf-8'),
        ],
    )


def _detect_slot() -> str | None:
    from src.config_reader import all_slots
    now_mins = (lambda t: t.hour * 60 + t.minute)(datetime.now(IST))
    for slot in sorted(all_slots()):
        h, m = map(int, slot.split(':'))
        if abs(h * 60 + m - now_mins) <= 45:
            return slot
    return None


def main():
    # Load .env if present (useful for local testing)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    _setup_logging()

    parser = argparse.ArgumentParser(description='Live Sheets V2 Pipeline')
    parser.add_argument('--slot', default=os.environ.get('SCHEDULE_SLOT', '').strip())
    args = parser.parse_args()

    slot = args.slot or _detect_slot()

    if not slot:
        now_str = datetime.now(IST).strftime('%H:%M')
        print(f'[INFO] No matching slot for current IST time ({now_str}). Nothing to run.')
        print('[INFO] Use --slot HH:MM to force a run.')
        sys.exit(0)

    from src.pipeline import run
    run(slot)


if __name__ == '__main__':
    main()
