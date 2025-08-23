# Pilot Runbook

This runbook describes the pilot workflow from generation through attachment.

## Steps

1. **Generate** – Produce the initial artifact using the pilot tools.
2. **Review** – Peers validate the artifact and simulation results.
3. **Export** – Convert the reviewed artifact into the approved format.
4. **Attach** – Upload the exported bundle to the system of record.

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

- [HATS Ranking](HATS_RANKING.md) – KPI calculations and scheduling integration.
