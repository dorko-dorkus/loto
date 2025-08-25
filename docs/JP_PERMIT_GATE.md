# Job Plan JP_PERMIT_GATE

This job plan enforces permit gating for work orders requiring an active permit.

## Tasks

| Seq | Description | Type |
| --- | ----------- | ---- |
| 10 | Permit Active | YORN |
| 20 | Isolation boundary verified (photo required) | YORN |
| 30 | Permit Closed & Hand-back uploaded | YORN |

## Planner instructions

- Add `JP_PERMIT_GATE` to work order templates or workflow steps so new work orders automatically include these tasks.
- Confirm the isolation boundary photo is attached before marking the permit verified.
- Upload permit closeout and hand-back documentation to satisfy the final task.
