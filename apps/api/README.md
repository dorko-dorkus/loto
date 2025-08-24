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
