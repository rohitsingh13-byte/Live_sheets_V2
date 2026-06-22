import os
import re
import math
import logging
import requests
import pandas as pd

log = logging.getLogger(__name__)
CHUNK_SIZE = 1500   # Apps Script has a ~30s timeout per request; 1500 rows is safe


def _sheet_id(url: str) -> str:
    m = re.search(r'/spreadsheets/d/([a-zA-Z0-9_-]+)', url)
    if not m:
        raise ValueError(f'Cannot extract Sheet ID from URL: {url}')
    return m.group(1)


def _clean(df: pd.DataFrame) -> list:
    """Convert DataFrame to a list-of-lists safe for JSON + Apps Script."""
    rows = [df.columns.tolist()]
    for _, row in df.iterrows():
        cleaned = []
        for v in row:
            if v is None or (isinstance(v, float) and math.isnan(v)):
                cleaned.append('')
            elif hasattr(v, 'isoformat'):
                cleaned.append(v.isoformat())
            elif isinstance(v, (int, float, bool, str)):
                cleaned.append(v)
            else:
                cleaned.append(str(v))
        rows.append(cleaned)
    return rows


def write(sheet_url: str, tab_name: str, data_range: str, df: pd.DataFrame) -> int:
    """
    Write df to a Google Sheet tab via Apps Script webhook.
    Sends data in chunks of CHUNK_SIZE rows.
    Returns the number of data rows written (excluding header).

    Required env vars:
        APPSSCRIPT_URL    — the /exec URL of your deployed Apps Script web app
        APPSSCRIPT_SECRET — must match WRITE_SECRET in the Apps Script code
    """
    url    = os.environ.get('APPSSCRIPT_URL', '').strip()
    secret = os.environ.get('APPSSCRIPT_SECRET', '').strip()

    if not url or not secret:
        raise EnvironmentError(
            'APPSSCRIPT_URL and APPSSCRIPT_SECRET must be set. '
            'Add them as GitHub Secrets (repo → Settings → Secrets → Actions).'
        )

    sid  = _sheet_id(sheet_url)
    rows = _clean(df)
    total_data_rows = len(rows) - 1   # minus header

    for chunk_num, i in enumerate(range(0, len(rows), CHUNK_SIZE)):
        chunk = rows[i : i + CHUNK_SIZE]
        payload = {
            'secret':  secret,
            'sheetId': sid,
            'tabName': tab_name,
            'rows':    chunk,
            'chunk':   chunk_num,
        }
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        if not result.get('success'):
            raise RuntimeError(f'Apps Script returned error: {result.get("error")}')

        log.debug(f'    chunk {chunk_num + 1}: {len(chunk)} rows sent')

    return total_data_rows
