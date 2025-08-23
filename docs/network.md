# Network Requirements

Outbound network access from the LOTO services must be limited to the Maximo and Coupa SaaS endpoints.

## Maximo
- Hostname: maximo.example.com
- IP address: 203.0.113.10
- Port: 443 (HTTPS)

## Coupa
- Hostname: api.coupahost.com
- IP address: 198.51.100.20
- Port: 443 (HTTPS)

All other outbound traffic should be blocked. See `docker-compose.yml` for container-level egress restrictions implemented via iptables.
