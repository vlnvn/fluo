// Verify the official temporary share path in a fresh browser, without OIDC headers.
import {chromium} from '../web/node_modules/playwright/index.mjs';
import {readFileSync,writeFileSync} from 'node:fs';
let phase='initialize';
process.on('uncaughtException',error=>{console.error(JSON.stringify({status:'FAIL',phase,error:error.name,message:error.message.split('\n')[0].replace(/https:\/\/[^\s"']+/g,'[URL redacted]')}));process.exit(1);});
const link=JSON.parse(readFileSync('.local/reviewer-link.json','utf8'));
const target=new URL(link.shareableUrl);
if(target.protocol!=='https:'||target.origin!==process.env.FLUO_BASE_URL)throw Error('Explicit verified FLUO_BASE_URL must match the share origin');
const browser=await chromium.launch({headless:true,executablePath:process.env.FLUO_BROWSER_PATH??'C:/Users/Valensius Alven/AppData/Local/ms-playwright/chromium-1243/chrome-win64/chrome.exe'});
const context=await browser.newContext({viewport:{width:1440,height:900}});
const page=await context.newPage();
phase='navigate';await page.goto(link.shareableUrl);
await page.getByRole('button',{name:'Start guest workspace',exact:true}).waitFor();
phase='guest entry';await page.getByRole('button',{name:'Start guest workspace',exact:true}).click();
await page.getByRole('heading',{name:'Condensate return',exact:true,level:1}).waitFor();
await page.reload();await page.getByRole('heading',{name:'Condensate return',exact:true,level:1}).waitFor();
await page.evaluate(()=>document.fonts.ready);
await page.screenshot({path:'.local/hosted-reviewer-overview.png'});
phase='logout';await page.getByRole('button',{name:'Open workspace profile'}).click();
await page.getByRole('button',{name:'End guest session',exact:true}).click();
await page.getByRole('button',{name:'Start guest workspace',exact:true}).waitFor();
const evidence={status:'PASS',url:target.origin,date:new Date().toISOString(),provider_oidc_header_used:false,
 checks:['Official temporary share link opened in fresh Chromium','App guest entry required','Real overview rendered','Refresh retained own workspace','App logout returned to entry'],
 share_link_note:link.info,share_capability_omitted:true};
writeFileSync('docs/implementation/qa/vercel/reviewer-access.json',JSON.stringify(evidence,null,2));
await browser.close();console.log(JSON.stringify({status:'PASS',checks:evidence.checks.length}));
