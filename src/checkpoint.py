"""
Checkpoint / Resume System
──────────────────────────
Saves progress after EVERY sheet so a mid-run failure (token expiry,
network drop, etc.) can resume from the last successful sheet instead
of restarting from scratch.

File layout:  checkpoints/YYYY-MM-DD_HHMM.json
  → one file per (date, slot) pair
  → written atomically: tmp file → rename, so a crash during write never
    leaves a corrupt checkpoint

Checkpoint schema:
{
  "date":         "2026-06-23",
  "slot":         "09:30",
  "started_at":   "<ISO UTC>",
  "status":       "in_progress" | "complete" | "auth_failed",
  "completed":    ["Sheet A", "Sheet B"],   ← names of sheets already processed
  "results":      [{...result dict...}, ...],
  "finished_at":  "<ISO UTC>"  (only when status == "complete")
}
"""

import json
import os
import logging
import tempfile
from datetime import datetime, timezone

log = logging.getLogger(__name__)
_DIR = os.path.join(os.path.dirname(__file__), '..', 'checkpoints')


def _path(date: str, slot: str) -> str:
    safe = slot.replace(':', '')
    return os.path.join(_DIR, f'{date}_{safe}.json')


def load(date: str, slot: str) -> dict | None:
    p = _path(date, slot)
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        data = json.load(f)
    log.info(f'Checkpoint loaded — {len(data.get("completed", []))} sheets already done')
    return data


def create(date: str, slot: str) -> dict:
    return {
        'date': date,
        'slot': slot,
        'started_at': datetime.now(timezone.utc).isoformat(),
        'status': 'in_progress',
        'completed': [],
        'results': [],
    }


def save(date: str, slot: str, data: dict) -> None:
    os.makedirs(_DIR, exist_ok=True)
    target = _path(date, slot)
    # Write to tmp then rename — crash-safe
    fd, tmp = tempfile.mkstemp(dir=_DIR, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp, target)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def add_result(ckpt: dict, name: str, result: dict) -> dict:
    ckpt['completed'].append(name)
    ckpt['results'].append(result)
    return ckpt


def is_done(ckpt: dict, name: str) -> bool:
    return name in ckpt.get('completed', [])


def cleanup_old(keep_days: int = 7) -> None:
    """Delete checkpoint files older than keep_days."""
    if not os.path.exists(_DIR):
        return
    cutoff = datetime.now(timezone.utc).timestamp() - keep_days * 86400
    for fname in os.listdir(_DIR):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(_DIR, fname)
        if os.path.getmtime(fpath) < cutoff:
            os.remove(fpath)
            log.debug(f'Removed old checkpoint: {fname}')
