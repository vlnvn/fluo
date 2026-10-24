import { chromium } from '../web/node_modules/playwright/index.mjs';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const out=resolve('docs/implementation/qa/post-audit/after');mkdirSync(out,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:process.env.FLUO_BROWSER_PATH??'C:/Users/Valensius Alven/AppData/Local/ms-playwright/chromium-1243/chrome-win64/chrome.exe'});
const context=await browser.newContext({baseURL:process.env.FLUO_BASE_URL??'http://127.0.0.1:8000',viewport:{width:1440,height:900},recordVideo:{dir:resolve(out,'video'),size:{width:1440,height:900}}});
const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
const measurements=[];
try{
  await page.goto(process.env.FLUO_BASE_URL??'http://127.0.0.1:8000');await page.locator('h1').waitFor();if(await page.getByRole('button',{name:'Start guest workspace',exact:true}).isVisible())await page.getByRole('button',{name:'Start guest workspace',exact:true}).click();await page.locator('h1').filter({hasText:'Condensate return'}).waitFor();await page.evaluate(()=>document.fonts.ready);
  const session=await page.evaluate(()=>localStorage.getItem('fluo.session.v1'));
  const state=await(await page.request.get(`/api/v1/sessions/${session}`)).json();
  for(const compact of [false,true]){
    if(compact)await page.getByRole('button',{name:'Collapse sidebar'}).click();
    for(const [path,name] of [['/','overview'],['/scenarios','scenarios'],['/events','events'],[`/events/${state.events[0].id}`,'details']]){
      await page.goto(`${process.env.FLUO_BASE_URL??'http://127.0.0.1:8000'}/#${path}`);await page.locator(`.page-${name}`).waitFor();await page.locator('.card').first().waitFor();await page.mouse.move(1400,880);
      measurements.push(await page.evaluate(({name,compact})=>{
        const rect=selector=>{const r=document.querySelector(selector).getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height};};
        return{name,compact,header:rect('.header'),sidebar:rect('.sidebar'),firstCard:rect('.card'),overflow:document.documentElement.scrollWidth-innerWidth};
      },{name,compact}));
      await page.screenshot({path:resolve(out,`probe-${name}-${compact?'compact':'full'}.png`),animations:'disabled'});
    }
  }
  for(const width of [1280,1024]){
    await page.setViewportSize({width,height:900});await page.goto(`${process.env.FLUO_BASE_URL??'http://127.0.0.1:8000'}/#/events`);await page.locator('.page-events').waitFor();
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);measurements.push({name:'additional-desktop',compact:true,width,overflow});if(overflow>0)throw new Error(`Horizontal overflow at ${width}`);
    await page.screenshot({path:resolve(out,`events-compact-${width}.png`),animations:'disabled'});
  }
  await page.setViewportSize({width:1440,height:900});await page.goto(`${process.env.FLUO_BASE_URL??'http://127.0.0.1:8000'}/#/scenarios`);await page.locator('.page-scenarios').waitFor();
  const slider=page.getByLabel('Replay position',{exact:true});await slider.scrollIntoViewIfNeeded();const r=await slider.boundingBox();await page.mouse.move(r.x+r.width*.2,r.y+r.height/2);await page.mouse.down();
  for(let i=0;i<30;i++){await page.mouse.move(r.x+r.width*(.2+i*.02),r.y+r.height/2);await page.waitForTimeout(35);}
  await page.waitForTimeout(200);await page.mouse.up();await page.waitForTimeout(300);
  writeFileSync(resolve(out,'geometry-final.json'),JSON.stringify({browser:browser.version(),platform:process.platform,deviceScaleFactor:1,reducedMotion:'no-preference (motion recording); screenshots animations disabled',measurements,consoleErrors:errors},null,2));
  if(errors.length)throw new Error(errors.join('\n'));
}finally{await context.close();await browser.close();}
