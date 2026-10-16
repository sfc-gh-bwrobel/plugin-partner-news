---
type: Decision
status: Accepted
description: Track Capgemini subsidiaries WNS and Kipi.ai inside the Capgemini config, as aliases and a dedicated digest section.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T19:00:00Z
verified:
  - by: human:bwrobel
    at: 2026-10-16T19:30:00Z
sources:
  - id: az4c-release
    resource: https://natlawreview.com/press-releases/az4cai-brings-ai-agents-data-and-governance-together-enterprises
    title: AZ4C.AI release (states Kipi.ai was acquired by WNS in 2025)
  - id: kipi-poy
    resource: https://www.kipi.ai/insights/blog/kipi-ai-named-2026-snowflake-global-telecom-partner-of-the-year
    title: Kipi.ai named 2026 Snowflake Global Telecom Partner of the Year
---

# 0010 - Track WNS and Kipi.ai as Capgemini subsidiaries

## Context
Capgemini acquired WNS; WNS acquired Kipi.ai (Snowflake-focused SI) in 2025. WNS now brands as "WNS - Part of Capgemini". Neither site has RSS or a sitemap (404, checked 2026-10-16).

## Decision
- Same config as Capgemini (one partner relationship), not a separate partner file.
- `aliases_regex` = Capgemini | WNS | Kipi: these names count as "about the partner" for all targeted sections and the Snowflake body check.
- New section `subsidiaries` (priority after `snowflake`), fed by Google News queries `"Kipi.ai" OR site:kipi.ai`, `"WNS" Capgemini OR site:wns.com`, and `(Kipi OR WNS) Snowflake`.
- Capgemini feed articles whose text mentions Kipi or WNS also go to `subsidiaries`, with the paragraph as evidence.

## Consequences
- 30-day test: Kipi Telecom POY in Snowflake section; 3 WNS marketing/event pages; 0 Capgemini articles mentioning Kipi/WNS.
- Kipi volume is very low (~1 item/quarter); kipi.ai blog is not otherwise monitored.
- WNS site pages are mostly marketing - relies on the LLM judge (0007) to drop them.
- Founder spin-off news (Seroda Ventures, AZ4C.AI) shows up via "Kipi.ai" mentions - keep as "also noted".
