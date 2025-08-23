# Deployment

The `prod.env` file contains non-secret configuration. Real credentials such as `MAXIMO_APIKEY` are stored in the team vault.

To populate `prod.env` with secrets:

1. Authenticate to the vault (`op signin` for 1Password or `vault login` for HashiCorp Vault).
2. Read the required values and append them to `prod.env`:

   ```bash
   # 1Password example
   op read "op://LOTO Planner/Production/MAXIMO_APIKEY" >> prod.env

   # HashiCorp Vault example
   vault kv get -field=MAXIMO_APIKEY secret/loto/prod >> prod.env
   ```

`prod.env` is ignored by git and should never be committed.

## CORS configuration

The API only responds to requests from approved web origins. Populate
`CORS_ORIGINS` in both `.env` and `prod.env` with the hostnames that will
serve the frontend:

```bash
# Example pilot origins
CORS_ORIGINS=http://localhost:3000,https://loto.example.com
```

Replace the values with the actual deployment hostnames as necessary.

## OIDC Configuration

The API uses OpenID Connect for authentication. Register a client with your identity
provider and add the credentials to `prod.env`:

```bash
OIDC_CLIENT_ID=your-client-id
OIDC_CLIENT_SECRET=your-client-secret
```

These values are read by `apps/api/main.py` during startup.

## Sentry configuration

Set `SENTRY_DSN` in `.env` and `prod.env` to enable error reporting to Sentry:

```bash
SENTRY_DSN=https://public@example.ingest.sentry.io/0
```

Omit the variable to disable Sentry in a given environment.
