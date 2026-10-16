---
type: Decision
status: Accepted
description: Digest is for the internal Snowflake team working with the partner; a human reviews every digest before it is sent.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T18:00:00Z
verified:
  - by: human:bwrobel
    at: 2026-10-16T18:00:00Z
sources: []
---

# 0001 - Audience and human review

## Context
News about Capgemini helps the Snowflake people who work with Capgemini (PSE, partner managers, AEs). Content is third-party; automated sending risks noise or wrong framing.

## Decision
- Audience: internal Snowflake partner team only, not Capgemini itself.
- Every digest is a DRAFT until a human approves it. The plugin never posts or emails on its own.
- Items are headline + 1-2 line summary + link. No full article text copied.

## Consequences
- Weekly review effort (~10 min) for the owner.
- Need a backup reviewer when the owner is out (open).
