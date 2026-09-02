# user-files

Login credentials — **one file per test**. Header `Username,Password`, one row per user.

| Test | File | Task default (`users_file`) |
|------|------|------------------------------|
| login   | `login_users.csv`   | `salesforce-login.jmx` |
| sales   | `sales_users.csv`   | `sales-workload.jmx` |
| service | `service_users.csv` | `service-workload.jmx` |
| agent   | `agent_users.csv`   | `agent-workload.jmx` |

- `*_users.csv` — plaintext samples, local runs only.
- `*.csv.enc` — encrypted bundles for shared/CI use. Commit the `.enc`, never plaintext
  (see repo `.gitignore`).

Override at runtime: `-Jusers_file=../../user-files/sales_users.csv` (JMeter).

Encrypt a plaintext CSV (example, openssl):

```bash
openssl enc -aes-256-cbc -pbkdf2 -salt \
  -in sales_users.csv -out sales_users.csv.enc
```

## JWT Bearer auth (agent workload)

`jwt_key.example.pem` is a throwaway PKCS#8 RSA private key used by the `agent`
workload's JWT Bearer flow (Pattern 3) — it replaces username/password login
for that workload, so there is no `agent_users.csv` round-robin anymore; the
impersonated user comes from the `jwt_subject` property.

Real keys must **NOT** be committed — `user-files/*.pem` is gitignored except
for the tracked example (see repo `.gitignore`).

To use JWT auth:

1. Create a Salesforce Connected App with OAuth enabled and "Use digital
   signatures" checked.
2. Upload the matching X.509 certificate to the Connected App.
3. Pre-authorize the `jwt_subject` user (profile/permission set + policy).
4. Point `-Jjwt_key_file=` (JMeter) / `SF_JWT_KEY_FILE` (env) at your private
   key.

Generate a key + cert pair, then convert the key to PKCS#8:

```bash
openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes
openssl pkcs8 -topk8 -nocrypt -in server.key -out jwt_key.pem
```
