---
type: Decision
status: Accepted
description: Use stdlib Python for collection and CoCo for judgement and writing; no Tavily or other paid search API.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T18:00:00Z
verified:
  - by: human:bwrobel
    at: 2026-10-16T18:00:00Z
sources:
  - id: research-tooling
    resource: ../research/tooling.md
    title: Tooling evaluation
---

# 0003 - Tooling, no paid search

## Context
Options: Tavily, CoCo web search (Brave-backed), RSS, Snowflake Marketplace datasets. See [research/tooling.md](../research/tooling.md).

## Decision
RSS covers the volume (~75-180 items/week) for free. Collector is Python standard library only (no installs). CoCo web search used ad hoc to resolve or verify top stories.

## Consequences
- No API keys or vendor approval needed.
- Revisit Tavily if more partners or full-text search are needed.
