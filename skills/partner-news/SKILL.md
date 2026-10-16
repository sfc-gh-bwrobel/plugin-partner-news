---
name: partner-news
description: Weekly partner news digest for the internal Snowflake partner team. Collects partner website RSS + Google News (EN/FR/DE), filters finance noise, and drafts a reviewed digest. Use when: partner news, Capgemini news, weekly digest, news digest. Triggers: partner news, capgemini news, news digest, weekly news.
---

# Partner news digest

## Steps
1. Pick the partner config in `partners/` (default `capgemini.json`).
2. Run `python3 collect.py partners/<partner>.json --days 7` from the plugin root.
   Output: `raw/<partner>/<YYYY-MM-DD>.json` with `items[]` (section, title, date, publisher, link), `stats`, `manual_checks`.
3. Read the raw file and write `digests/<partner>/digest-<YYYY-MM-DD>.md` using the template below.
   - Merge items that cover the same story (different titles, same event).
   - Resolve Google News redirect links to the publisher URL for every item you keep (web search the title).
   - Headline + 1-2 line summary + link only. Never paste full article text.
   - Hyphens, not em-dashes. Status line stays `DRAFT`.
4. Show the draft to the user and STOP. Do not send or post anything without explicit approval.

## Template
```
# <Partner> news - week of <dates>
Status: DRAFT | Sources: <n> raw, <n> kept

## Snowflake mentions
<items, or "None this week.">

## Subsidiaries (WNS, Kipi.ai)
<items, or "None this week.">

## Top stories (max 6)
### <n>. <headline>
<summary>
- Why it matters: <one line for a Snowflake partner team>
- Follow-up: <optional action>
- Source: <link>

## People & org changes
<items, or "None this week.">

## Competitor partnerships (Databricks, Fabric, BigQuery, ...)
<items, or "None this week.">

## Coming up
<dated events, earnings>

## Also noted
<one-liners>

## Manual checks
<from raw manual_checks - LinkedIn, press releases, investor calendar>
```

## Notes
- `snowflake` section is content-based: an item lands there if one article paragraph mentions both the partner and "Snowflake" (capgemini.com feeds carry full text; Google News hits from the Snowflake query are decoded and fetched). `evidence` holds that paragraph - quote it as the reason. Rate the mention: core (partnership/joint deal) vs passing (listed among others).
- Other sections are assigned from the title: `snowflake` > `competitors` > `leadership` > `general`. Targeted sections require the partner name in the title.
- Add a partner by copying `partners/capgemini.json` and editing name, feeds, queries.
