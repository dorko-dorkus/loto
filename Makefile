.PHONY: fmt lint typecheck test run-demo demo-up demo-down check-prereqs seed-demo

fmt:
	black loto apps/api tests
	isort loto apps/api tests

lint:
	ruff check loto apps/api tests

typecheck:
	mypy loto apps/api

test:
	pytest

run-demo: demo-up

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
	$$COMPOSE --profile demo --profile pilot up --build -d; \
	end_time=$$(($(date +%s)+120)); \
	until curl --silent --fail http://localhost:8000/healthz >/dev/null 2>&1; do \
	[ $$(date +%s) -ge $$end_time ] && { echo "API failed to start"; exit 1; }; \
	sleep 1; \
	done; \
	$(MAKE) seed-demo; \
	end_time=$$(($(date +%s)+120)); \
	until curl --silent --fail http://localhost:8000/healthz >/dev/null 2>&1; do \
	[ $$(date +%s) -ge $$end_time ] && { echo "Health check failed"; exit 1; }; \
	sleep 1; \
	done; \
	end_time=$$(($(date +%s)+120)); \
	until curl --silent --fail http://localhost:3000/ >/dev/null 2>&1; do \
	[ $$(date +%s) -ge $$end_time ] && { echo "UI failed to start"; exit 1; }; \
	sleep 1; \
	done; \
	if command -v xdg-open >/dev/null 2>&1; then \
	xdg-open http://localhost:3000; \
	elif command -v open >/dev/null 2>&1; then \
	open http://localhost:3000; \
	fi; \
	$$COMPOSE --profile demo --profile pilot logs -f

demo-down:
	@COMPOSE="docker compose"; \
	if docker compose version >/dev/null 2>&1; then \
	COMPOSE="docker compose"; \
	elif command -v docker-compose >/dev/null 2>&1; then \
	COMPOSE="docker-compose"; \
	else \
	echo "Docker Compose is not installed. Install Docker and Docker Compose."; \
	exit 1; \
	fi; \
	$$COMPOSE --profile demo --profile pilot down -v

check-prereqs:
	./scripts/check-prereqs.sh

seed-demo:
	python scripts/seed_demo.py
