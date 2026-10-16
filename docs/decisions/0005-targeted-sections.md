---
type: Decision
status: Accepted
description: Add targeted queries and digest sections for Snowflake mentions, competitor partnerships and leadership changes.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T18:00:00Z
verified:
  - by: human:bwrobel
    at: 2026-10-16T18:00:00Z
sources: []
---

# 0005 - Targeted sections

## Context
A generic partner feed misses what a Snowflake partner team cares about most.

## Decision
- Extra Google News queries: Capgemini + Snowflake, Capgemini + (Databricks, Microsoft Fabric, BigQuery, Palantir), Capgemini + appointments.
- Google News matches loosely, so section is assigned from the title (`section_title_regex`) and the title must contain the partner name. Non-matching hits from targeted queries are dropped.
- Priority: snowflake > competitors > leadership > general.

## Consequences
- 30-day test: 4 leadership items, 0 competitor, 0 Snowflake by title.
- Title rules are brittle; superseded in part by [0006](0006-snowflake-content-check.md) and [0007](0007-llm-relevance-judge.md).
- Deferred: news about Capgemini at our accounts (needs account list), M&A section, extra languages.
