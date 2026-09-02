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
| **agent**   | JWT auth → start Agentforce session → send utterance → end session | `agent-workload.jmx` | `agent-workload.js` |

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

## Execution patterns

Three ways to wire credentials, data, and the login step. This repo ships all three
patterns.

### Pattern 1 — User-File-Driven Execution (session-per-user)

The **users file is the source of truth**. Each thread reads one row → logs in once →
performs **all** operations for that session → logs out.

```
CSVDataSet(users.csv) → shareMode.thread          # each thread picks: username, password
login once → execute full transaction flow as that user → logout
```

Best for: **simulating real user sessions** — one person logs in, does N actions, logs
out. If a row needs business data, look it up by username (Pattern-2-style lookup) *after*
login. **This repo:** the `service` and `agent` workloads (round-robin their own
`*_users.csv` via a thread-scoped CSV Data Set, one login per iteration of many actions).

### Pattern 2 — Data-File-Driven Execution (row-per-transaction)

The **data/accounts file is the source of truth**. For **each** row → fresh login →
execute one transaction → discard session → next row.

```
CSVDataSet(data.csv) → shareMode.all, recycle=true
per row: extract Username → login → single transaction → discard session
```

Best for: **bulk transaction throughput** — volume of records processed, not persistent
sessions. Higher login:transaction ratio (1 login per row vs 1 login per N actions).
**This repo:** the `sales` workload (data row carries the login `Username`; setUp group +
resolve PreProcessor supply the password — see below). Data-file-driven login.

### Pattern 3 — JWT/Token-Based Auth + session reuse

Authenticate **once via JWT/OAuth** (not username/password form login), cache the token,
reuse across all operations for that thread — same session-persistence idea as Pattern 1
but skips repeated credential-based login overhead.

**This repo:** the `agent` workload. Each thread authenticates once via a signed **RS256
JWT Bearer assertion**, exchanges it for an `access_token`, and reuses that token for every
Agentforce API call in the thread:

- **JMeter:** a `JSR223Sampler` "Build JWT assertion" (Groovy) signs the RS256 assertion,
  followed by a `POST oauth2 token` sampler — both wrapped in an **If Controller** keyed on
  `vars.get("access_token") == null` so the exchange runs once per thread, not once per
  iteration.
- **Playwright:** Node's built-in `crypto` module signs the RS256 assertion; the token
  exchange uses `request.newContext()` once per worker/session.

```groovy
// If Controller condition: ${__groovy(vars.get("access_token") == null)}
// JSR223Sampler "Build JWT assertion" builds+signs the RS256 JWT (iss=client_id, sub=jwt_subject,
// aud=login_host, exp=now+3min); the following "POST oauth2 token" sampler exchanges it and a
// JSR223PostProcessor stores the response's access_token into vars for reuse by every later sampler:
// Authorization: Bearer ${access_token}
```

Best for: **isolating business-logic load from auth load** — stress the app tier without
hammering the login/SSO tier. Salesforce-specific: **JWT Bearer Flow** skips the password
entirely — no CSV password column needed. Requires a Salesforce **Connected App** with
"Use digital signatures" enabled (certificate uploaded there must match the private key
used to sign the assertion) and the target user **pre-authorized** for JWT access on that
Connected App (or org-wide admin pre-approval).

### Sales credential model (data-driven login)

Sales differs from the other workloads. Its data file `sales_leads.csv` leads with a
`Username` column — the login user each row runs as. The plan does **not** round-robin a
users CSV. Instead it splits login into two JMeter elements for data-file-driven login.

#### 1. setUp Thread Group — "Load Credentials"

A **setUp Thread Group** (1 thread, 1 loop) runs to completion *before* the main thread
group starts. Its single **`JSR223Sampler` "Load user-file into properties"** (Groovy)
reads the user file and stashes every credential as a global JMeter **property** keyed
`password.<username>`:

