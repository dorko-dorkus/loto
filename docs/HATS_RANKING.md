# HATS Ranking

This document describes how the Historical Asset Triage Score (HATS) ranking is defined and used.

Reviewed by Ops and Safety on 2024-05-27.

## Key Performance Indicators (KPIs)
- **Reliability**: fraction of runs executed without incident.
- **Throughput**: jobs completed per scheduling window.
- **Quality**: percentage of jobs meeting acceptance criteria.

## Ranking Math
Each KPI is normalized to a value between 0 and 1. The composite score is the weighted sum:

```
score = w_r * reliability + w_t * throughput + w_q * quality
```

Weights `w_r`, `w_t`, and `w_q` must sum to 1. The final rank is `round(100 * score)`.

## Guardrails
- Any KPI below 0.4 causes the rank to be capped at 20.
- Scores are recomputed daily and require at least 30 samples.
- Manual overrides require sign-off from Ops and Safety.

## Tuning
Weights are configured in `config/hats.json`. To adjust:
1. Propose new weights and rationale.
2. Obtain approval from Ops and Safety.
3. Update the configuration and restart the scheduler.

## Use in Scheduling
Scheduler jobs are sorted by descending HATS rank. Higher-ranked jobs receive earlier execution slots, while ties are broken by submit time.

