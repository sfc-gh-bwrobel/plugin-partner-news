/**
 * Partner news digest - Google Apps Script web app (set up once).
 *
 * Serves the static page PAGE_NAME from FOLDER_ID. The page is pre-built
 * (build_site.py) with all weeks inside, so replacing that one Drive file
 * updates the site. Looked up by name, so a re-uploaded file keeps working.
 *
 * Deploy: Web app, Execute as: Me, Who has access: Anyone within Snowflake.
 */
const FOLDER_ID = '1ePyr-PclAiCu3f94X0Utx9htXrgIpmWg';
const PAGE_NAME = 'capgemini-news.html';

function doGet() {
  const pages = DriveApp.getFolderById(FOLDER_ID).getFilesByName(PAGE_NAME);
  if (!pages.hasNext()) return HtmlService.createHtmlOutput('Page ' + PAGE_NAME + ' not found in the Drive folder.');
  return HtmlService.createHtmlOutput(pages.next().getBlob().getDataAsString('UTF-8'))
    .setTitle('Capgemini news digest')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}
