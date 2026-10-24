import { expect, type Page } from '@playwright/test';
export async function enterGuest(page:Page){
  await page.goto('/');
  await expect(page.locator('h1')).toHaveText(/Your private guest workspace|Condensate return/);
  const entry=page.getByRole('button',{name:'Start guest workspace',exact:true});
  if(await entry.isVisible())await entry.click();
  await expect(page.locator('h1')).toHaveText('Condensate return');
}
export async function csrfHeaders(page:Page){const auth=await(await page.request.get('/api/v1/auth/session')).json();return {'X-CSRF-Token':auth.csrf_token};}
