---
type: Concept
description: Measured quality of the regex noise filter on 7 days of Capgemini news, 2026-10-16.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T18:00:00Z
stale_after: 2026-11-16T00:00:00Z
sources: []
---

# Filter quality (7 days, 2026-10-16)

- Raw 189, dropped as noise 50, kept 74.
- Drops: ~48/50 correct (share-price spam). False drops: "course à l'IA" matched `cours`; Q1 revenue headline matched `hausse`.
- Kept: ~30/74 worth reading. Leaks: Boursier "gagne/prend x%", analyst price targets, treasury-share filings, earnings-call transcript, World Rugby, Ukraine data centres, unrelated appointments.
- Duplicates by story: automotive agentic-AI report x7, green-card freeze x6.

Judgement by cortex-code, not human-reviewed. Re-measure after decision 0007.

## After decision 0007 (same week, 2026-10-16)
- Collector with trimmed regex: raw 191, noise 31, kept 96.
- LLM judge: 31 kept in 11 stories, 65 dropped with reasons (`raw/capgemini/2026-10-16.judged.json`). Biggest drop groups: share price/analyst ratings (~30), low-signal thought leadership (~13), career/employer pages, unrelated.
- Fixed false drops: "course a l'IA" article now kept (auto report cluster); Q1 revenue headline reached the judge and was dropped as stale (April).
