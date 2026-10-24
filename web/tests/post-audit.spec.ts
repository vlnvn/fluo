import { enterGuest } from './guest';
import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { timeLabel } from '../src/api';

const out=resolve('../docs/implementation/qa/post-audit/after');mkdirSync(out,{recursive:true});
async function boot(page:Page){await enterGuest(page);await expect(page.locator('h1')).toHaveText('Condensate return');await page.evaluate(()=>document.fonts.ready);}
async function state(page:Page){const id=await page.evaluate(()=>localStorage.getItem('fluo.session.v1'));return (await page.request.get(`/api/v1/sessions/${id}`)).json();}
async function axe(page:Page,name:string){const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();writeFileSync(resolve(out,`axe-${name}.json`),JSON.stringify(scan.violations,null,2));expect(scan.violations,JSON.stringify(scan.violations)).toEqual([]);}

test('live scrub previews real frames without committing; playing clock cannot pull thumb back',async({page})=>{
  await boot(page);await page.getByRole('link',{name:'Scenario Review',exact:true}).click();
  const slider=page.getByLabel('Replay position',{exact:true});await slider.scrollIntoViewIfNeeded();
  const original=await state(page);let seekCount=0;
  page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/replay')&&r.postDataJSON().action==='seek')seekCount++;});
  const before=await page.locator('[data-series="steam"]').getAttribute('d');
  const box=(await slider.boundingBox())!;
  await page.mouse.move(box.x+box.width*.15,box.y+box.height/2);await page.mouse.down();
  await page.mouse.move(box.x+box.width*.7,box.y+box.height/2,{steps:35});
  const cursor=Number(await slider.inputValue());
  await expect(page.locator('.data-provenance')).toContainText('cursor preview');
  const timestamp=new Date(Date.parse(original.scenario.start_timestamp)+cursor*60000).toISOString();
  await expect(page.locator('.playback-card h2')).toContainText(timeLabel(timestamp));
  expect(await page.locator('[data-series="steam"]').getAttribute('d')).not.toBe(before);
  expect((await state(page)).cursor).toBe(original.cursor);expect(seekCount).toBe(0);
  await page.screenshot({path:resolve(out,'live-scrub-preview.png'),animations:'disabled'});
  await page.mouse.up();await expect.poll(()=>seekCount).toBe(1);await expect(slider).toBeEnabled();
  await expect(page.locator('.data-provenance')).not.toContainText('cursor preview');
  expect((await state(page)).cursor).toBe(cursor);
  // Clicking the existing thumb without moving must not leave transport locked.
  await slider.click();await expect(page.getByRole('button',{name:'Play replay',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'Playback speed 1x'}).click();await page.getByRole('button',{name:'Play replay',exact:true}).click();
  await slider.scrollIntoViewIfNeeded();const moving=(await slider.boundingBox())!;
  await page.mouse.move(moving.x+moving.width*.3,moving.y+moving.height/2);await page.mouse.down();
  await page.mouse.move(moving.x+moving.width*.4,moving.y+moving.height/2,{steps:20});const held=await slider.inputValue();
  await page.waitForTimeout(1200);await expect(slider).toHaveValue(held);await page.mouse.up();
  await page.getByRole('button',{name:'Pause replay',exact:true}).click();
  const frozen=(await state(page)).cursor;await page.waitForTimeout(700);expect((await state(page)).cursor).toBe(frozen);
});

test('all core routes and contextual dialogs pass scoped Axe; four event contexts in both shells',async({page})=>{
  test.setTimeout(120000);await page.addInitScript(()=>{window.print=()=>{};});await boot(page);
  const events=(await state(page)).events.slice(0,4);
  await axe(page,'overview');
  for(const name of ['Scenario Review','Event Center']){await page.getByRole('link',{name,exact:true}).click();await expect(page.getByRole('link',{name,exact:true})).toHaveAttribute('aria-current','page');await axe(page,name.replaceAll(' ','-'));}
  for(const compact of [false,true]){
    if(compact)await page.getByRole('button',{name:'Collapse sidebar'}).click();
    for(const event of events){await page.goto(`/#/events/${event.id}`);await expect(page.locator('h1')).toHaveText(`Event review / ${event.id}`);await page.screenshot({path:resolve(out,`${event.id}-${compact?'compact':'full'}.png`),animations:'disabled'});}
  }
  await axe(page,'details');
  for(const name of ['Help center','Preferences','Open workspace profile']){await page.getByRole('button',{name,exact:true}).click();await axe(page,name.replaceAll(' ','-'));await page.keyboard.press('Escape');}
  await page.locator('.notification-button').click();await axe(page,'notifications');await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'View inspection summary',exact:true}).click();await axe(page,'summary');await page.keyboard.press('Escape');
  await page.getByRole('link',{name:'Event Center',exact:true}).click();await page.getByRole('button',{name:'Filters',exact:true}).click();await axe(page,'filter');await page.keyboard.press('Escape');
});

