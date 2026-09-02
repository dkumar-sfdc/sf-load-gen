// Sales workload (Playwright): launch -> login -> create Lead -> update Lead -> logout.
// Mirrors test-plans/jmeter/sales-workload.jmx.
//
//   node sales-workload.js            # run once with first data row
//   npx playwright test               # if wired into a runner
const path = require('path');
const { chromium } = require('playwright');
const { login, logout, config } = require('./login-flow');
const { readCsv } = require('./_csv');

const DATA = process.env.DATA_FILE || path.join(__dirname, '../../data-files/sales_leads.csv');

async function run(page, row) {
  // Create Lead via UI API (session cookie carries auth in-browser context).
  const created = await page.request.post(
    `${config.myDomain}/services/data/v60.0/sobjects/Lead`,
    { data: {
      Company: row.Company, LastName: row.LastName, FirstName: row.FirstName,
      Email: row.Email, Phone: row.Phone, Status: row.LeadStatus,
    } },
  );
  const leadId = (await created.json()).id;

  // Update the Lead just created (PATCH -> 204 No Content).
  await page.request.patch(
    `${config.myDomain}/services/data/v60.0/sobjects/Lead/${leadId}`,
    { data: { Status: row.UpdatedStatus, Phone: row.Phone } },
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
    console.log(`sales-workload: processed ${rows.length} rows`);
  } finally {
    await browser.close();
  }
})();
