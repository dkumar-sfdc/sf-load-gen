// Shared Salesforce login module (Playwright): mirrors the login flow in
// test-plans/jmeter/salesforce-login.jmx. Standard My Domain username/password
// form login (lt=standard). Used by the login/sales/service runners. The agent
// workload does NOT use this — it authenticates via JWT Bearer (see agent-workload.js).
//
// Config via env, all with placeholder defaults (replace before running):
//   SF_MY_DOMAIN   https://<org>--<sandbox>.sandbox.my.salesforce.com
//   SF_USERNAME    login user
//   SF_PASSWORD    login password

const config = {
  myDomain: process.env.SF_MY_DOMAIN || 'https://example--sandbox.sandbox.my.salesforce.com',
  username: process.env.SF_USERNAME || 'login.user1@example.com',
  password: process.env.SF_PASSWORD || 'ChangeMe123!',
};

// Launch -> fill username/password -> submit -> land on Lightning home.
async function login(page) {
  await page.goto(`${config.myDomain}/`, { waitUntil: 'domcontentloaded' });
  await page.fill('#username', config.username);
  await page.fill('#password', config.password);
  await Promise.all([
    page.waitForLoadState('domcontentloaded'),
    page.click('#Login'),
  ]);
  return { username: config.username };
}

// Standard Salesforce logout.
async function logout(page) {
  await page.goto(`${config.myDomain}/secur/logout.jsp`, { waitUntil: 'domcontentloaded' });
}

module.exports = { login, logout, config };
