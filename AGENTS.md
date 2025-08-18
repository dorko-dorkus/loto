# Guidelines for Contributors

## Code style
- Use Python 3.11+ and `pip install -e .[dev]` to install dependencies.
- Format Python code with `make fmt` and lint with `make lint`.
- Type check with `make typecheck`.
- Run tests with `make test`.
- For frontend changes under `apps/maximo-extension-ui`, run `pnpm install` and `pnpm -F maximo-extension-ui test`.

## Pre-commit
- Run `pre-commit run --files <file1> <file2>` on changed files before committing.

## Environment
- Copy `.env.example` to `.env` and set required variables: `MAXIMO_BASE_URL`, `MAXIMO_APIKEY`, `MAXIMO_OS_WORKORDER`, `MAXIMO_OS_ASSET`, `NEXT_PUBLIC_USE_API`.

## Pull Requests
- Describe changes and include test results in the PR body.
