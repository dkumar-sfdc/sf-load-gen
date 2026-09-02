# data-files

Shared business/test data CSVs consumed by the workload plans (both engines).

| File | Consumed by | Columns |
|------|-------------|---------|
| `sales_leads.csv` | sales-workload | `Username,Company,LastName,FirstName,Email,Phone,LeadStatus,UpdatedStatus` |
| `service_cases.csv`  | service-workload | `Subject,Description,Priority,Origin,Status,UpdatedStatus,ContactEmail` |
| `agent_prompts.csv`  | agent-workload | `SessionLabel,UtteranceText,ExpectedTopic` |

**Sales note:** `sales_leads.csv` leads with a `Username` column — the login user for
each row. Every value must match a row in `user-files/sales_users.csv`; the sales plan's
setUp Thread Group + "Resolve Password for row Username" PreProcessor look up the password
by that username (data-file-driven login). Service/agent data files carry no
`Username` — those plans round-robin their own `*_users.csv`.

Reference a data file from the plan (a `CSVDataSet`) and from the workload metadata under
`data_files`, e.g.:

```json
"data_files": {
  "lead_file": "sales_leads.csv"
}
```
