ERROR_MAP = {
    'auth_expired': [
        'jwt', 'token expired', '250001', 'token is no longer valid',
        'authentication token', 'id token', 'session has expired',
    ],
    'permission': [
        'insufficient privileges', 'permission denied', 'access denied',
        '003001', '090070', 'not authorized',
    ],
    'query_error': [
        'sql compilation error', 'syntax error', 'invalid identifier',
        'object does not exist', 'unknown database', 'unknown schema',
    ],
    'connection': [
        'network error', 'connection refused', 'connection timed out',
        'socket', 'unreachable', 'failed to connect', 'eof occurred',
    ],
    'sheets_limit': [
        '10,000,000', 'cell limit', 'exceeds the limit', 'too many cells',
    ],
    'sheets_perm': [
        'forbidden', '403', 'script error', 'unauthorized',
        'not permitted to call', 'deployment',
    ],
    'invalid_id': [
        'invalid spreadsheet id', 'no item with the given id',
        'spreadsheet not found', 'file not found',
    ],
    'missing_tab': [
        'unable to find worksheet', 'sheet not found', 'no worksheet',
        'could not find', 'does not have a tab',
    ],
    'quota': [
        'quota exceeded', 'rate limit', '429', 'too many requests',
        'user rate limit',
    ],
    'data_type': [
        'value must be', 'cannot convert', 'invalid value', 'not serializable',
    ],
}

ACTIONS = {
    'auth_expired': (
        'Token expired. Re-run: python run.py --slot XX:XX '
        '(browser will open for SSO login, then it continues automatically).'
    ),
    'permission': (
        'Your Snowflake role lacks access to this table. '
        'Ask the data platform team: GRANT SELECT ON TABLE <name> TO ROLE ROHIT_SINGH13_RL.'
    ),
    'query_error': (
        'SQL error in the query for this mapping. '
        'Check config/mappings.json → snowflake_query field for typos or missing table names.'
    ),
    'connection': (
        'Network issue or Snowflake is unreachable. '
        'Check your internet connection and retry. Run test_connection.py to verify.'
    ),
    'sheets_limit': (
        'This Google Sheet has reached the 10M cell limit. '
        'Reduce the data range in the query or split into multiple sheets.'
    ),
    'sheets_perm': (
        'Apps Script permission error. '
        'Re-deploy the web app (Extensions → Apps Script → Deploy → Manage → Redeploy) '
        'and update APPSSCRIPT_URL in GitHub Secrets.'
    ),
    'invalid_id': (
        'Invalid Google Sheet ID. '
        'Check the sheet_url in config/mappings.json — open the URL in a browser to verify it still exists.'
    ),
    'missing_tab': (
        'Tab not found. '
        'The tab_name in config/mappings.json must exactly match the tab in the sheet (case-sensitive).'
    ),
    'quota': (
        'Google Sheets API quota exceeded. '
        'Spread sheets across different time slots in config/mappings.json to reduce concurrent calls.'
    ),
    'data_type': (
        'A value in the query result cannot be serialized. '
        'Add CAST(column AS VARCHAR) in the query for columns with unusual types.'
    ),
    'unknown': (
        'Unexpected error. '
        'Check the full log in the logs/ folder or GitHub Actions run output for the complete stack trace.'
    ),
}


def classify(exc: Exception) -> str:
    msg = str(exc).lower()
    for error_type, keywords in ERROR_MAP.items():
        if any(kw in msg for kw in keywords):
            return error_type
    return 'unknown'


def suggest(error_type: str) -> str:
    return ACTIONS.get(error_type, ACTIONS['unknown'])
