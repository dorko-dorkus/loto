# LOTO Planner

## Quickstart

### Python backend

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
```

### Frontend

```bash
# Install dependencies and run tests for the Next.js app
pnpm install
pnpm -F maximo-extension-ui test
```

### Environment variables

Copy `.env.example` to `.env` and fill in values as needed:

```bash
cp .env.example .env
```

Required variables:

```dotenv
MAXIMO_BASE_URL=https://example.com
MAXIMO_APIKEY=changeme
MAXIMO_OS_WORKORDER=WORKORDER
MAXIMO_OS_ASSET=ASSET
NEXT_PUBLIC_USE_API=false
```

### Demo

Run the API and UI with demo data using Docker. Ensure Docker and Docker Compose are installed and the Docker daemon is running:

```bash
make demo-up
```

This reads `.env.example` and starts the API at <http://localhost:8000> and the
UI at <http://localhost:3000>. Verify the API is running:

```bash
curl :8000/healthz
```

Open the UI in your browser to view the Portfolio page at
<http://localhost:3000>.

To run the CLI demo instead:

```bash
make run-demo
```
