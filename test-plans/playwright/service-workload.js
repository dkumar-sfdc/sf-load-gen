// Service workload (Playwright): launch -> login -> create Case -> update Case -> logout.
// Mirrors test-plans/jmeter/service-workload.jmx.
const path = require('path');
const { chromium } = require('playwright');
const { login, logout, config } = require('./login-flow');
const { readCsv } = require('./_csv');

const DATA = process.env.DATA_FILE || path.join(__dirname, '../../data-files/service_cases.csv');

async function run(page, row) {
  const res = await page.request.post(
    `${config.myDomain}/services/data/v60.0/sobjects/Case`,
    { data: {
      Subject: row.Subject, Description: row.Description, Priority: row.Priority,
      Origin: row.Origin, Status: row.Status,
    } },
  );
  const caseId = (await res.json()).id;

  // Update the Case just created (PATCH -> 204 No Content).
  await page.request.patch(
    `${config.myDomain}/services/data/v60.0/sobjects/Case/${caseId}`,
    { data: { Status: row.UpdatedStatus, Priority: row.Priority } },
  );
}

(async () => {
  const rows = readCsv(DATA);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    await login(page);
    for (const row of rows) await run(page, row);
    await logout(page);
    console.log(`service-workload: processed ${rows.length} rows`);
  } finally {
    await browser.close();
  }
})();
