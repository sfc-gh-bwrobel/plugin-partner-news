---
name: partner-news
description: Weekly partner news digest for the internal Snowflake partner team. Collects partner website RSS + Google News (EN/FR/DE), filters finance noise, and drafts a reviewed digest. Use when: partner news, Capgemini news, weekly digest, news digest. Triggers: partner news, capgemini news, news digest, weekly news.
---

# Partner news digest

## Steps
1. Pick the partner config in `partners/` (default `capgemini.json`).
2. Run `python3 collect.py partners/<partner>.json --days 7` from the plugin root.
   Output: `raw/<partner>/<YYYY-MM-DD>.json` with `items[]` (id, section, title, date, publisher, link, evidence), `stats`, `manual_checks`.
   If today's file exists it is reused (no rescan). Use `--refresh` only when the user asks.
3. **Judge** (decision 0007). Read every raw item and write `raw/<partner>/<YYYY-MM-DD>.judged.json`:
   ```json
   {"judged_by": "cortex-code/<model>", "items": [
     {"id": 12, "keep": true, "cluster": "auto-agentic-report", "section": "top", "score": 3,
      "reason": "Capgemini Research Institute report, wide pickup"}]}
   ```
   - One entry per raw id, kept or dropped, each with a short reason.
   - `cluster`: same slug for items about the same story. Keep the most authoritative source as the cluster lead (partner site > tier-1 press > rest).
   - `section`: snowflake | subsidiaries | top | people | competitors | coming_up | also_noted.
   - `score` 1-3 (3 = act on / tell the team).
   - If the judged file already exists, reuse it - do not judge again unless asked.
4. Resolve the link of every kept cluster lead that is still a `news.google.com` redirect (`collect.decode_google_news`, or web search the title). Store resolved links back into the judged file.
5. Write `digests/<partner>/digest-<YYYY-MM-DD>.md` from kept clusters only, using the template.
   - Headline + 1-2 line summary + link only. Never paste full article text.
   - Hyphens, not em-dashes. Status line stays `DRAFT`. Never invent items.
6. Show the draft and the dropped list (titles + reasons) to the user and STOP. Do not send or post anything without explicit approval.

## Judging rubric
Keep:
- Partnerships and integrations, especially with Snowflake, Databricks, hyperscalers, SAP, ServiceNow.
- Client wins, large deals, public-sector contracts.
- Acquisitions, divestments, funding.
- Leadership and organisation changes at the partner (not ex-employees elsewhere).
- Analyst recognition (Gartner, Forrester, IDC, HFS, Everest).
- Partner research reports with wide pickup (keep one cluster lead).
- Earnings and guidance (headline numbers only), security incidents, regulatory issues hitting the partner.

Drop:
- Share-price moves, analyst price targets, buyback and own-share filings, trading products.
- Listicles, generic PR without substance, recycled or regurgitated news.
- Articles where the partner is only one name in a long list.
- Career profiles, job ads, event sponsorship fluff, unrelated topics.
- Same-story duplicates beyond the cluster lead.

Be strict: a weekly digest with 4-8 kept clusters is normal; zero in a section is fine.

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
- Raw `section` is a hint from the collector; the judged `section` wins.
- `snowflake` section is content-based: an item lands there if one article paragraph mentions both the partner and "Snowflake" (capgemini.com feeds carry full text; Google News hits from the Snowflake query are decoded and fetched). `evidence` holds that paragraph - quote it as the reason. Rate the mention: core (partnership/joint deal) vs passing (listed among others).
- Other sections are assigned from the title: `snowflake` > `competitors` > `leadership` > `general`. Targeted sections require the partner name in the title.
- Add a partner by copying `partners/capgemini.json` and editing name, feeds, queries.
