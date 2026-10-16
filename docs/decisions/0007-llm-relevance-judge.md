---
type: Decision
status: Accepted
description: Script collects and dedupes; the LLM decides keep/drop, clusters stories and ranks, writing a reason per item.
generated:
  by: cortex-code/claude-opus-5-5
  at: 2026-10-16T18:00:00Z
verified:
  - by: human:bwrobel
    at: 2026-10-16T19:30:00Z
sources:
  - id: filter-quality
    resource: ../research/filter-quality.md
    title: Measured regex filter quality
---

# 0007 - LLM judges relevance

## Context
Regex filter: ~96% correct on drops but only ~40% of kept items worth reading; cannot merge same story with different headlines (automotive report appeared 7 times). See [research/filter-quality.md](../research/filter-quality.md).

## Decision
- `collect.py`: fetch, decode, exact dedupe, Snowflake body check, minimal noise regex (obvious stock-ticker spam only; fix `cours`/`hausse` false drops).
- Skill step: LLM reads raw items, writes `raw/<partner>/<date>.judged.json` with keep/drop, cluster id, section, one-line reason.
- Digest built only from kept clusters. Dropped list reviewed by a human during the trial.

## Alternatives
- Regex only: cheap, but low precision and no clustering.
- Snowflake AI_FILTER / AI_CLASSIFY: good once data lives in Snowflake; overkill for one partner now.

## Consequences
- One LLM pass per week (~75-180 titles); results vary slightly run to run, mitigated by written reasons.
