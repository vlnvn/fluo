import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const out=resolve('../docs/implementation/qa/screenshots');mkdirSync(out,{recursive:true});
async function boot(page:Page){await page.goto('/');await expect(page.getByRole('heading',{name:'Condensate return',exact:true,level:1})).toBeVisible();await page.evaluate(()=>document.fonts.ready);}
async function capture(page:Page,name:string){await page.screenshot({path:resolve(out,`${name}.png`),animations:'disabled'});}
async function sid(page:Page){return page.evaluate(()=>localStorage.getItem('fluo.session.v1')!);}

test('real HGB readings, four pages, Full/Compact geometry and original local assets',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  const failures:string[]=[];page.on('response',r=>{if(r.status()>=400)failures.push(`${r.status()} ${r.url()}`);});
  await boot(page);
  const session=await sid(page),state=await (await page.request.get(`/api/v1/sessions/${session}`)).json();
  await expect(page.getByTestId('kpi-steam-feed')).toHaveText(state.current.readings.steam_kg_h.toFixed(1));
  await expect(page.getByTestId('signature-score')).toHaveText(state.current.inference.score.toFixed(2));
  expect(state.current.inference.warning).toBe(true);
  await capture(page,'overview-full');
  const full=await page.getByTestId('telemetry-chart').boundingBox();
  await page.getByRole('button',{name:'Collapse sidebar'}).click();
  await expect(page.locator('.sidebar')).toHaveCSS('width','76px');
  const wide=await page.getByTestId('telemetry-chart').boundingBox();
  expect(wide!.width).toBeGreaterThan(full!.width+80);
  await capture(page,'overview-compact');
  await page.getByRole('button',{name:'Expand sidebar'}).click();
  await page.getByRole('link',{name:'Scenario Review',exact:true}).click();
  await capture(page,'scenario-full');await page.getByRole('button',{name:'Collapse sidebar'}).click();await capture(page,'scenario-compact');
  await expect(page.getByRole('heading',{name:'Scenario Review',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Expand sidebar'}).click();await page.getByRole('link',{name:'Event Center',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Signal events'})).toBeVisible();await capture(page,'events-full');
  await page.getByRole('button',{name:'Collapse sidebar'}).click();await capture(page,'events-compact');await page.getByRole('button',{name:'Expand sidebar'}).click();
  const first=page.getByRole('button',{name:/^Open EV-/}).first();await first.click();
  await expect(page.getByRole('heading',{name:/Event review/})).toBeVisible();await expect(page.locator('.verification-list input')).toHaveCount(4);
  await capture(page,'details-full');await page.getByRole('button',{name:'Collapse sidebar'}).click();await capture(page,'details-compact');
  const geometry=await page.locator('.event-context').evaluate(el=>{const card=el.getBoundingClientRect();const chart=el.querySelector('.chart')!.getBoundingClientRect();return{card:card.width,chart:chart.width};});
  expect(Math.abs(geometry.card-geometry.chart-26)).toBeLessThan(3);
  for(const img of await page.locator('img').all()){expect(await img.evaluate((el:HTMLImageElement)=>el.complete&&el.naturalWidth>0)).toBe(true);}
  expect(errors).toEqual([]);expect(failures).toEqual([]);
  writeFileSync(resolve(out,'geometry.json'),JSON.stringify({fullChart:full,compactChart:wide,eventGeometry:geometry},null,2));
});

test('deterministic replay controls, scenario reset, model/quality cases, reload and retained navigation',async({page})=>{
  await boot(page);await page.getByRole('link',{name:'Scenario Review',exact:true}).click();
  await page.getByRole('button',{name:'Reset replay',exact:true}).click();
  await expect(page.getByLabel('Replay position',{exact:true})).toHaveValue('0');
  await page.getByRole('button',{name:'Play replay',exact:true}).click();
  await page.waitForTimeout(1600);await page.getByRole('button',{name:'Pause replay',exact:true}).click();
  const frozen=await page.getByLabel('Replay position',{exact:true}).inputValue();expect(Number(frozen)).toBeGreaterThan(0);
  await page.waitForTimeout(1200);await expect(page.getByLabel('Replay position',{exact:true})).toHaveValue(frozen);
  await page.getByRole('button',{name:'Playback speed 1x'}).click();await expect(page.getByRole('button',{name:'Playback speed 2x'})).toBeVisible();
  for(const name of ['Normal operation','Return pipe loss','Trap blowthrough','Return meter bias','Transport delay shift','Connection outage','Return meter interruption','Mode transition']){
    await page.getByRole('button',{name:new RegExp(`^${name}`)}).click();await expect(page.getByLabel('Replay position',{exact:true})).toHaveValue('0');
  }
  await page.getByRole('button',{name:/^Return diversion/}).click();
  const session=await sid(page);await page.request.post(`/api/v1/sessions/${session}/replay`,{data:{action:'seek',cursor:80}});
  await page.reload();await expect(page.getByRole('heading',{name:'Scenario Review',exact:true})).toBeVisible();
  await expect(page.getByLabel('Replay position',{exact:true})).toHaveValue('80');
  const before=await(await page.request.get(`/api/v1/sessions/${session}`)).json();
  await page.getByRole('button',{name:'Collapse sidebar'}).click();await expect(page.getByLabel('Replay position',{exact:true})).toHaveValue('80');
  await page.reload();await expect(page.locator('.sidebar')).toHaveCSS('width','76px');
  const after=await(await page.request.get(`/api/v1/sessions/${session}`)).json();expect(after.current).toEqual(before.current);
});

