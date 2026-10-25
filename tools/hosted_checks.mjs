// Actual HTTPS checks. Provider and guest credentials stay in ignored files.
import {request} from '../web/node_modules/playwright/index.mjs';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
process.on('uncaughtException', error => {
 console.error(JSON.stringify({status:'FAIL',error:error.name,message:error.message.split('\n')[0]}));
 process.exit(1);
});
const base=process.env.FLUO_BASE_URL;
if(!base||new URL(base).protocol!=='https:'||!new URL(base).hostname.endsWith('.vercel.app'))throw new Error('An explicit Vercel HTTPS origin is required');
const env=Object.fromEntries(readFileSync('.local/fluo-development.env','utf8').split(/\r?\n/).filter(x=>x&&!x.startsWith('#')&&x.includes('=')).map(line=>{const i=line.indexOf('=');const v=line.slice(i+1);return[line.slice(0,i),v.startsWith('"')?JSON.parse(v):v];}));
const token=env.VERCEL_OIDC_TOKEN;
if(!token)throw new Error('Refresh the project development OIDC credentials');
const mode=process.argv.includes('--verify')?'verify':'capture';
const out='docs/implementation/qa/vercel';mkdirSync(out,{recursive:true});
const context=async(storageState)=>request.newContext({baseURL:base,extraHTTPHeaders:{'x-vercel-trusted-oidc-idp-token':token},...(storageState?{storageState}:{}),timeout:30000});
const checks=[];
function check(name,actual,expected){if(actual!==expected)throw new Error(`${name}: expected ${expected}, received ${actual}`);checks.push({name,pass:true});}
async function enter(client){const r=await client.post('/api/v1/auth/guest',{headers:{'X-Fluo-Intent':'guest'},data:{}});check('guest entry HTTP',r.status(),200);return(await r.json()).csrf_token;}
function scopedState(state){return{...state,cookies:state.cookies.map(c=>({...c,domain:new URL(base).hostname}))};}
const anchorFile='.local/hosted-proof-private.json';
let report={url:base,date:new Date().toISOString(),mode,checks,public_anonymous_provider_access:false};
if(mode==='capture'){
 const anonymous=await context();const a=await context();const b=await context();
 const started=Date.now();const ready=await anonymous.get('/health/ready');check('readiness',ready.status(),200);report.first_observed_ready_ms=Date.now()-started;
 const csrf=await enter(a);const otherCsrf=await enter(b);
 const created=await a.post('/api/v1/sessions',{headers:{'X-CSRF-Token':csrf},data:{}});check('owned session create',created.status(),201);
 const state=await created.json();const sid=state.session_id;const event=state.events.find(e=>e.category==='return')??state.events[0];
 const root=`/api/v1/sessions/${sid}`;
 for(const suffix of ['', '/preview?cursor=0','/preferences','/events',...state.events.slice(0,4).flatMap(e=>['','/report.pdf','/print','/print?embedded=true'].map(s=>`/events/${e.id}${s}`))]){
  check(`anonymous ${suffix}`, (await anonymous.get(root+suffix)).status(),401);
  check(`foreign guest ${suffix}`, (await b.get(root+suffix)).status(),404);
 }
 for(const [verb,suffix,data] of [['post','/replay',{action:'reset'}],['put','/preferences',{warning_sound:true}],['put',`/events/${event.id}/review`,{checked_steps:[],note:'foreign attempt',revision:0}],['post',`/events/${event.id}/review/submit`,{checked_steps:[],note:'foreign attempt',revision:0}]])check('foreign write '+suffix,(await b[verb](root+suffix,{headers:{'X-CSRF-Token':otherCsrf},data})).status(),404);
 check('CSRF rejection',(await a.post(root+'/replay',{data:{action:'reset'}})).status(),403);
 check('hostile origin',(await a.post(root+'/replay',{headers:{'X-CSRF-Token':csrf,Origin:'https://evil.invalid'},data:{action:'reset'}})).status(),403);
 check('public raw inference forbidden',(await a.post('/api/v1/inference',{headers:{'X-CSRF-Token':csrf},data:{}})).status(),403);
 check('malformed request',(await a.post('/api/v1/sessions',{headers:{'X-CSRF-Token':csrf,'Content-Type':'application/json'},data:'{'})).status(),422);
 check('body limit',(await a.post('/api/v1/sessions',{headers:{'X-CSRF-Token':csrf},data:Buffer.alloc(4*1024*1024+1)})).status(),413);
 for(const path of ['/docs','/redoc','/openapi.json','/.env','/.git/config','/models/fluo_hgb_synthetic_v2.joblib','/data/original/fluo_sensor_stream.csv.gz']){
  const status=(await a.get(path)).status();check('private route denied '+path,[400,403,404].includes(status),true);
 }
 const note='Hosted persistence proof from verified Fluo release; synthetic demo.';
 const saved=await a.put(root+`/events/${event.id}/review`,{headers:{'X-CSRF-Token':csrf},data:{checked_steps:[],note,revision:0}});check('review draft',saved.status(),200);
 const submitted=await a.post(root+`/events/${event.id}/review/submit`,{headers:{'X-CSRF-Token':csrf},data:{checked_steps:[],note,revision:1}});check('review submit',submitted.status(),200);
 check('preferences write',(await a.put(root+'/preferences',{headers:{'X-CSRF-Token':csrf},data:{warning_sound:true}})).status(),200);
 const pdf=await a.get(root+`/events/${event.id}/report.pdf`);check('real PDF',pdf.status(),200);check('PDF type',pdf.headers()['content-type'].startsWith('application/pdf'),true);const bytes=await pdf.body();check('PDF magic',bytes.subarray(0,4).toString(),'%PDF');writeFileSync('.local/hosted-event.pdf',bytes);report.pdf_bytes=bytes.length;
 const html=await a.get(root+`/events/${event.id}/print?embedded=true`);check('actual HTML report',html.status(),200);check('nonce CSP',html.headers()['content-security-policy'].includes("'nonce-"),true);
 const health=await(await a.get('/api/v1/health')).json();check('frozen model SHA',health.lineage.model_sha256,'5237917ae6ccfccd2ff21d288b92201536c923028d8931599aaf9715033e9b09');
 check('runtime parity digest',health.runtime_proof.runtime_output_sha256,'2f334f76816f7cff05f843d77f64a85f393e2ca18336c4acae33eec320a34ac3');check('runtime rows',health.runtime_proof.runtime_rows,51840);
 const cookies=(await a.storageState()).cookies;const guest=cookies.find(c=>c.name==='__Host-fluo_guest');check('cookie Secure',guest?.secure,true);check('cookie HttpOnly',guest?.httpOnly,true);check('cookie SameSite',guest?.sameSite,'Strict');check('HSTS',ready.headers()['strict-transport-security'],'max-age=31536000');
 const logoutState=await b.storageState();check('logout',(await b.post('/api/v1/auth/logout',{headers:{'X-CSRF-Token':otherCsrf}})).status(),204);const revoked=await context(logoutState);check('revoked cookie',(await revoked.get('/api/v1/auth/session')).status(),401);await revoked.dispose();
 writeFileSync(anchorFile,JSON.stringify({url:base,storageState:await a.storageState(),csrf,sid,event:event.id,noteHash:createHash('sha256').update(note).digest('hex'),instance:health.startup_metrics.instance_id},null,2));
 report.health=health;report.persistence_anchor_created=true;await Promise.all([a.dispose(),b.dispose(),anonymous.dispose()]);
}else{
 const anchor=JSON.parse(readFileSync(anchorFile,'utf8'));const client=await context(scopedState(anchor.storageState));
 const root=`/api/v1/sessions/${anchor.sid}`;const state=await client.get(root);check('session after redeploy',state.status(),200);
 const detail=await(await client.get(root+`/events/${anchor.event}`)).json();check('review revision survives',detail.review.revision,2);check('review submission survives',detail.review.status,'submitted');check('review note survives',createHash('sha256').update(detail.review.note).digest('hex'),anchor.noteHash);
 check('preferences survive',(await(await client.get(root+'/preferences')).json()).warning_sound,true);
 const health=await(await client.get('/api/v1/health')).json();check('new function instance',health.startup_metrics.instance_id!==anchor.instance,true);check('runtime digest after redeploy',health.runtime_proof.runtime_output_sha256,'2f334f76816f7cff05f843d77f64a85f393e2ca18336c4acae33eec320a34ac3');report.health=health;report.previous_url=anchor.url;report.cookie_scope_note='Own test credential transferred to the new verified deployment hostname for cross-instance storage verification; this does not claim browsers share cookies across domains.';
 await client.dispose();
}
report.status='PASS';writeFileSync(`${out}/hosted-${mode}.json`,JSON.stringify(report,null,2));console.log(JSON.stringify({status:report.status,url:base,mode,checks:checks.length}));
