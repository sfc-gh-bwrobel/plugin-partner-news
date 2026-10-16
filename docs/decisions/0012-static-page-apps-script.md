---
type: Decision
status: Accepted
description: Build one static HTML page with all weeks pre-rendered; Apps Script only serves that Drive file. Supersedes 0011.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T20:30:00Z
verified:
  - by: human:bwrobel
    at: 2026-10-16T20:30:00Z
sources:
  - id: drive-folder
    resource: https://drive.google.com/drive/folders/1ePyr-PclAiCu3f94X0Utx9htXrgIpmWg
    title: Digest folder (Capgemini)
---

# 0012 - Static page served by Apps Script

## Context
The dynamic viewer (0011: page lists and parses digest files at runtime) did not work when served from a Drive file. Static is simpler and has fewer moving parts.

## Decision
- `build_site.py <partner>` renders every `digests/<partner>/digest-*.md` to HTML at build time into `site/<partner>-news.html` (self-contained: inline CSS, a week picker that only shows/hides pre-rendered sections, no runtime loading or Markdown parsing).
- The page is uploaded to the Drive folder as `<partner>-news.html`.
- `apps-script/Code.gs` only has `doGet`, serving that file looked up by name in the folder. Deploy once: Execute as Me, Anyone within Snowflake.

## Deployment
Web app: https://script.google.com/a/macros/snowflake.com/s/AKfycbzyCkooeR8mRfkbeV6964bScg6vcdmoMoAah8ANNmt10jsNuSvn4Q24VLGiA1VK40IT_w/exec

## Consequences
- Weekly update = rebuild + replace one Drive file; no Apps Script changes.
- Page also works opened directly from disk.
- `digest-*.md` files in Drive are no longer required (kept as archive).
- `Code.gs` and `appsscript.json` (web app: execute as owner, domain access, drive.readonly) are managed with clasp from `apps-script/`: `npx @google/clasp push -f` then `npx @google/clasp create-deployment -i <deploymentId>` keeps the same /exec URL. Only needed when the script changes, not for new weeks.
