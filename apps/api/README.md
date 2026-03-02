# API Service

This directory contains a minimal [FastAPI](https://fastapi.tiangolo.com/) service for loto.

## Endpoints

- `GET /healthz` – readiness check reporting rate limits, adapter and database status.
- `GET /version` – return the application version.
- `POST /blueprint` – placeholder accepting a CSV upload or work order ID.
- `POST /schedule` – placeholder endpoint for creating schedules.
- `GET /workorders/{id}` – mock endpoint returning a work order.

## Setup

Install dependencies:

```bash
pip install -r apps/api/requirements.txt
```

## Running

Start the development server:

```bash
uvicorn apps.api.main:app --reload
```

OpenAPI documentation is available at `/docs`.

## Audit logging

Requests are recorded in an append-only `audit_records` table.  Run the
Alembic migrations to create the table:

```bash
alembic -c apps/api/alembic/alembic.ini upgrade head
```

Logs can be periodically exported to immutable storage.  The helper below
uploads all records to an S3 bucket with object lock enabled and retains them
for seven years:

```bash
python -m apps.api.audit my-audit-log-bucket
```

Plan a scheduled job (for example, cron) to run this command regularly.  This
implements the retention policy of keeping audit logs for seven years.

## `/schedule` response contract

The `POST /schedule` job result now follows a canonical contract:

- `status`: one of `feasible`, `blocked_by_parts`, or `failed`
- `provenance`: includes `plan_id`, `simulation_config_id`,
  `simulation_config_version`, and `random_seed` (or `seed_strategy`)

Parts-block policy:

- Default **Policy B** (`parts_block_policy=B`): returns `status=blocked_by_parts` and includes conditional percentiles marked with `percentiles_conditional=true` and `conditional_basis`.
- Optional **Policy A** (`parts_block_policy=A`): returns failure with `HTTP 409` semantics in the job result and no Monte Carlo percentiles.

Conditional fields by status:

- `feasible`: requires `p10`, `p50`, `p90`, and `expected_makespan`
  (`expected_cost` is optional when available)
- `blocked_by_parts`: requires `missing_parts` and/or `gating_reason`; when using Policy B, returned percentiles are explicitly marked conditional
- `failed`: requires `error_code` and `error_message`

The OpenAPI schema is generated from `apps/api/schemas.py::ScheduleResponse`,
which enforces these status-dependent requirements via model validation.
