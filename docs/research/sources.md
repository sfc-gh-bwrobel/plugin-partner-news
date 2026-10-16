---
type: Concept
description: Verified Capgemini news feeds with volume and noise, tested 2026-10-16.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T18:00:00Z
stale_after: 2027-01-16T00:00:00Z
sources:
  - id: capgemini-feed
    resource: https://www.capgemini.com/feed/
    title: Capgemini global RSS
  - id: google-news
    resource: https://news.google.com/rss/search?q=Capgemini
    title: Google News RSS search
---

# Sources

| Feed | Status | Volume (7d) |
|---|---|---|
| capgemini.com/feed/ | Use, full text in `content:encoded` | ~5-10 |
| capgemini.com/de-de/feed/ | Use | ~1 |
| capgemini.com/fr-fr/feed/ | Optional, sparse | <1 |
| Google News EN-GB "Capgemini" | Use | 46 (12 finance noise) |
| Google News FR | Use | 53 (14 noise) |
| Google News DE | Use | 23 (17 noise) |
| capgemini.com/news/feed/, /press-releases/feed/ | Exclude, empty comment feeds | 0 |
| investors.capgemini.com/en/feed/ | Exclude, empty | 0 |

Not verified: whether every press release appears in the main feed (hence manual check).
Google News links are redirects; decoding needs the `batchexecute` call (see decision 0006).
