"""
Quick connection test — run this ONCE before setting up scheduled automation.
Verifies Snowflake + Apps Script are both working.

Usage:
  python test_connection.py
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print('\n' + '─' * 50)
print('Live Sheets V2 — Connection Test')
print('─' * 50)

# ── Snowflake ──────────────────────────────────────────────────────
print('\n[1/2] Snowflake…')
try:
    from src.snowflake_conn import connect, query
    conn = connect()
    df   = query(conn, "SELECT CURRENT_TIMESTAMP() as ts, CURRENT_USER() as u, CURRENT_ROLE() as r")
    print(f'  ✅  Connected as {df["U"][0]}  role={df["R"][0]}')
    conn.close()
except Exception as e:
    print(f'  ❌  FAILED: {e}')

# ── Apps Script ────────────────────────────────────────────────────
print('\n[2/2] Apps Script webhook…')
url    = os.environ.get('APPSSCRIPT_URL', '').strip()
secret = os.environ.get('APPSSCRIPT_SECRET', '').strip()

if not url or not secret:
    print('  ⚠  APPSSCRIPT_URL or APPSSCRIPT_SECRET not set.')
    print('     Set them in a .env file or as environment variables.')
else:
    try:
        import requests
        import pandas as pd
        from src.sheets_writer import write

        # Post a tiny 1-row test to a throwaway sheet only if a test sheet URL is provided
        test_url = os.environ.get('TEST_SHEET_URL', '').strip()
        if test_url:
            df_test = pd.DataFrame({'col_a': ['test'], 'col_b': [123]})
            n = write(test_url, 'TestTab', 'A:B', df_test)
            print(f'  ✅  Apps Script OK — {n} row written to TestTab')
        else:
            # Just check reachability
            resp = requests.get(url, timeout=10)
            print(f'  ✅  Apps Script endpoint reachable (HTTP {resp.status_code})')
            print('     Set TEST_SHEET_URL=<sheet_url> in .env to do a full write test.')
    except Exception as e:
        print(f'  ❌  FAILED: {e}')

print('\n' + '─' * 50 + '\n')
