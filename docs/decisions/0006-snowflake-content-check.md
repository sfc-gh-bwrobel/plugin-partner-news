---
type: Decision
status: Accepted
description: An item is a Snowflake mention if one article paragraph names both the partner and Snowflake; Google News links are decoded to fetch the body.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T18:00:00Z
verified:
  - by: human:bwrobel
    at: 2026-10-16T18:00:00Z
sources: []
---

# 0006 - Snowflake mentions checked in content

## Context
Snowflake is often mentioned in the body, not the headline. Raw keyword counts give false hits (Simply Wall St "Snowflake" chart, sidebar link lists).

## Decision
- capgemini.com feed items: check `content:encoded` (full text in feed).
- Hits from the Snowflake query: decode Google News link (undocumented `batchexecute` endpoint), fetch page, check.
- Rule: one `<p>` paragraph <= 800 chars contains the partner name and case-sensitive `Snowflake`. Paragraph saved as `evidence`.
- 1 s pause between decodes.

## Consequences
- 30-day test found 2 real passing mentions (HackerRank Chakra) with no title match.
- General items (~150/month) are not body-checked, to stay fast and polite.
- Decoder may break without notice; failures are logged, run continues. Some sites block (403/429) or need JavaScript.
