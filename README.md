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

Requires Node.js 20+.

```bash
# Install pnpm
corepack enable

# Install dependencies and run tests for the Next.js app
pnpm install
pnpm -F maximo-extension-ui test

# Start the local development server
pnpm -F maximo-extension-ui dev
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

## Local Development

Install Python dependencies and run the Next.js development server:

```bash
pip install -e .[dev]
pnpm install
pnpm -F maximo-extension-ui dev
```

This starts the UI at <http://localhost:3000>. In another terminal you can
launch the API with `uvicorn loto.main:app --reload` which will listen on
<http://localhost:8000>.

## Docker Demo

Run the API and UI with demo data using Docker. Ensure Docker and Docker Compose are installed and the Docker daemon is running:

```bash
docker compose --profile demo up
```

To start the pilot stack, which includes a Postgres service:

```bash
docker compose --profile pilot up
```

These commands read `.env.example` and start the API at <http://localhost:8000> and the
UI at <http://localhost:3000>. Verify the API is running:

```bash
curl :8000/healthz
curl :8000/version
```

Open the UI in your browser to view the Portfolio page at
<http://localhost:3000>.

To run the CLI demo instead:

```bash
make run-demo
```

## On-Call Support

See [On-Call Guide](docs/on_call.md) for contact rotations, escalation paths, and rollback steps.

## Screenshots

Due to repository constraints, screenshots are not stored in git. Run the demo and capture your own screenshots of the API and UI, or view placeholder images below.

### API

![API screenshot placeholder](https://via.placeholder.com/800x400?text=API+Screenshot)

### UI

![UI screenshot placeholder](https://via.placeholder.com/800x400?text=UI+Screenshot)
