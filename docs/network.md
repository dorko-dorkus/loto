# Network Requirements

Outbound network access from the LOTO services must be limited to an allowlist of hostnames specified via the `EGRESS_ALLOWED_HOSTS` environment variable.

The `scripts/restrict-egress.sh` entrypoint resolves each hostname in the comma-separated allowlist and permits HTTPS traffic to the resulting IP addresses. All other outbound traffic is logged and dropped. See `docker-compose.yml` for container-level egress restrictions implemented via iptables.
