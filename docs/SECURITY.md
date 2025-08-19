# Security

Security considerations for the pilot process.

- Review generated artifacts for sensitive information before export and attachment.
- Data flows only through approved environments (`dev`, `staging`, `prod`).
- Apply least-privilege permissions when accessing pilot resources.
- Report incidents immediately in `#pilot-support`.

## Runbook

### CORS origins

The API only responds to requests from approved origins:

- `http://localhost:3000` for local development
- `https://loto.example.com` for production

### Authentication modes

- API key via the `MAXIMO_APIKEY` environment variable for server-to-server communication
- OAuth2 bearer tokens for user-facing flows

### Rate-limit defaults

Requests are limited to **100 per minute per IP**. The limit can be overridden via the `RATE_LIMIT` configuration value when necessary.

### Key rotation

Rotate API keys and credentials at least every **90 days**. Revoke and regenerate keys immediately if compromise is suspected.

### Log retention

Audit and access logs are retained for **30 days** in centralized storage and then purged.