test('filter overlay all/return/quality, cancel, reset, contextual notifications/preferences/help and focus',async({page})=>{
  await boot(page);await page.getByRole('link',{name:'Event Center',exact:true}).click();
  for(const compact of [false,true]){
    if(compact)await page.getByRole('button',{name:'Collapse sidebar'}).click();
    await page.getByRole('button',{name:'Filters',exact:true}).click();
    const dialog=page.getByRole('dialog',{name:'Filter events'});await expect(dialog).toBeVisible();
    const bounds=await dialog.boundingBox();expect(Math.round(bounds!.width)).toBe(675);expect(Math.round(bounds!.height)).toBe(624);
    for(const [value,label]of [['all','All events'],['return','Return deficit'],['quality','Data quality']]){
      await dialog.getByRole('radio',{name:new RegExp(`^${label}`)}).check();await capture(page,`filter-${value}-${compact?'compact':'full'}`);
    }
    await dialog.getByRole('button',{name:'Apply filters'}).click();await expect(page.locator('.filter-toolbar')).toContainText('Data quality');
    await page.getByRole('button',{name:'Filters',exact:true}).click();await page.getByRole('button',{name:'Reset',exact:true}).click();await page.getByRole('button',{name:'Apply filters'}).click();
    await expect(page.locator('.filter-toolbar')).toContainText('All events');
    await page.getByRole('button',{name:'Filters',exact:true}).click();await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);await expect(page.getByRole('button',{name:'Filters',exact:true})).toBeFocused();
  }
  await page.getByRole('button',{name:/^Notifications/}).click();await capture(page,'notifications');await page.getByRole('button',{name:'Close Notifications'}).click();
  await expect(page.getByRole('heading',{name:'Signal events'})).toBeVisible();
  await page.getByRole('button',{name:'Preferences',exact:true}).click();await expect(page.getByRole('switch',{name:'Warning sound'})).toHaveAttribute('aria-checked','false');
  await page.getByRole('switch',{name:'Warning sound'}).click();await capture(page,'preferences');await page.getByRole('button',{name:'Save preferences'}).click();
  await page.reload();await page.getByRole('button',{name:'Preferences',exact:true}).click();await expect(page.getByRole('switch',{name:'Warning sound'})).toHaveAttribute('aria-checked','true');await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Help center',exact:true}).click();await capture(page,'help');await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Open workspace profile'}).click();await capture(page,'profile');await page.keyboard.press('Escape');
  await expect(page.getByRole('heading',{name:'Signal events'})).toBeVisible();await expect(page.locator('.sidebar')).toHaveCSS('width','76px');
});

