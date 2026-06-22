// ─────────────────────────────────────────────────────────────────────────────
// Live Sheets V2 — Apps Script Web App
//
// SETUP (one time only):
//   1. Open ANY Google Sheet you own
//   2. Extensions → Apps Script → paste this entire file → Save
//   3. Change WRITE_SECRET below to a random string (keep it secret)
//   4. Deploy → New deployment → Web app
//        Execute as: Me
//        Who has access: Anyone
//   5. Copy the deployment URL → paste into GitHub Secret: APPSSCRIPT_URL
//   6. Copy WRITE_SECRET below → paste into GitHub Secret: APPSSCRIPT_SECRET
//
// ONE deployment covers ALL your Google Sheets — no re-deploy needed for
// new sheets. Just add a new row to config/mappings.json.
// ─────────────────────────────────────────────────────────────────────────────

var WRITE_SECRET = 'CHANGE_THIS_TO_SOMETHING_RANDOM_LIKE_abc123xyz456';


// ── doPost: write data to any sheet ─────────────────────────────────────────
function doPost(e) {
  try {
    var payload = JSON.parse(e.postData.contents);

    if (payload.secret !== WRITE_SECRET) {
      return respond({ success: false, error: 'Unauthorized' });
    }

    var ss    = SpreadsheetApp.openById(payload.sheetId);
    var sheet = ss.getSheetByName(payload.tabName);

    if (!sheet) {
      // Auto-create tab if it doesn't exist
      sheet = ss.insertSheet(payload.tabName);
    }

    var rows  = payload.rows  || [];
    var chunk = payload.chunk || 0;

    if (chunk === 0) {
      sheet.clearContents();
    }

    var startRow = sheet.getLastRow() + 1;
    if (chunk === 0) startRow = 1;

    if (rows.length > 0) {
      sheet.getRange(startRow, 1, rows.length, rows[0].length).setValues(rows);
    }

    // Bold the header row on the first chunk
    if (chunk === 0 && rows.length > 0) {
      sheet.getRange(1, 1, 1, rows[0].length).setFontWeight('bold');
    }

    return respond({ success: true, rowsWritten: rows.length });

  } catch (err) {
    return respond({ success: false, error: err.toString() });
  }
}


// ── doGet: health check ──────────────────────────────────────────────────────
function doGet(e) {
  return respond({ status: 'ok', version: 'Live_sheets_V2' });
}


// ── Helper ───────────────────────────────────────────────────────────────────
function respond(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
