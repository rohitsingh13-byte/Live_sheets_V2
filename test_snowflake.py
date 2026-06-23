"""
Standalone Snowflake test.

Usage (local):    python test_snowflake.py
Usage (GitHub):   triggered by .github/workflows/test_snowflake.yml

Output: output/test_result.csv  (uploaded as GitHub Actions artifact)
"""

import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.snowflake_conn import connect, query

TEST_SQL = """
SELECT DISTINCT
    o.lead_id,
    c2b_lead_id,
    procurement_type,
    alternate_phone_reason,
    CASE
        WHEN o.alternate_phone_reason = 'C2D_FULL_ASSIST'
            THEN 'C2D_FULL_ASSIST'
        WHEN o.procurement_type = 'C2D'
         AND (o.alternate_phone_reason IS NULL OR o.alternate_phone_reason <> 'C2D_FULL_ASSIST')
            THEN 'C2D_SELF_ASSIST'
        ELSE 'C2B'
    END AS FINAL_PROCUREMENT_TYPE,
    gs_type
FROM CSPL_C2B_DB.ADMIN_PANEL_PROD_DEALERENGINE_PROD.ORDERS o
LEFT JOIN cspl_C2b_db.prod.ops_logistics ops ON ops.lead_id = o.lead_id
LEFT JOIN cspl_c2b_db.prod.spd           spd ON spd.appt_id = o.lead_id
WHERE
    c2b_lead_id IN ('GS_ASSURED')
    AND first_si::date >= '2026-05-01'
"""


def main():
    log.info('Connecting to Snowflake...')
    conn = connect()
    log.info('Connected!')

    log.info('Running query...')
    df = query(conn, TEST_SQL)
    log.info(f'Result: {len(df):,} rows  x  {len(df.columns)} columns')
    log.info(f'Columns: {list(df.columns)}')

    if len(df) > 0:
        log.info(f'\nSample (first 5 rows):\n{df.head(5).to_string(index=False)}')

    os.makedirs('output', exist_ok=True)
    out = 'output/test_result.csv'
    df.to_csv(out, index=False)
    log.info(f'Saved -> {out}')

    conn.close()
    log.info('Done.')


if __name__ == '__main__':
    main()
