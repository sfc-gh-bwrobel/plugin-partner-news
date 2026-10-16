---
type: Decision
status: Accepted
description: Monitor partner website RSS and Google News RSS in EN/FR/DE; LinkedIn, press releases and investor calendar are manual checks.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T18:00:00Z
verified:
  - by: human:bwrobel
    at: 2026-10-16T18:00:00Z
sources:
  - id: research-sources
    resource: ../research/sources.md
    title: Verified feeds
---

# 0002 - Sources

## Context
Wanted: partner website, LinkedIn, third-party mentions. See [research/sources.md](../research/sources.md).

## Decision
- Automated: `capgemini.com/feed/`, `/de-de/feed/`, Google News RSS search EN-GB, FR, DE.
- Manual checks listed in every digest: LinkedIn page, press-release page, investor calendar.
- Not used: Ekkow Global News Agency dataset (no confirmed users, search service was suspended), `/news/feed/` and IR feed (empty).

## Consequences
- LinkedIn-only posts are missed; most mirror website news.
- Other languages (India, Spain, Italy, NL, Nordics) not covered yet.
- Google News is an unofficial, free source and may change.
