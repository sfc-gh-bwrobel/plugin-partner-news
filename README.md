# plugin-partner-news

CoCo plugin that drafts a weekly partner news digest for internal Snowflake partner teams.

- `partners/<partner>.json` - feeds, Google News queries, noise filter, section rules
- `collect.py` - stdlib-only collector -> `raw/<partner>/<date>.json`
- `skills/partner-news/` - turns raw items into a reviewed digest in `digests/<partner>/`
- `pilot/` - first manual pilot (2026-10-16)

Run: `python3 collect.py partners/capgemini.json --days 7`, then ask CoCo for the "partner news" digest.
Nothing is sent automatically - the digest is a DRAFT until reviewed.
