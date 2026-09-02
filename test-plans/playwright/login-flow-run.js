// Standalone login-only runner (mirrors test-plans/jmeter/salesforce-login.jmx).
const { chromium } = require('playwright');
const { login, logout } = require('./login-flow');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    const { username } = await login(page);
    console.log(`login-flow: authenticated as ${username}`);
    await logout(page);
  } finally {
    await browser.close();
  }
})();
