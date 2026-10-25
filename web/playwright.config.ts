import { defineConfig } from '@playwright/test';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

const localBrowser = 'C:/Users/Valensius Alven/AppData/Local/ms-playwright/chromium-1243/chrome-win64/chrome.exe';
export default defineConfig({
  testDir: './tests', timeout: 60_000, expect: { timeout: process.env.FLUO_VERCEL_OIDC_TOKEN ? 30_000 : 10_000 }, fullyParallel: false, workers: 1,
  reporter: [['list'], ['json', { outputFile: '../docs/implementation/qa/e2e-results.json' }], ['html', { outputFolder: '../docs/implementation/qa/playwright-report', open: 'never' }]],
  outputDir: '../.local/playwright-results',
  use: { baseURL: process.env.FLUO_BASE_URL ?? 'http://127.0.0.1:5173', viewport: {width:1440,height:900}, headless:true, trace:'retain-on-failure', screenshot:'only-on-failure', launchOptions: { executablePath: process.env.FLUO_BROWSER_PATH ?? (existsSync(localBrowser) ? localBrowser : undefined) } },
  metadata: { evidenceDirectory: resolve('../docs/implementation/qa') },
});
