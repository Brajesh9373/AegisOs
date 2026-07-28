import { chromium } from 'playwright';

const token = process.env.ECMS_E2E_TOKEN;
const baseUrl = process.env.ECMS_WEB_URL || 'http://localhost:3000';
const renderer = process.argv[2] || 'cosmos';
const dataset = process.argv[3] || '';

if (!token) {
  throw new Error('ECMS_E2E_TOKEN is required');
}

const params = new URLSearchParams();
if (renderer === 'd3') params.set('knowledgeBenchmark', '1');
else params.set('knowledgeRenderer', 'cosmos');
if (dataset) params.set('knowledgeDataset', dataset);

const browser = await chromium.launch({
  headless: process.env.ECMS_E2E_HEADFUL !== '1',
});
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const browserErrors = [];
page.on('pageerror', (error) => browserErrors.push(error.message));

await page.addInitScript((authToken) => {
  localStorage.setItem('auth_token', authToken);
}, token);

try {
  await page.goto(`${baseUrl}/administration?${params}`, {
    waitUntil: 'domcontentloaded',
    timeout: 60_000,
  });
  await page.getByRole('tab', { name: 'Knowledge', exact: true }).click();
  await page.getByTestId('knowledge-graph-benchmark').waitFor({ timeout: 120_000 });
  await page.waitForFunction(() => Boolean(window.__ECMS_GRAPH_BENCHMARK__), null, {
    timeout: 180_000,
  });

  const result = await page.evaluate(() => ({
    benchmark: window.__ECMS_GRAPH_BENCHMARK__,
    canvasCount: document.querySelectorAll('canvas').length,
    svgCount: document.querySelectorAll('svg').length,
  }));

  if (renderer !== 'd3') {
    await page.getByRole('button', { name: 'Fit complete graph' }).click();
    const canvas = page.locator('canvas').first();
    await canvas.hover();
    await page.mouse.wheel(0, -300);
    const box = await canvas.boundingBox();
    if (box) {
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down();
      await page.mouse.move(box.x + box.width / 2 + 80, box.y + box.height / 2 + 40);
      await page.mouse.up();
    }
  }

  if (browserErrors.length > 0) {
    throw new Error(`Browser errors: ${browserErrors.join(' | ')}`);
  }

  process.stdout.write(`${JSON.stringify(result)}\n`);
} finally {
  await browser.close();
}
