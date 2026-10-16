---
type: Decision
status: Accepted
description: Weekly digest drafted Monday 08:00 by a CoCo Desktop automation; same-day alerts deferred.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T18:00:00Z
verified:
  - by: human:bwrobel
    at: 2026-10-16T19:30:00Z
sources: []
---

# 0008 - Cadence and runtime

## Context
Volume: website ~6/week, Google News ~75 kept/week. Most news is not urgent.

## Decision
- Weekly digest, Monday 08:00 local, drafted by a CoCo Desktop automation.
- Same-day alerts for Snowflake mentions: later, once the weekly flow is stable.

## Alternatives
- Snowflake-hosted CoCo automation (Preview): runs with the laptop off, but sandbox egress is allowlisted; Google News and publisher sites likely blocked. Untested.

## Consequences
- Needs CoCo Desktop open and Mac awake; a missed run catches up once at next start.
