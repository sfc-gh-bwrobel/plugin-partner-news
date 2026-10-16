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

## Consequences
- Weekly update = rebuild + replace one Drive file; no Apps Script changes.
- Page also works opened directly from disk.
- `digest-*.md` files in Drive are no longer required (kept as archive).
- Option: `clasp` could push `Code.gs` from the repo; not needed while the script stays this small.