test('favicon, original chime decoding/media delivery, error recovery and malformed deep link',async({page})=>{
  let creates=0;page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/sessions'))creates++;});
  await boot(page);expect(creates).toBe(1);
  for(const file of ['/favicon.svg','/favicon.ico','/icon-192.png','/apple-touch-icon.png','/manifest.webmanifest'])expect((await page.request.get(file)).status()).toBe(200);
  await expect(page.locator('link[rel="icon"][type="image/svg+xml"]')).toHaveAttribute('href','/favicon.svg');
  const audio=await page.request.get('/assets/notification-chime.mp3',{headers:{Range:'bytes=0-1023'}});expect(audio.status()).toBe(206);
  const duration=await page.evaluate(async()=>{const buffer=await(await fetch('/assets/notification-chime.mp3')).arrayBuffer();const context=new AudioContext();try{return(await context.decodeAudioData(buffer)).duration;}finally{await context.close();}});expect(duration).toBeGreaterThan(0);
  await page.goto('/#/events/%E0%A4%A');await expect(page.locator('.loading-state')).toContainText('Event unavailable');
  await page.getByRole('button',{name:'Event Center',exact:true}).click();await expect(page.locator('h1')).toHaveText('Signal events');
  await page.route('**/api/v1/scenarios',route=>route.fulfill({status:500,contentType:'application/json',body:'{"error":{"code":"TEST_FAILURE","message":"Unavailable during QA"}}'}));
  await page.reload();await expect(page.locator('h1')).toHaveText('Local service unavailable');await expect(page.getByRole('button',{name:'Retry connection'})).toBeVisible();
  await page.unroute('**/api/v1/scenarios');await page.getByRole('button',{name:'Retry connection'}).click();await expect(page.locator('h1')).toHaveText('Signal events');
  writeFileSync(resolve(out,'media-runtime.json'),JSON.stringify({audioSeconds:duration,browser:page.context().browser()?.version(),viewport:page.viewportSize(),fonts:await page.evaluate(()=>document.fonts.status)},null,2));
});

test('new warning surfaces a notice across routes; seek is silent and autoplay denial is truthful',async({page})=>{
  await page.addInitScript(()=>{window.Audio=class {volume=1;play(){return Promise.reject(new DOMException('Autoplay blocked','NotAllowedError'));}} as unknown as typeof Audio;});
  await boot(page);const initial=await state(page);const event=initial.events.find((e:{category:string})=>e.category==='return');
  const before=Math.round((Date.parse(event.timestamp)-Date.parse(initial.scenario.start_timestamp))/60000)-1;
  await page.getByRole('link',{name:'Scenario Review',exact:true}).click();
  await page.getByLabel('Replay position',{exact:true}).fill(String(before));await page.getByLabel('Replay position',{exact:true}).dispatchEvent('pointerup');
  await expect(page.getByRole('button',{name:'Play replay',exact:true})).toBeEnabled();
  await expect(page.locator('.toast')).toHaveCount(0);
  await page.getByRole('button',{name:'Play replay',exact:true}).click();
  await page.getByRole('link',{name:'Event Center',exact:true}).click();
  await expect(page.locator('.toast')).toContainText('New return-flow warning');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button',{name:'Review warning',exact:true}).click();await expect(page.locator('h1')).toContainText(event.id);
  await page.getByRole('button',{name:'Preferences',exact:true}).click();await page.getByRole('switch',{name:'Warning sound'}).click();await page.getByRole('button',{name:'Save preferences'}).click();
  await page.getByRole('link',{name:'Scenario Review',exact:true}).click();await page.getByRole('button',{name:'Pause replay',exact:true}).click();
  await page.getByLabel('Replay position',{exact:true}).fill(String(before));await page.getByLabel('Replay position',{exact:true}).dispatchEvent('pointerup');
  await expect(page.getByRole('button',{name:'Play replay',exact:true})).toBeEnabled();await page.getByRole('button',{name:'Play replay',exact:true}).click();
  await expect(page.locator('.toast')).toContainText('browser blocked the audio cue');
});

