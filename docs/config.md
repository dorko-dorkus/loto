# Configuration

## HATS integration

- `HATS_MODE` – Selects the adapter for HATS checks. Set to `HTTP` to call the real service when `HATS_BASE_URL` is provided; defaults to the built-in demo adapter.
- `HATS_CACHE_TTL_S` – Time-to-live in seconds for cached HATS responses. Unset disables caching.
- `HATS_FAILCLOSE_CRITICAL` – When `true`, missing HATS data fails critical work orders (default `true`).
- `HATS_WARN_ONLY_MECH` – When `true`, non-critical mechanical work orders only log warnings on HATS errors instead of failing (default `false`).

## Isolation planner weights

These environment variables tune the cost model used by the isolation planner. All values are floating point numbers.

- `W_ALPHA` (default `1.0`)
- `W_BETA` (default `5.0`)
- `W_GAMMA` (default `0.5`)
- `W_DELTA` (default `1.0`)
- `W_EPSILON` (default `2.0`)
- `W_ZETA` (default `0.5`)
- `CB_SCALE` (default `30.0`)
- `CB_MAX` (default `120.0`)
- `RST_SCALE` (default `30.0`)
