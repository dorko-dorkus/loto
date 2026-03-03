# Step 3 Schedule Smoke Test Checklist

Use this script for a quick stakeholder demo of scheduling behavior.

## Preconditions
- API is reachable and seeded with a Work Order (WO) that has **multiple isolation actions**.
- You have an auth method/token ready for `/blueprint` and `/schedule` calls.

## 1) Pick a WO with multiple isolation actions
- Select a WO known to generate more than one lockout/isolation task.
- Record the WO id here: `WO_ID=__________`

## 2) Verify `/blueprint` returns multiple steps
- Call `/blueprint` for `WO_ID`.
- Confirm the response contains **multiple steps/actions** (not a single-step plan).
- Record result: step count = `_____`.

## 3) Baseline `/schedule` with default caps
- Call `/schedule` using default `resource_caps`.
- Capture schedule distribution metrics:
  - `p10 = _____`
  - `p50 = _____`
  - `p90 = _____`
- Expected: returns a feasible baseline distribution for the selected WO.

## 4) Compare with tighter and looser `resource_caps`
Run `/schedule` two more times for the same WO:

- **Tighter caps** (fewer resources than default)
  - Record: `p10 = _____`, `p50 = _____`, `p90 = _____`
  - Expected: durations generally shift **up** (later/slower outcomes).

- **Looser caps** (more resources than default)
  - Record: `p10 = _____`, `p50 = _____`, `p90 = _____`
  - Expected: durations generally shift **down** (earlier/faster outcomes).

## 5) Demo narrative (expected outcomes language)
Use this wording during stakeholder walkthrough:

- **Blocked**: "Given current constraints, the schedule is blocked/unfeasible for this WO."  
  (No feasible plan or hard conflicts remain.)
- **Feasible**: "A feasible schedule exists under current constraints, with p10/p50/p90 showing likely completion range."
- **Staffing tradeoff**: "When staffing/resource caps are tighter, completion risk and duration increase; when caps are looser, timeline improves. This shows the staffing-vs-delivery tradeoff."

## Pass criteria
- `/blueprint` shows multiple steps.
- Three `/schedule` runs completed (default, tighter, looser).
- Observed distribution shift matches expectation (tighter => slower, looser => faster), or deviations are noted with rationale.
