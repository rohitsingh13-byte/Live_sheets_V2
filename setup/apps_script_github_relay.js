/**
 * Apps Script: GitHub → Google Sheet relay
 *
 * Setup (one-time):
 *  1. Open Google Sheet → Extensions → Apps Script → paste this file
 *  2. Project Settings (gear icon) → Script Properties → Add:
 *       GITHUB_PAT   = your GitHub personal access token (read:repo scope)
 *  3. Left menu → Triggers → Add trigger:
 *       Function: refreshFromGitHub
 *       Event source: Time-driven → Hour timer → Every hour  (or Every 30 min)
 *  4. Save + Authorize (click through the org permission dialog once)
 *
 * The function fetches data/test_result.csv from the private GitHub repo
 * using the PAT and writes it to the "Test" tab starting at A1.
 */

var REPO  = 'rohitsingh13-byte/Live_sheets_V2';
var FILE  = 'data/test_result.csv';
var SHEET = 'Test';

function refreshFromGitHub() {
  var pat = PropertiesService.getScriptProperties().getProperty('GITHUB_PAT');
  if (!pat) throw new Error('GITHUB_PAT not set in Script Properties');

  var url = 'https://api.github.com/repos/' + REPO + '/contents/' + FILE;

  var response = UrlFetchApp.fetch(url, {
    method: 'get',
    headers: {
      'Authorization': 'token ' + pat,
      'Accept': 'application/vnd.github.v3.raw'
    },
    muteHttpExceptions: true
  });

  if (response.getResponseCode() !== 200) {
    throw new Error('GitHub fetch failed: ' + response.getResponseCode() + ' ' + response.getContentText());
  }

  var rows = Utilities.parseCsv(response.getContentText());
  if (!rows || rows.length === 0) {
    Logger.log('No data returned from GitHub');
    return;
  }

  var ss    = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET);
  if (!sheet) throw new Error('Sheet "' + SHEET + '" not found');

  sheet.clearContents();
  sheet.getRange(1, 1, rows.length, rows[0].length).setValues(rows);

  Logger.log('Done: ' + (rows.length - 1) + ' rows written to ' + SHEET);
}

/** Test manually: run this once to verify before setting the trigger */
function testRun() {
  refreshFromGitHub();
}
