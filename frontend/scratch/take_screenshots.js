const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const targetDir = 'C:\\Users\\Groot\\.gemini\\antigravity-ide\\brain\\ac0a3f40-eaed-48e4-844c-37191a734f62';

async function takeScreenshots() {
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1366, height: 768 }
  });
  const page = await context.newPage();

  console.log('1. Capturing Login Page...');
  await page.goto('http://localhost:5173/login');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(targetDir, 'login.png') });

  console.log('Logging in...');
  await page.fill('input[placeholder*="Email"]', 'admin@aegisos.com');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(3000);

  console.log('2. Capturing Operations Console...');
  await page.goto('http://localhost:5173/home');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(targetDir, 'console.png') });

  console.log('3. Capturing Project List...');
  await page.goto('http://localhost:5173/projects');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(targetDir, 'projects.png') });

  console.log('4. Capturing Project Workspace...');
  // Find project id from database or list
  const projectId = '7a52120a-7760-4dde-9f91-8f9bbe35b332';
  await page.goto(`http://localhost:5173/projects/${projectId}/workspace`);
  await page.waitForTimeout(5000);
  await page.screenshot({ path: path.join(targetDir, 'workspace.png') });

  console.log('5. Capturing Human Queue...');
  await page.goto('http://localhost:5173/queue');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(targetDir, 'queue.png') });

  console.log('6. Capturing Users Page...');
  await page.goto('http://localhost:5173/users');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(targetDir, 'users.png') });

  console.log('7. Capturing Administration (Settings) Page...');
  await page.goto('http://localhost:5173/administration');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(targetDir, 'settings.png') });

  console.log('8. Capturing Install Wizard (Locked state / redirect)...');
  await page.goto('http://localhost:5173/install');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(targetDir, 'install.png') });

  await browser.close();
  console.log('All screenshots captured successfully!');
}

takeScreenshots().catch(console.error);