test('touch scrub previews actual data; delayed preview cannot overwrite committed seek',async({page})=>{
  await boot(page);await page.getByRole('link',{name:'Scenario Review',exact:true}).click();
  const slider=page.getByLabel('Replay position',{exact:true});await slider.scrollIntoViewIfNeeded();const box=(await slider.boundingBox())!;
  const cdp=await page.context().newCDPSession(page);let seeks=0;
  page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/replay')&&r.postDataJSON().action==='seek')seeks++;});
  const y=box.y+box.height/2;
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:box.x+box.width*.2,y}]});
  for(let i=0;i<12;i++){await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:box.x+box.width*(.2+i*.035),y}]});}
  await expect(page.locator('.data-provenance')).toContainText('cursor preview');const cursor=await slider.inputValue();expect(seeks).toBe(0);
  await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await expect.poll(()=>seeks).toBe(1);await expect(slider).toBeEnabled();await expect(slider).toHaveValue(cursor);
  await page.route('**/preview?*',async route=>{await new Promise(resolve=>setTimeout(resolve,400));await route.continue().catch(()=>{});});
  await slider.fill('20');await slider.dispatchEvent('pointerup');await expect(slider).toBeEnabled();await page.waitForTimeout(600);await expect(slider).toHaveValue('20');expect((await state(page)).cursor).toBe(20);
  await cdp.detach();
});

test('opt-in chime actually starts through native media playback',async({page})=>{
  await page.addInitScript(()=>{
    const original=HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play=function(){return original.call(this).then(()=>{document.documentElement.dataset.nativeAudioStarted='true';});};
  });
  await boot(page);const initial=await state(page);const event=initial.events.find((e:{category:string})=>e.category==='return');const before=Math.round((Date.parse(event.timestamp)-Date.parse(initial.scenario.start_timestamp))/60000)-1;
  await page.getByRole('button',{name:'Preferences',exact:true}).click();await page.getByRole('switch',{name:'Warning sound'}).click();await page.getByRole('button',{name:'Save preferences'}).click();
  await page.getByRole('link',{name:'Scenario Review',exact:true}).click();await page.getByLabel('Replay position',{exact:true}).fill(String(before));await page.getByLabel('Replay position',{exact:true}).dispatchEvent('pointerup');
  await expect(page.getByRole('button',{name:'Play replay',exact:true})).toBeEnabled();await page.getByRole('button',{name:'Play replay',exact:true}).click();await expect(page.locator('html')).toHaveAttribute('data-native-audio-started','true');
  writeFileSync(resolve(out,'native-audio.json'),JSON.stringify({nativePlayResolved:true,browser:page.context().browser()?.version(),acousticOutputMeasured:false}));
});

test('rapid review actions save once, 409 is visible, and empty/backdrop states remain usable',async({page})=>{
  await boot(page);const initial=await state(page);const event=initial.events[0];await page.goto(`/#/events/${event.id}`);await expect(page.locator('h1')).toContainText(event.id);
  let writes=0;page.on('request',r=>{if(r.method()==='PUT'&&r.url().endsWith('/review'))writes++;});
  await page.getByLabel('Inspection evidence / note').fill('QA double click: one saved revision.');
  await page.getByRole('button',{name:'Save draft',exact:true}).evaluate(button=>{(button as HTMLButtonElement).click();(button as HTMLButtonElement).click();});
  await expect(page.getByRole('button',{name:'Save draft',exact:true})).toBeEnabled();expect(writes).toBe(1);
  await page.route('**/review',route=>route.fulfill({status:409,contentType:'application/json',body:'{"error":{"code":"REVISION_CONFLICT","message":"Review changed; reload before saving."}}'}));
  await page.getByRole('button',{name:'Save draft',exact:true}).click();await expect(page.getByRole('alert')).toContainText('reload before saving');
  await page.unroute('**/review');await page.reload();await expect(page.getByLabel('Inspection evidence / note')).toHaveValue('QA double click: one saved revision.');
  await page.getByRole('link',{name:'Event Center',exact:true}).click();await page.getByLabel('Search events').fill('no-such-event-qa-20261025');await expect(page.locator('.empty-state')).toHaveText('No events match this filter.');
  await page.getByLabel('Search events').fill('');await page.getByRole('button',{name:'Filters',exact:true}).click();await page.mouse.click(10,10);await expect(page.getByRole('dialog')).toHaveCount(0);await expect(page.getByRole('button',{name:'Filters',exact:true})).toBeFocused();
});
