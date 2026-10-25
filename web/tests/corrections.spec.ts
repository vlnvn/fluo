import { test } from './guest';
import { enterGuest } from './guest';
import { expect } from '@playwright/test';
import type { Event } from '../src/contracts';
import { mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const out = resolve('../docs/implementation/qa/corrections');
mkdirSync(out, { recursive: true });

test('consistent notification counts, navigation icon states, actual summary visuals and spaced actions', async ({ page }) => {
  await enterGuest(page);
  await expect(page.getByRole('heading', { name: 'Condensate return', exact: true, level: 1 })).toBeVisible();
  await expect(page.locator('.page-title-actions')).toContainText('Production');
  const session = await page.evaluate(() => localStorage.getItem('fluo.session.v1')!);
  const snapshot = await (await page.request.get(`/api/v1/sessions/${session}`)).json();
  const count = String(snapshot.events.length);
  await expect(page.getByTestId('notification-count')).toHaveText(count);
  for (const route of ['Scenario Review', 'Event Center', 'Overview']) {
    await page.getByRole('link', { name: route, exact: true }).click();
    await expect(page.getByTestId('notification-count')).toHaveText(count);
    await expect(page.getByRole('link',{name:route,exact:true})).toHaveAttribute('aria-current','page');
    const active = await page.locator('.sidebar nav .active .icon').evaluate(el => getComputedStyle(el).filter);
    for (const icon of await page.locator('.sidebar nav .nav-row:not(.active) .icon').all()) {
      expect(await icon.evaluate(el => getComputedStyle(el).filter)).not.toBe(active);
    }
  }
  await page.locator('.notification-button').click();
  await expect(page.getByTestId('notification-count')).toHaveText(count);
  await page.getByRole('button', { name: 'Close Notifications', exact: true }).click();
  await page.reload();
  await expect(page.getByTestId('notification-count')).toHaveText(count);
  await page.locator('.notification-button').click();
  const peer = await page.context().newPage();
  await peer.goto('/');
  await expect(peer.getByTestId('notification-count')).toHaveText(count);
  await page.getByRole('button', { name: 'Mark all as read', exact: true }).click();
  await expect(peer.getByTestId('notification-count')).toHaveCount(0);
  await peer.close();
  await expect(page.getByTestId('notification-count')).toHaveCount(0);
  await page.keyboard.press('Escape');
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Condensate return', exact: true, level: 1 })).toBeVisible();
  await expect(page.getByTestId('notification-count')).toHaveCount(0);
  await page.screenshot({ path: resolve(out, 'overview-full.png') });
  await page.getByRole('link', { name: 'Event Center', exact: true }).click();
  const events: Event[] = snapshot.events;
  for (const category of ['return', 'quality'] as const) {
    const bars = page.locator(`.histogram-${category} rect`);
    await expect(bars).toHaveCount(13);
    const counts = await bars.evaluateAll(items => items.map(el => Number(el.getAttribute('data-count'))));
    expect(counts.reduce((a, b) => a + b, 0)).toBe(events.filter(e => e.category === category && (category !== 'quality' || ['GATEWAY_OFFLINE','VERIFY_RETURN_METER'].includes(e.quality_action ?? ''))).length);
    const first = await bars.nth(0).boundingBox(), next = await bars.nth(1).boundingBox();
    expect(first!.x + first!.width).toBeLessThan(next!.x);
  }
  await expect(page.locator('.window-progress')).toHaveAccessibleName(/Replay window \d+% elapsed/);
  await page.screenshot({ path: resolve(out, 'events-full.png') });
  await page.getByRole('button', { name: 'Collapse sidebar', exact: true }).click();
  await page.screenshot({ path: resolve(out, 'events-compact.png') });
  await page.getByRole('button', { name: `Open ${events[0].id}`, exact: true }).click();
  await expect(page.locator('.evidence-card')).toContainText('Process: Production');
  const draft = await page.getByRole('button', { name: 'Save draft', exact: true }).boundingBox();
  const record = await page.getByRole('button', { name: 'Record operator review', exact: true }).boundingBox();
  expect(record!.y > draft!.y || record!.x - (draft!.x + draft!.width) >= 9).toBe(true);
  await page.getByRole('button', { name: 'Save draft', exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: resolve(out, 'review-actions.png') });
  await page.getByRole('button', { name: 'View inspection summary', exact: true }).click();
  await page.getByRole('button', { name: 'Print', exact: true }).click();
  const report = page.frameLocator('#report-preview');
  await expect(report.getByRole('heading', { name: 'Inspection summary', exact: true })).toBeVisible();
  await expect(report.getByRole('button')).toHaveCount(0);
  await expect(report.locator('.evidence')).toContainText('Production');
  await expect(page.getByRole('button', { name: 'Close', exact: true })).toHaveCount(1);
  await expect(page.getByRole('button', { name: 'Print A4', exact: true })).toHaveCount(1);
  await page.screenshot({ path: resolve(out, 'print-single-toolbar.png') });
});

test('continuous pointer scrubbing sends one seek on release; keyboard and forward/backward stay deterministic', async ({ page }) => {
  await enterGuest(page);
  await page.getByRole('link', { name: 'Scenario Review', exact: true }).click();
  const slider = page.getByLabel('Replay position', { exact: true });
  await expect(slider).toBeEnabled();
  const seeks: number[] = [];
  page.on('request', request => {
    if (request.url().endsWith('/replay') && request.method() === 'POST') {
      const body = request.postDataJSON();
      if (body.action === 'seek') seeks.push(body.cursor);
    }
  });
  await slider.scrollIntoViewIfNeeded();
  const box = (await slider.boundingBox())!;
  await page.mouse.move(box.x + box.width * .2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * .65, box.y + box.height / 2, { steps: 30 });
  await page.waitForTimeout(200);
  expect(seeks).toHaveLength(0);
  await expect(slider).toBeEnabled();
  const released = Number(await slider.inputValue());
  await page.mouse.up();
  await expect.poll(() => seeks.length).toBe(1);
  await expect(slider).toBeEnabled();
  await expect(slider).toHaveValue(String(released));
  await page.getByRole('button', { name: 'Forward 10 samples', exact: true }).click();
  const maximum = Number(await slider.getAttribute('max'));
  await expect(slider).toHaveValue(String(Math.min(maximum, released + 10)));
  await page.getByRole('button', { name: 'Rewind 10 samples', exact: true }).click();
  await expect(slider).toHaveValue(String(released));
  await slider.focus(); await page.keyboard.press('End');
  await expect(page.getByRole('button', { name: 'Forward 10 samples', exact: true })).toBeDisabled();
  await expect(slider).toHaveValue(String(maximum));
  await expect(slider).toBeEnabled();
  await slider.focus(); await page.keyboard.press('Home');
  await expect(slider).toHaveValue('0');
  await expect(page.getByRole('button', { name: 'Rewind 10 samples', exact: true })).toBeDisabled();
  await page.screenshot({ path: resolve(out, 'scenario-controls-full.png') });
  await page.getByRole('button', { name: 'Collapse sidebar', exact: true }).click();
  await page.screenshot({ path: resolve(out, 'scenario-controls-compact.png') });
  await page.setViewportSize({ width: 1180, height: 900 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(1180);
  await page.screenshot({ path: resolve(out, 'scenario-controls-narrow.png') });
});
