// Agent workload (Playwright): login -> start Agentforce session -> send utterance -> end session.
// Mirrors test-plans/jmeter/agent-workload.jmx.
const path = require('path');
const { chromium } = require('playwright');
const { login, logout, config } = require('./login-flow');
const { readCsv } = require('./_csv');

const DATA = process.env.DATA_FILE || path.join(__dirname, '../../data-files/agent_prompts.csv');
const AGENT_ID = process.env.SF_AGENT_ID || '0XxSB000000mockAgentId';

async function run(page, row, i) {
  const start = await page.request.post(
    `${config.myDomain}/einstein/ai-agent/v1/agents/${AGENT_ID}/sessions`,
    { data: {
      externalSessionKey: `${row.SessionLabel}-${i}`,
      instanceConfig: { endpoint: config.myDomain },
      streamingCapabilities: { chunkTypes: ['Text'] },
    } },
  );
  const sessionId = (await start.json()).sessionId;

  await page.request.post(
    `${config.myDomain}/einstein/ai-agent/v1/sessions/${sessionId}/messages`,
    { data: { message: { sequenceId: 1, type: 'Text', text: row.UtteranceText } } },
  );

  await page.request.post(
    `${config.myDomain}/einstein/ai-agent/v1/sessions/${sessionId}/end`,
    { data: { reason: 'UserRequest' } },
  );
}

(async () => {
  const rows = readCsv(DATA);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    await login(page);
    for (let i = 0; i < rows.length; i++) await run(page, rows[i], i);
    await logout(page);
    console.log(`agent-workload: processed ${rows.length} prompts`);
  } finally {
    await browser.close();
  }
})();
