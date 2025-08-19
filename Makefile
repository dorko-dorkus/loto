.PHONY: fmt lint typecheck test run-demo demo-up

fmt:
	black loto tests
	isort loto tests

lint:
	ruff check loto tests

typecheck:
	mypy loto

test:
	pytest

run-demo:
	python -m loto.cli --demo

demo-up:
	@if docker compose version >/dev/null 2>&1; then \
		docker compose up --build -d; \
	elif command -v docker-compose >/dev/null 2>&1; then \
		docker-compose up --build -d; \
	else \
		echo "Docker Compose is not installed. Install Docker and Docker Compose."; \
		exit 1; \
	fi
