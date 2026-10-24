import { test, expect } from '@playwright/test';
import { enterGuest, csrfHeaders } from './guest';
import AxeBuilder from '@axe-core/playwright';

test('guest entry is accessible and starts a workspace with the keyboard',async({page})=>{
  await page.goto('/');
  const start=page.getByRole('button',{name:'Start guest workspace',exact:true});
  await expect(start).toBeVisible();
  expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
  await page.keyboard.press('Tab');
  await expect(start).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('.page-overview')).toBeVisible();
});

test('fresh browsers isolate objects; HttpOnly credential, CSRF and logout are enforced',async({page,browser})=>{
  await enterGuest(page);
  expect(await page.evaluate(()=>document.cookie)).not.toContain('fluo_guest');
  const first=await page.evaluate(()=>localStorage.getItem('fluo.session.v1')!);
  const own=await(await page.request.get(`/api/v1/sessions/${first}`)).json();
  const otherContext=await browser.newContext({baseURL:process.env.FLUO_BASE_URL??'http://127.0.0.1:5173'});const other=await otherContext.newPage();
  await enterGuest(other);
  const anonymous=await browser.newContext({baseURL:process.env.FLUO_BASE_URL??'http://127.0.0.1:5173'});
  for(const suffix of ['', '/preview?cursor=0', '/preferences', `/events/${own.events[0].id}/report.pdf`, `/events/${own.events[0].id}/print`]){
    expect((await other.request.get(`/api/v1/sessions/${first}${suffix}`)).status()).toBe(404);
    expect((await anonymous.request.get(`/api/v1/sessions/${first}${suffix}`)).status()).toBe(401);
  }
  expect((await page.request.post(`/api/v1/sessions/${first}/replay`,{data:{action:'reset'}})).status()).toBe(403);
  expect((await page.request.post('/api/v1/auth/logout',{headers:await csrfHeaders(page)})).status()).toBe(204);
  expect((await page.request.get(`/api/v1/sessions/${first}`)).status()).toBe(401);
  await page.reload();await expect(page.getByRole('button',{name:'Start guest workspace',exact:true})).toBeVisible();
  await otherContext.close();await anonymous.close();
});
