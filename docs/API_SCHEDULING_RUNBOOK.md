# API Scheduling Validation Runbook

Use this short runbook to validate blueprint/schedule behavior for a single work order and to sanity-check parts gating behavior.

## Prerequisites

- API is running locally (`make run-demo` or equivalent).
- `curl` and `jq` are installed.
- Planner auth token is available in `TOKEN`.

```bash
export API_BASE_URL=http://localhost:8000
export TOKEN="dev-token"
export WORKORDER_ID="WO-1"
```

## 1) Call `/blueprint` for a work order

```bash
BLUEPRINT_JOB_ID=$(curl -sS -X POST "$API_BASE_URL/blueprint" \
  -H 'Content-Type: application/json' \
  -d "{\"workorder_id\":\"$WORKORDER_ID\"}" | jq -r '.job_id')

curl -sS "$API_BASE_URL/jobs/$BLUEPRINT_JOB_ID" | jq
```

Expected observable outcomes:

- Job status eventually becomes `done`.
- `result.steps` is non-empty for a valid work order.

## 2) Call `/schedule` for the same work order

```bash
SCHEDULE_JOB_ID=$(curl -sS -X POST "$API_BASE_URL/schedule" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"workorder\":\"$WORKORDER_ID\"}" | jq -r '.job_id')

curl -sS "$API_BASE_URL/jobs/$SCHEDULE_JOB_ID" | jq
```

Expected observable outcomes:

- Job status eventually becomes `done`.
- `result.status` is typically `feasible` for demo WO data.
- `result.provenance.plan_id` is present and can be compared with blueprint output.

## 3) Reduce staffing/capacity and re-run `/schedule`

Adjust the staffing/capacity configuration used by your deployment, restart the API, then run the same `/schedule` call again.

> Example places to tune staffing/capacity in this repo include policy/config inputs under `config/` that feed scheduler decisions in a deployment pipeline.

```bash
# Re-run after your config change + API restart
SCHEDULE_LOW_CAP_JOB_ID=$(curl -sS -X POST "$API_BASE_URL/schedule" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"workorder\":\"$WORKORDER_ID\"}" | jq -r '.job_id')

curl -sS "$API_BASE_URL/jobs/$SCHEDULE_LOW_CAP_JOB_ID" | jq
```

Expected observable outcomes:

- Under lower staffing/capacity, median completion time (`result.p50`) should increase or remain unchanged versus baseline.
- `result.p90` typically increases with lower capacity as schedule tail risk grows.

## 4) Force a parts block and verify blocked behavior

Use strict mode to force policy A behavior when parts are not available.

```bash
BLOCKED_JOB_ID=$(curl -sS -X POST "$API_BASE_URL/schedule?strict=true&parts_block_policy=B" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"workorder\":\"$WORKORDER_ID\"}" | jq -r '.job_id')

curl -sS "$API_BASE_URL/jobs/$BLOCKED_JOB_ID" | jq
```

Expected observable outcomes:

- Job status becomes `failed` if a parts block is triggered in strict mode.
- `result.error_code` is `PARTS_BLOCKED`.
- `result.missing_parts` contains one or more missing part entries (`item`, `required`, `available`, `shortfall`, `reason`).

If you want conditional scheduling output instead of hard-fail behavior, run the same request with `strict=false&parts_block_policy=B` and verify:

- `result.status == "blocked_by_parts"`
- `result.percentiles_conditional == true`
- `result.conditional_basis` is populated
