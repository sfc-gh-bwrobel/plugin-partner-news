---
type: Decision
status: Accepted
description: Build a generic CoCo plugin; each partner is one JSON config in partners/.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T18:00:00Z
verified:
  - by: human:bwrobel
    at: 2026-10-16T18:00:00Z
sources: []
---

# 0004 - Generic plugin, per-partner config

## Context
Repo is `plugin-partner-news`. Other PSEs could reuse it for Accenture, Deloitte, etc.

## Decision
- `partners/<partner>.json`: feeds, Google News queries and locales, noise regex, section rules, manual checks.
- `collect.py` and `skills/partner-news/SKILL.md` contain no partner-specific logic.
- Output: `raw/<partner>/<date>.json` (gitignored), `digests/<partner>/`.

## Consequences
- Adding a partner = copy and edit one file, then tune for a week.
