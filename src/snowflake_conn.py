import os
import logging
import pandas as pd

log = logging.getLogger(__name__)

ACCOUNT = 'CQ31887-CARS24CSPL'
USER    = 'rohit.singh13@cars24.com'
ROLE    = 'ROHIT_SINGH13_RL'


def connect():
    """
    Connect to Snowflake.

    - On your local PC (self-hosted runner): uses externalbrowser SSO.
      After the FIRST browser login, the token is cached in Windows Credential
      Manager via client_store_temporary_credential=True, so all future runs
      are silent — no browser popup — until the token expires (8–24 hrs).

    - If SNOWFLAKE_PAT env var is set (optional IT-enabled feature):
      uses OAuth PAT instead — fully headless, never opens a browser.
    """
    import snowflake.connector

    pat = os.environ.get('SNOWFLAKE_PAT', '').strip()
    if pat:
        log.info('  auth: PAT (headless)')
        return snowflake.connector.connect(
            user=USER,
            account=ACCOUNT,
            role=ROLE,
            authenticator='oauth',
            token=pat,
        )

    log.info('  auth: SSO externalbrowser (browser opens only if token expired)')
    return snowflake.connector.connect(
        user=USER,
        account=ACCOUNT,
        role=ROLE,
        authenticator='externalbrowser',
        client_store_temporary_credential=True,
        login_timeout=120,
    )


def query(conn, sql: str) -> pd.DataFrame:
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]
    cur.close()
    return pd.DataFrame(rows, columns=cols)
