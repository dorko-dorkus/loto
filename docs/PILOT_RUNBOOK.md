# Pilot Runbook

This runbook describes the pilot workflow from generation through attachment.

## Steps

1. **Generate** – Produce the initial artifact using the pilot tools.
2. **Review** – Peers validate the artifact and simulation results.
3. **Export** – Convert the reviewed artifact into the approved format.
4. **Attach** – Upload the exported bundle to the system of record.

## Demo quickstart

1. **Set environment**
   ```bash
   cp .env.example .env
   export MAXIMO_BASE_URL=https://example.com
   export MAXIMO_APIKEY=changeme
   export MAXIMO_OS_WORKORDER=WORKORDER
   export MAXIMO_OS_ASSET=ASSET
   export NEXT_PUBLIC_USE_API=false
   ```
   Ensure Docker is running and the above variables reflect your test endpoints.

2. **Start demo stack**
   ```bash
   make run-demo
   ```
   The API health check at `http://localhost:8000/healthz` must return `{"status":"ok"}` before continuing.

3. **Use sample work orders**
   - `WO-1` – Pump replacement
   - `WO-2` – Motor upgrade
   - `WO-3` – Energy audit

4. **Export a PDF**
   ```bash
   python -m loto.cli demo --out out
   ```
   The file `out/LOTO_A.pdf` is ready for distribution. Remove the output with `rm -rf out` if regeneration is required.

5. **Stop demo stack**
   ```bash
   make demo-down
   ```

## Rollback

- Stop all services and remove volumes:
  ```bash
  make demo-down
  ```
- Rebuild from a clean state:
  ```bash
  make run-demo
  ```
- Escalate to on-call support for prod rollbacks. All deadlines remain in New Zealand time; e.g. `2024-08-15 09:00 NZST (UTC+12)`.

## Data flow

Source data enters the pipeline, is processed by the pilot tools,
reviewed, and exported for attachment.

## Environments

- **dev** – local smoke tests
- **staging** – integration tests
- **prod** – official pilot execution

All deadlines are recorded in New Zealand time; for example
`2024-08-15 09:00 NZST (UTC+12)`.

## Support

Contact the platform team via `#pilot-support` for assistance.
Refer to [On-Call Guide](on_call.md) for contact rotations, escalation paths, and rollback procedures.

## References

- [Triage Ranking](TRIAGE_RANKING.md) – KPI calculations and scheduling integration.
