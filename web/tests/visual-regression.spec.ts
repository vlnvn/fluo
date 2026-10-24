import { enterGuest } from './guest';
import { test, expect } from '@playwright/test';

test('paused fixed telemetry visual baselines: four routes in Full and Compact',async({page})=>{
  test.setTimeout(60000);await enterGuest(page);await expect(page.locator('h1')).toHaveText('Condensate return');await page.evaluate(()=>document.fonts.ready);
  const id=await page.evaluate(()=>localStorage.getItem('fluo.session.v1'));
  const state=await(await page.request.get(`/api/v1/sessions/${id}`)).json();
  for(const compact of [false,true]){
    if(compact)await page.getByRole('button',{name:'Collapse sidebar'}).click();
    for(const [route,name] of [['/','overview'],['/scenarios','scenario'],['/events','events'],[`/events/${state.events[0].id}`,'details']]){
      await page.goto(`/#${route}`);await expect(page.locator('h1')).toBeVisible();await page.evaluate(()=>document.fonts.ready);await page.mouse.move(1400,880);
      await expect(page).toHaveScreenshot(`${name}-${compact?'compact':'full'}.png`,{animations:'disabled',maxDiffPixels:100});
    }
  }
});
