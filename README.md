# Salesforce Load / Perf Test Repo

Generic, org-agnostic load-generation repo for Salesforce. Ships parallel **JMeter**
and **Playwright** implementations of the same scenarios, all built on a shared,
mocked **Salesforce login** flow. Intended as a common, publishable starting point —
no customer data, all hosts/credentials are placeholders.

## Scenarios

| Workload | Journey | JMeter | Playwright |
|----------|---------|--------|------------|
| **login**   | launch → username/password → frontdoor session → logout | `salesforce-login.jmx` | `login-flow.js` |
| **sales**   | launch → login → create Lead → update Lead → logout | `sales-workload.jmx` | `sales-workload.js` |
| **service** | launch → login → create Case → update Case → logout | `service-workload.jmx` | `service-workload.js` |
| **agent**   | login → start Agentforce session → send utterance → end session | `agent-workload.jmx` | `agent-workload.js` |

## Layout

```
salesforce-login-loadtest/
├── data-files/                     # Shared CSV data for API calls (both engines)
│   ├── sales_leads.csv
│   ├── service_cases.csv
│   └── agent_prompts.csv
├── test-plans/
│   ├── jmeter/                     # JMeter scripts (.jmx)
│   │   ├── salesforce-login.jmx
│   │   ├── sales-workload.jmx
│   │   ├── service-workload.jmx
│   │   └── agent-workload.jmx
│   └── playwright/                 # Playwright scripts (.js)
│       ├── login-flow.js           # shared login module
│       ├── sales-workload.js
│       ├── service-workload.js
│       └── agent-workload.js
├── user-files/                     # Credentials — one file per test (.csv sample, .enc for CI)
│   ├── login_users.csv
│   ├── sales_users.csv
│   ├── service_users.csv
│   └── agent_users.csv
├── workload-metadata/              # Orchestration metadata JSONs
│   ├── salesforce_login_workload_metadata.json
│   ├── sales_workload_metadata.json
│   ├── service_workload_metadata.json
│   └── agent_workload_metadata.json
└── scripts/build_scenarios.py      # regenerates the scenario .jmx from a shared base
```

## Data files (mocked)

| File | Columns |
|------|---------|
| `sales_leads.csv` | `Username,Company,LastName,FirstName,Email,Phone,LeadStatus,UpdatedStatus` |
| `service_cases.csv`  | `Subject,Description,Priority,Origin,Status,UpdatedStatus,ContactEmail` |
| `agent_prompts.csv`  | `SessionLabel,UtteranceText,ExpectedTopic` |

Credentials are **per test** in `user-files/<scenario>_users.csv` (`Username,Password`):
`login_users.csv`, `sales_users.csv`, `service_users.csv`, `agent_users.csv`. Each
workload's `.jmx` and metadata default to its own file; override with `-Jusers_file=`.

### Sales credential model (data-driven login)

Sales differs from the other workloads. Its data file `sales_leads.csv` leads with a
`Username` column — the login user each row runs as. The plan does **not** round-robin a
users CSV. Instead:

1. A **setUp Thread Group** ("Load Credentials") runs once, reading `sales_users.csv`
   (`Username,Password`) into JMeter properties `password.<username>`.
2. A **"Resolve Password for row Username"** BeanShell PreProcessor in the main thread
   group maps each data row's `Username` → `USERNAME`/`PASSWORD` before `T2_Login`.

So each row logs in as its own user, with the password looked up (not carried in the data
file). This mirrors the original **GRAB-TASK1** plan. The `Username` values must match rows
in `sales_users.csv`. Service and agent workloads are unchanged — they round-robin their
own `*_users.csv` via a standard CSV Data Set.

## Run — JMeter

All settings are `-J` properties with safe defaults:

| Property | Default | Meaning |
|----------|---------|---------|
| `my_domain_host` | `example--sandbox.sandbox.my.salesforce.com` | My Domain host |
| `lightning_host` | `example--sandbox.sandbox.lightning.force.com` | Lightning host |
| `api_version` | `v60.0` | REST API version |
| `users_file` | `../../user-files/<scenario>_users.csv` | credentials CSV (per test) |
| `data_file` | per scenario | scenario data CSV |
| `threads` / `ramp` / `loops` | `10` / `30` / `1` | load shape |
| `think_time` | `2000` | think ms (±1000) |
| `agent_id` | mock id | Agentforce agent id (agent workload) |

```bash
jmeter -n -t test-plans/jmeter/sales-workload.jmx \
  -Jmy_domain_host=myorg--sandbox.sandbox.my.salesforce.com \
  -Jlightning_host=myorg--sandbox.sandbox.lightning.force.com \
  -Jthreads=25 -Jramp=60 -Jloops=5 \
  -l results/sales.jtl -e -o results/html
```

## Run — Playwright

```bash
cd test-plans/playwright
npm install && npx playwright install chromium
export SF_MY_DOMAIN=https://myorg--sandbox.sandbox.my.salesforce.com
export SF_USERNAME=user@example.com SF_PASSWORD='***'
npm run sales      # or: login | service | agent
```

## Regenerate JMeter scenarios

The three workload `.jmx` share one login base. Edit `scripts/build_scenarios.py`
(scenario table at the bottom) and rebuild:

```bash
python3 scripts/build_scenarios.py
```

## Notes

- Hosts, credentials and the Agentforce `agent_id` are placeholders — replace before running.
- Login uses standard username/password (`lt=standard`). MFA / SSO / IP-restricted
  orgs won't authenticate this way.
- `workload-metadata/*.json` `allowed_domains` carries a broad Salesforce wildcard set
  (my.salesforce.com, lightning/vf/file.force.com, my.site.com, salesforce-sites.com,
  visualforce.com, plus sandbox variants) so the runner's egress policy covers redirects.
- Keep real credentials out of version control (`.gitignore`; use `user-files/*.enc`).
