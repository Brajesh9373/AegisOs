import { chromium } from 'playwright';

const token = process.env.ECMS_E2E_TOKEN;
const baseUrl = process.env.ECMS_WEB_URL || 'http://localhost:3000';
if (!token) throw new Error('ECMS_E2E_TOKEN is required');

const browser = await chromium.launch({ headless: true });
const errors = [];

try {
  const cosmosPage = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  cosmosPage.on('pageerror', (error) => errors.push(`cosmos: ${error.message}`));
  await cosmosPage.addInitScript((authToken) => {
    localStorage.setItem('auth_token', authToken);
  }, token);
  await cosmosPage.goto(
    `${baseUrl}/administration?knowledgeRenderer=cosmos`,
    { waitUntil: 'domcontentloaded', timeout: 60_000 },
  );
  await cosmosPage.getByRole('tab', { name: 'Knowledge', exact: true }).click();
  await cosmosPage.getByTestId('knowledge-graph-cosmos').waitFor({ timeout: 120_000 });
  await cosmosPage.locator('canvas').first().waitFor({ timeout: 60_000 });
  const search = cosmosPage.getByPlaceholder('Search nodes...');
  for (const value of ['api', 'worker', 'security', '']) {
    await search.fill(value);
  }
  await cosmosPage.goto(`${baseUrl}/`, { waitUntil: 'domcontentloaded' });
  if (await cosmosPage.getByTestId('knowledge-graph-cosmos').count() !== 0) {
    throw new Error('Cosmos renderer survived route unmount');
  }
  await cosmosPage.close();

  const fallbackPage = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  fallbackPage.on('pageerror', (error) => errors.push(`fallback: ${error.message}`));
  await fallbackPage.addInitScript((authToken) => {
    localStorage.setItem('auth_token', authToken);
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function getContext(type, ...args) {
      if (type === 'webgl2') return null;
      return original.call(this, type, ...args);
    };
  }, token);
  await fallbackPage.route('**/api/knowledge-graph/v2/config', (route) => {
    void route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ renderer: 'cosmos' }),
    });
  });
  await fallbackPage.goto(`${baseUrl}/administration`, {
    waitUntil: 'domcontentloaded',
    timeout: 60_000,
  });
  await fallbackPage.getByRole('tab', { name: 'Knowledge', exact: true }).click();
  await fallbackPage.getByTestId('knowledge-graph-d3').waitFor({ timeout: 120_000 });
  await fallbackPage.getByText(
    'WebGL2 is unavailable; using the compatibility renderer.',
  ).waitFor();
  if (await fallbackPage.getByTestId('knowledge-graph-cosmos').count() !== 0) {
    throw new Error('Cosmos mounted when WebGL2 was unavailable');
  }
  await fallbackPage.close();

  if (errors.length > 0) throw new Error(errors.join(' | '));
  process.stdout.write(JSON.stringify({
    cosmosLoad: 'passed',
    rapidSearch: 'passed',
    rendererCleanup: 'passed',
    webglFallback: 'passed',
  }) + '\n');
} finally {
  await browser.close();
}
