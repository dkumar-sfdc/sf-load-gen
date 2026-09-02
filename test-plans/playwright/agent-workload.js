// Agent workload (Playwright): JWT Bearer auth (Pattern 3) -> start Agentforce session -> send utterance -> end session.
// Mirrors test-plans/jmeter/agent-workload.jmx. No browser, no form login: authenticate once via a
// signed RS256 JWT exchanged for an access_token, then drive the Agent API with that bearer token.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { request } = require('playwright');
const { readCsv } = require('./_csv');

const LOGIN_HOST = process.env.SF_LOGIN_HOST || 'login.salesforce.com';
const CLIENT_ID = process.env.SF_CLIENT_ID || '3MVG9mockConnectedAppConsumerKey';
const JWT_SUBJECT = process.env.SF_JWT_SUBJECT || 'agent.user1@example.com';
const JWT_KEY_FILE = process.env.SF_JWT_KEY_FILE || path.join(__dirname, '../../user-files/jwt_key.example.pem');
const MY_DOMAIN = process.env.SF_MY_DOMAIN || 'https://example--sandbox.sandbox.my.salesforce.com';
const AGENT_ID = process.env.SF_AGENT_ID || '0XxSB000000mockAgentId';
const DATA = process.env.DATA_FILE || path.join(__dirname, '../../data-files/agent_prompts.csv');

function b64url(buf) {
  return Buffer.from(buf).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// Build and sign an RS256 JWT Bearer assertion. The matching X.509 cert must be uploaded to
// the Salesforce Connected App (Use digital signatures). Key file is a PKCS#8 PEM private key.
function buildJwtAssertion() {
  const header = { alg: 'RS256' };
  const exp = Math.floor(Date.now() / 1000) + 300;
  const claims = { iss: CLIENT_ID, sub: JWT_SUBJECT, aud: `https://${LOGIN_HOST}`, exp };
  const signingInput = `${b64url(JSON.stringify(header))}.${b64url(JSON.stringify(claims))}`;

  const pem = fs.readFileSync(JWT_KEY_FILE, 'utf8');
  const privateKey = crypto.createPrivateKey(pem);
  const signer = crypto.createSign('RSA-SHA256');
  signer.update(signingInput);
  signer.end();
  const signature = signer.sign(privateKey);

  return `${signingInput}.${b64url(signature)}`;
}

async function authenticate(ctx) {
  const assertion = buildJwtAssertion();
  const res = await ctx.post(`https://${LOGIN_HOST}/services/oauth2/token`, {
    form: {
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion,
    },
  });
  const body = await res.json();
  if (!body.access_token) throw new Error(`JWT Bearer token exchange failed: ${JSON.stringify(body)}`);
  return { accessToken: body.access_token, instanceUrl: body.instance_url };
}

async function run(ctx, accessToken, row, i) {
  const headers = { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' };

  const start = await ctx.post(
    `${MY_DOMAIN}/einstein/ai-agent/v1/agents/${AGENT_ID}/sessions`,
    { headers, data: {
      externalSessionKey: `${row.SessionLabel}-${i}`,
      instanceConfig: { endpoint: MY_DOMAIN },
      streamingCapabilities: { chunkTypes: ['Text'] },
    } },
  );
  const sessionId = (await start.json()).sessionId;

  await ctx.post(
    `${MY_DOMAIN}/einstein/ai-agent/v1/sessions/${sessionId}/messages`,
    { headers, data: { message: { sequenceId: 1, type: 'Text', text: row.UtteranceText } } },
  );

  await ctx.post(
    `${MY_DOMAIN}/einstein/ai-agent/v1/sessions/${sessionId}/end`,
    { headers, data: { reason: 'UserRequest' } },
  );
}

(async () => {
  const rows = readCsv(DATA);
  const ctx = await request.newContext();
  try {
    const { accessToken } = await authenticate(ctx);
    for (let i = 0; i < rows.length; i++) await run(ctx, accessToken, rows[i], i);
    console.log(`agent-workload: processed ${rows.length} prompts`);
  } finally {
    await ctx.dispose();
  }
})();
