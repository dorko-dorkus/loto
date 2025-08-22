.PHONY: fmt lint typecheck test run-demo demo-up check-prereqs

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
	@COMPOSE="docker compose"; \
	if docker compose version >/dev/null 2>&1; then \
	COMPOSE="docker compose"; \
	elif command -v docker-compose >/dev/null 2>&1; then \
	COMPOSE="docker-compose"; \
	else \
	echo "Docker Compose is not installed. Install Docker and Docker Compose."; \
	exit 1; \
	fi; \
	$$COMPOSE up --build -d; \
	end_time=$$(($(date +%s)+30)); \
	until curl --silent --fail http://localhost:8000/healthz >/dev/null 2>&1; do \
	[ $$(date +%s) -ge $$end_time ] && { echo "Health check failed"; exit 1; }; \
	sleep 1; \
	done; \
	if command -v xdg-open >/dev/null 2>&1; then \
	xdg-open http://localhost:3000; \
	elif command -v open >/dev/null 2>&1; then \
	open http://localhost:3000; \
	fi; \
	$$COMPOSE logs -f

check-prereqs:
	./scripts/check-prereqs.sh
