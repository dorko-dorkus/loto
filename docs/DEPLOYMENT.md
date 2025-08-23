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
