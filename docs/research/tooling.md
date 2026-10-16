---
type: Concept
description: Evaluated options for search, LinkedIn, datasets and scheduling.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T18:00:00Z
stale_after: 2027-01-16T00:00:00Z
sources:
  - id: tavily-pricing
    resource: https://tavily.com/
    title: Tavily
---

# Tooling

- **Tavily**: free 1000 credits/month, then $0.008/credit (basic search 1, advanced 2). Not needed at current volume.
- **CoCo web search**: built in (Brave-backed). Good for ad-hoc verification.
- **LinkedIn**: Posts API needs `r_organization_social` with page admin role; no general feed access.
- **Ekkow Global News Agency Dataset** (Marketplace `GZ2FTZNPJK3`): no confirmed Snowflake users; Mar 2026 review found its Cortex Search suspended. Contact: Ben Srour.
- **Scheduling**: CoCo Desktop automation (local, app must be open); Snowflake-hosted CoCo automation (Preview, cloud sandbox, hourly min, allowlisted egress, no external access integrations, default role); CoWork automations (email delivery of recurring questions).
- **Snowflake AI functions** (AI_FILTER, AI_CLASSIFY): option for relevance if data moves into Snowflake.
