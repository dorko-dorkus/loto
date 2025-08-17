# LOTO Planner

## Quickstart

```bash
# Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

# Set up pre-commit hooks
pre-commit install

# Format, lint, type-check and run tests
make fmt
make lint
make typecheck
make test

# Show the CLI help as a simple demo
make run-demo
```
