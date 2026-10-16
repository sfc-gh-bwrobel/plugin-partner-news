---
type: Decision
status: Accepted
description: Publish approved digests as Markdown files in a Drive folder and view them through a Google Apps Script web app that reads the folder on every visit.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T20:00:00Z
verified:
  - by: human:bwrobel
    at: 2026-10-16T20:00:00Z
sources:
  - id: drive-folder
    resource: https://drive.google.com/drive/folders/1ePyr-PclAiCu3f94X0Utx9htXrgIpmWg
    title: Digest folder (Capgemini)
---

# 0011 - Drive folder + Apps Script viewer

## Context
Wanted: one HTML page in Google Drive that shows each week's digest and picks up new weeks automatically. A plain HTML file cannot read private Drive files without an OAuth client; the static Apps Script recipe would need a re-paste every week.

## Decision
- Approved digests are uploaded as `digest-YYYY-MM-DD.md` into the folder in `drive_folder_id`.
- `apps-script/Code.gs` lists and reads those files at request time (`DriveApp`); the page `partner-news.html` is a normal file in the same Drive folder, loaded by `doGet` by name (edit or replace it in Drive, no Apps Script editing). It has a week picker and a small built-in Markdown renderer (escapes HTML, links only http/https).
- Deploy once as Web app: Execute as Me, access Anyone within Snowflake. Not public.
- No `XFrameOptionsMode.ALLOWALL` unless embedding in Google Sites is needed.

## Consequences
- New week = upload one file; no redeploy. Code changes need a new deployment version.
- Viewers see what the owner's script can read; `getDigest` serves only files listed from the folder.
- One-time paste of `Code.gs` into an Apps Script project (no Apps Script API access from CoCo); afterwards only Drive files change.
- Org-wide web app access may be restricted by Workspace admin policy - verify on deploy.
