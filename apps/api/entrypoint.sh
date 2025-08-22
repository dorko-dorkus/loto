#!/bin/sh
set -e
alembic -c apps/api/alembic/alembic.ini upgrade head
exec uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
