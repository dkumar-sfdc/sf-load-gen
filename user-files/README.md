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
