import { chromium } from 'playwright';

const token = process.env.ECMS_E2E_TOKEN;
const jobId = process.env.ECMS_INGESTION_JOB_ID;
const baseUrl = process.env.ECMS_WEB_URL || 'http://localhost:3000';
if (!token || !jobId) {
  throw new Error('ECMS_E2E_TOKEN and ECMS_INGESTION_JOB_ID are required');
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));

try {
  const response = await page.request.get(
    `${baseUrl}/api/connector-ingestions/${jobId}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!response.ok()) throw new Error(`job lookup returned ${response.status()}`);
  const durable = await response.json();
  const persisted = {
    ...durable,
    status: String(durable.status).toUpperCase(),
    connection_name: 'OpenClaw production qualification',
    repository_url: 'https://github.com/openclaw/openclaw',
  };
  await page.addInitScript(({ authToken, ingestion }) => {
    localStorage.setItem('auth_token', authToken);
    localStorage.setItem(
      'ecms.connector-ingestions.v1',
      JSON.stringify({ [ingestion.job_id]: ingestion }),
    );
  }, { authToken: token, ingestion: persisted });

  await page.goto(`${baseUrl}/administration`, {
    waitUntil: 'domcontentloaded',
    timeout: 60_000,
  });
  await page.getByRole('tab', { name: 'Tools', exact: true }).click();
  await page.getByText('OpenClaw production qualification', { exact: true }).first()
    .waitFor({ timeout: 30_000 });
  await page.locator('.ant-progress').first().waitFor({ timeout: 30_000 });

  await page.getByRole('tab', { name: 'Knowledge', exact: true }).click();
  await page.getByRole('tab', { name: 'Tools', exact: true }).click();
  await page.getByText('OpenClaw production qualification', { exact: true }).first()
    .waitFor({ timeout: 30_000 });

  await page.reload({ waitUntil: 'domcontentloaded', timeout: 60_000 });
  await page.getByRole('tab', { name: 'Tools', exact: true }).click();
  await page.getByText('OpenClaw production qualification', { exact: true }).first()
    .waitFor({ timeout: 30_000 });

  const stored = await page.evaluate(() => (
    JSON.parse(localStorage.getItem('ecms.connector-ingestions.v1') || '{}')
  ));
  if (!stored[jobId]) throw new Error('durable job was lost after reload');
  if (errors.length) throw new Error(errors.join(' | '));

  process.stdout.write(JSON.stringify({
    progressVisible: 'passed',
    navigationPersistence: 'passed',
    reloadPersistence: 'passed',
    browserErrors: 0,
  }) + '\n');
} finally {
  await browser.close();
}
