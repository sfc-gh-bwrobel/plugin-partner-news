# plugin-partner-news

CoCo plugin that drafts a weekly partner news digest for internal Snowflake partner teams.

- `partners/<partner>.json` - feeds, Google News queries, noise filter, section rules
- `collect.py` - stdlib-only collector -> `raw/<partner>/<date>.json`
- `skills/partner-news/` - turns raw items into a reviewed digest in `digests/<partner>/`
- `pilot/` - first manual pilot (2026-10-16)

## Use in CoCo

Open this repository and ask: "Read `skills/partner-news/SKILL.md` and prepare the Capgemini digest for the latest completed Monday-Sunday week." Add "prepare only, do not publish" for a preview.

The skill orchestrates collection, source verification, editorial decisions, Markdown, HTML snapshots and publication. The Python collector alone does not write or publish a digest. For a specific week, collection uses `python3 collect.py partners/capgemini.json --days 7 --end <Sunday YYYY-MM-DD>`.

## Automatic publication

Bart authorized automatic Capgemini publication on 2026-10-16. This skips per-edition approval, not validation: incomplete collection, failed checks or unavailable Drive access stop the run before the live update. Existing archived editions are never overwritten. Other partners still require approval unless explicitly authorized.

A scheduled CoCo Desktop run should read the skill, collect and publish the latest completed week, refreshing pending/unpublished cached collections and regenerating their editorial decisions. Keep the automation in this repository and use the existing Drive destination and permissions. It may resume a partially completed publication, but must not rewrite an archived edition.

Scheduling is separate from installing the plugin. Desktop automations require CoCo Desktop to be open; missed runs catch up once on reopening. This publication workflow also needs Drive access and, when using the local publishing path, Drive for Desktop sync. Tool approval settings still apply. No schedule is created by these files.

Automatic-mode gates are agent instructions, not a standalone unattended publisher. A scheduled end-to-end run remains to be tested. Run regression checks with `python3 -m unittest discover -s . -p 'test_*.py'`.