test('four events have independent persisted checklists, real PDFs, A4 preview/print, accessible keyboard path',async({page})=>{
  await page.addInitScript(()=>{window.print=()=>{document.documentElement.dataset.printInvoked='true';};});
  await boot(page);await page.getByRole('link',{name:'Event Center',exact:true}).click();
  const session=await sid(page);const events=await(await page.request.get(`/api/v1/sessions/${session}/events`)).json();
  for(const event of events.slice(0,4)){
    await page.goto(`/#/events/${event.id}`);await expect(page.getByRole('heading',{name:`Event review / ${event.id}`})).toBeVisible();
    const checkbox=page.locator('.verification-list input').first();await checkbox.focus();await page.keyboard.press('Space');await expect(checkbox).toBeChecked();await expect(checkbox).toBeEnabled();
    await page.reload();await expect(page.locator('.verification-list input').first()).toBeChecked();
    await page.getByLabel('Inspection evidence / note').fill(`Browser QA evidence for ${event.id}`);
    await page.getByRole('button',{name:'Save draft',exact:true}).click();await expect(page.getByRole('button',{name:'Save draft',exact:true})).toBeEnabled();
    await page.reload();await expect(page.getByLabel('Inspection evidence / note')).toHaveValue(`Browser QA evidence for ${event.id}`);
    await page.getByRole('button',{name:'Record operator review',exact:true}).click();await expect(page.locator('.operator-status')).toContainText('submitted locally');
    await page.getByRole('button',{name:'View inspection summary'}).click();await expect(page.getByRole('dialog')).toContainText(event.id);
    if(event===events[0])await capture(page,'inspection-summary');
    const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download PDF'}).click();const file=await download;expect(file.suggestedFilename()).toContain(event.id);await file.saveAs(resolve(out,`${event.id}.pdf`));
    await page.getByRole('button',{name:'Print',exact:true}).click();await expect(page.getByRole('dialog',{name:`A4 inspection preview ${event.id}`})).toBeVisible();
    const report=page.frameLocator('#report-preview');
    await expect(page.getByRole('dialog').getByRole('button',{name:'Close',exact:true})).toHaveCount(1);
    await expect(report.getByRole('button')).toHaveCount(0);await expect(report.getByRole('heading',{name:'Inspection summary',exact:true})).toBeVisible();
    await expect.poll(()=>report.locator('html').getAttribute('data-print-invoked')).toBe('true');
    if(event===events[0]){
      await capture(page,'a4-preview');
      const printPage=await page.context().newPage();
      await printPage.goto(`/api/v1/sessions/${session}/events/${event.id}/print`);
      await printPage.evaluate(()=>document.fonts.ready);
      await printPage.getByRole('article',{name:'A4 inspection summary'}).screenshot({path:resolve(out,'a4-document.png')});
      await printPage.pdf({path:resolve(out,'browser-print.pdf'),format:'A4',printBackground:true});
      await printPage.close();
    }
    await page.getByRole('button',{name:'Back to summary',exact:true}).click();await page.getByRole('button',{name:'Close',exact:true}).click();await expect(page.getByRole('heading',{name:`Event review / ${event.id}`})).toBeVisible();
  }
});

test('accessibility, focus trap, reduced motion and narrower desktop remain usable',async({page})=>{
  await boot(page);await page.emulateMedia({reducedMotion:'reduce'});
  const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  writeFileSync(resolve(out,'accessibility-overview.json'),JSON.stringify(scan.violations,null,2));expect(scan.violations).toEqual([]);
  await page.getByRole('button',{name:'Help center',exact:true}).click();
  for(let i=0;i<8;i++){await page.keyboard.press('Tab');expect(await page.getByRole('dialog').evaluate(el=>el.contains(document.activeElement))).toBe(true);}
  await page.keyboard.press('Escape');await expect(page.getByRole('button',{name:'Help center',exact:true})).toBeFocused();
  await page.setViewportSize({width:1180,height:900});await capture(page,'overview-narrow');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(1180);
});

test('warning audio requires opt-in and a newly crossed detector event; no mount cue',async({page})=>{
  await page.addInitScript(()=>{
    (window as unknown as {audioCalls:number}).audioCalls=0;
    window.Audio=class {volume=1;play(){(window as unknown as {audioCalls:number}).audioCalls++;return Promise.resolve();}} as unknown as typeof Audio;
  });
  await boot(page);
  const calls=()=>page.evaluate(()=>(window as unknown as {audioCalls:number}).audioCalls);
  expect(await calls()).toBe(0);
  const session=await sid(page);
  const state=await(await page.request.get(`/api/v1/sessions/${session}`)).json();
  const latest=state.events.find((e:{category:string})=>e.category==='return');
  const before=Math.round((Date.parse(latest.timestamp)-Date.parse(state.scenario.start_timestamp))/60000)-1;
  expect(before).toBeGreaterThan(0);
  await page.getByRole('button',{name:'Preferences',exact:true}).click();
  await page.getByRole('switch',{name:'Warning sound'}).click();await page.getByRole('button',{name:'Save preferences'}).click();
  expect(await calls()).toBe(0);
  await page.getByRole('link',{name:'Scenario Review',exact:true}).click();
  await page.getByLabel('Replay position',{exact:true}).fill(String(before));
  await page.getByLabel('Replay position',{exact:true}).dispatchEvent('pointerup');
  await expect(page.getByRole('button',{name:'Play replay',exact:true})).toBeEnabled();
  await expect(page.getByLabel('Replay position',{exact:true})).toHaveValue(String(before));
  expect(await calls()).toBe(0);
  await page.getByRole('button',{name:'Play replay',exact:true}).click();
  await expect.poll(calls,{timeout:7000}).toBe(1);
  await page.getByRole('button',{name:'Pause replay',exact:true}).click();
  await page.reload();await expect(page.getByRole('heading',{name:'Scenario Review',exact:true})).toBeVisible();expect(await calls()).toBe(0);
});
