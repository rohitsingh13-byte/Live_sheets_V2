import os
import logging
import pandas as pd

log = logging.getLogger(__name__)

ACCOUNT = 'CQ31887-CARS24CSPL'
USER    = 'rohit.singh13@cars24.com'
ROLE    = 'ROHIT_SINGH13_RL'


def connect():
    """
    Connect to Snowflake. Auth priority:

    1. SNOWFLAKE_PRIVATE_KEY env var (RSA key-pair) — fully headless, never expires.
       Set as GitHub Secret. Run setup/generate_snowflake_key.py to generate.

    2. SNOWFLAKE_PAT env var (OAuth PAT) — headless if IT enables PAT auth.

    3. SSO externalbrowser — opens browser on first run, then silent via
       Windows Credential Manager cache (client_store_temporary_credential=True).
       Works for local testing. Not reliable on the runner after long sleep.
    """
    import snowflake.connector

    private_key_pem = os.environ.get('SNOWFLAKE_PRIVATE_KEY', '').strip()
    pat             = os.environ.get('SNOWFLAKE_PAT', '').strip()

    if private_key_pem:
        log.info('  auth: RSA key-pair (headless)')
        from cryptography.hazmat.primitives.serialization import (
            load_pem_private_key, Encoding, PrivateFormat, NoEncryption
        )
        pk       = load_pem_private_key(private_key_pem.encode(), password=None)
        pk_bytes = pk.private_bytes(Encoding.DER, PrivateFormat.PKCS8, NoEncryption())
        return snowflake.connector.connect(
            user=USER,
            account=ACCOUNT,
            role=ROLE,
            private_key=pk_bytes,
        )

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
