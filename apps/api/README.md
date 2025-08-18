# API Service

This directory contains a minimal [FastAPI](https://fastapi.tiangolo.com/) service for loto.

## Endpoints

- `GET /healthz` – basic health check (excluded from OpenAPI schema).
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

OpenAPI documentation is available at `/docs` and lists the three placeholder endpoints.
