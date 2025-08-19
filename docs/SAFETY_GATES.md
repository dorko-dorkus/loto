# Safety Gates

Gating rules that must pass before artifacts are attached.

## Gating rules

- **Simulation green** – proceed only when the latest simulation run is green.
- **Policy chips** – confirm all policy chips are satisfied prior to export.

## Data flow

Inputs enter the simulator, gates evaluate results,
and only approved outputs move forward for attachment.

## Environments

- **dev** – gates are informational
- **staging** – requires simulation green
- **prod** – requires simulation green and policy chips

Gate reviews log absolute New Zealand times such as
`2024-08-15 09:00 NZST (UTC+12)`.

## Support

For assistance with failing gates, contact `#pilot-support`.
