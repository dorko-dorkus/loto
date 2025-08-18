.PHONY: fmt lint typecheck test run-demo

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
