/**
 * Partner news digest viewer - Google Apps Script web app (set up once).
 *
 * The page itself is a normal Drive file (PAGE_NAME in FOLDER_ID): edit or
 * replace it in Drive and the site updates - no need to open Apps Script.
 * Digests are digest-YYYY-MM-DD.md files in the same folder, read on every visit.
 *
 * Deploy: Web app, Execute as: Me, Who has access: Anyone within Snowflake.
 * Viewers do not need access to the folder (script runs as the owner).
 */
const FOLDER_ID = '1ePyr-PclAiCu3f94X0Utx9htXrgIpmWg';
const PAGE_NAME = 'partner-news.html';
const TITLE = 'Capgemini news digest';
const DIGEST_NAME = /^digest-(\d{4}-\d{2}-\d{2})\.md$/;

function doGet() {
  // Looked up by name, not ID, so a replaced/re-uploaded page keeps working.
  const pages = DriveApp.getFolderById(FOLDER_ID).getFilesByName(PAGE_NAME);
  if (!pages.hasNext()) return HtmlService.createHtmlOutput('Page file ' + PAGE_NAME + ' not found.');
  return HtmlService.createHtmlOutput(pages.next().getBlob().getDataAsString('UTF-8'))
    .setTitle(TITLE)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/** Newest first: [{id, date}] - called from the page via google.script.run */
function listDigests() {
  const files = DriveApp.getFolderById(FOLDER_ID).getFiles();
  const out = [];
  while (files.hasNext()) {
    const f = files.next();
    const m = f.getName().match(DIGEST_NAME);
    if (m && !f.isTrashed()) out.push({ id: f.getId(), date: m[1] });
  }
  return out.sort((a, b) => b.date.localeCompare(a.date));
}

/** Markdown text of one digest; only files listed from FOLDER_ID are served. */
function getDigest(id) {
  const allowed = listDigests().some(d => d.id === id);
  if (!allowed) throw new Error('Unknown digest');
  return DriveApp.getFileById(id).getBlob().getDataAsString('UTF-8');
}
