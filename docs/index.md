---
okf_version: "0.2"
type: Index
description: Knowledge bundle for plugin-partner-news - decisions (ADR-style) and research facts.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T18:00:00Z
---

# plugin-partner-news knowledge

How to read: `decisions/` are ADRs (`type: Decision`, status Proposed / Accepted / Superseded, never edited after Accepted - supersede instead). `research/` are facts that expire (`type: Concept`, check `stale_after`).

## Decisions
| # | Decision | Status |
|---|---|---|
| [0001](decisions/0001-audience-and-human-review.md) | Internal partner team audience, human review before sending | Accepted |
| [0002](decisions/0002-sources.md) | Partner RSS + Google News EN/FR/DE; LinkedIn manual | Accepted |
| [0003](decisions/0003-tooling-no-paid-search.md) | Stdlib Python + CoCo, no Tavily | Accepted |
| [0004](decisions/0004-generic-plugin.md) | Generic CoCo plugin with per-partner config | Accepted |
| [0005](decisions/0005-targeted-sections.md) | Snowflake / competitors / leadership sections | Accepted |
| [0006](decisions/0006-snowflake-content-check.md) | Snowflake mentions checked in article body | Accepted |
| [0007](decisions/0007-llm-relevance-judge.md) | Script collects, LLM judges relevance | Accepted |
| [0008](decisions/0008-cadence-and-runtime.md) | Weekly Monday digest via Desktop automation | Accepted |
| [0009](decisions/0009-delivery.md) | Two-week solo run, then #capgemini-global-partner | Accepted |
| [0010](decisions/0010-subsidiaries-wns-kipi.md) | Track WNS and Kipi.ai as Capgemini subsidiaries | Accepted |
| [0011](decisions/0011-drive-viewer-apps-script.md) | Drive folder + Apps Script viewer | Superseded by 0012 |
| [0012](decisions/0012-static-page-apps-script.md) | Static page, Apps Script serves the Drive file | Accepted |

## Research
- [Sources](research/sources.md) - verified feeds and their volume
- [Tooling](research/tooling.md) - search / LinkedIn / Snowflake options evaluated
- [Prior art](research/prior-art.md) - similar efforts inside Snowflake
- [Filter quality](research/filter-quality.md) - measured regex precision (2026-10-16)