```groovy
import org.apache.jmeter.services.FileServer

// The plan has to run wherever it is dropped on the VM, so try the path as given
// (absolute, or relative to the working directory) and then relative to this .jmx.
def path = vars.get("USER_FILE")
def candidates = [new File(path), new File(FileServer.getFileServer().getBaseDir(), path)]
def file = candidates.find { it.isFile() }
if (file == null) {
  SampleResult.setSuccessful(false)
  SampleResult.setResponseData("credentials loaded: 0", "UTF-8")
  SampleResult.setResponseMessage("No user file at " + candidates.collect { it.getAbsolutePath() }.join(" or "))
  return
}

int loaded = 0
file.readLines().drop(1).each { line ->
  def row = line.trim()
  if (row.length() != 0) {
    def cols = row.split(",", -1)
    if (cols.length >= 2) {
      props.put("password." + cols[0].trim(), cols[1].trim())
      loaded++
    }
  }
}

SampleResult.setResponseData("credentials loaded: " + loaded, "UTF-8")
SampleResult.setDataType("text")
SampleResult.setSuccessful(loaded != 0)
if (loaded == 0) {
  SampleResult.setResponseMessage("No credentials found in " + file.getAbsolutePath())
}
```

#### 2. Resolve Password PreProcessor

A **`JSR223PreProcessor` "Resolve Password for row Username"** (Groovy) on the main thread
group runs once per iteration, *before* `T2_Login`. It reads the data row's `Username`,
looks up the property loaded in step 1, and exposes `USERNAME`/`PASSWORD` for the login POST:

```groovy
def user = vars.get("Username")
def password = props.get("password." + user)
if (password == null) { log.error("No password in user-file for username: " + user); password = "" }
vars.put("USERNAME", user)
vars.put("PASSWORD", password)
```

So each row logs in as its own user, with the password looked up (never carried in the
business data file).

#### Dependencies

- **Groovy** scripting engine — bundled with JMeter (`lib/groovy-all-*.jar`); no extra
  install. `scriptLanguage=groovy` on both JSR223 elements.
- **`org.apache.jmeter.services.FileServer`** (core JMeter) for `.jmx`-relative path fallback.
- **Global `props`** — properties are a single JVM-wide map, so values written by the setUp
  group are visible to every thread in the main group. Ordering guaranteed: setUp Thread
  Groups always finish before main groups begin.
- **`USER_FILE`** UDV — defaults to `../../user-files/sales_users.csv`; override with
  `-Jusers_file=`. The loader resolves it either as-given or relative to the plan file.
- Data-row **`Username`** values **must** exist in the user file, else no password maps.

#### Validations

| Where | Check | On failure |
|-------|-------|------------|
| setUp loader | file found via one of the candidate paths | sampler marked failed, message lists tried paths, `return` (no creds loaded) |
| setUp loader | at least one credential parsed | `SampleResult.setSuccessful(loaded != 0)` — sampler red if file empty/malformed |
| Resolve PreProcessor | `password.<username>` property exists | `log.error(...)`, `PASSWORD` set to empty (login then fails its assertion) |
| `T2_Login` | login returned a session id | Response Assertion: variable `sid` must not contain `SID_NOT_FOUND` |

Service and agent workloads are unchanged — they round-robin their own `*_users.csv` via a
standard CSV Data Set (no setUp group, no resolve step).

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
| `login_host` | `login.salesforce.com` | JWT token endpoint host (agent workload, Pattern 3 JWT auth) |
| `client_id` | placeholder | Connected App consumer key (agent workload, JWT) |
| `jwt_subject` | placeholder | User to impersonate/authenticate as (agent workload, JWT) |
| `jwt_key_file` | `../../user-files/jwt_key.example.pem` | PKCS#8 PEM private key for signing the JWT assertion (agent workload, JWT) — `jwt_key.example.pem` is a throwaway sample key; replace with your Connected App's key |

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
