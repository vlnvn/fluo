import { expect, test as base, type BrowserContext, type Page } from '@playwright/test';

export async function authorizeProvider(context:BrowserContext,baseURL:string){
  const token=process.env.FLUO_VERCEL_OIDC_TOKEN;
  if(!token)return;
  const origin=new URL(baseURL).origin;
  if(!origin.startsWith('https://')||!new URL(origin).hostname.endsWith('.vercel.app'))throw new Error('Provider token requires the explicit Vercel HTTPS test origin');
  await context.route(`${origin}/**`,route=>route.continue({headers:{...route.request().headers(),'x-vercel-trusted-oidc-idp-token':token}}));
  // Browser routing does not cover page.request. Scope its API headers too.
  const client=context.request;
  for(const verb of ['get','post','put'] as const){
    const original=client[verb].bind(client);
    client[verb]=(url,options)=>original(url,{...options,headers:{...(new URL(url,origin).origin===origin?{'x-vercel-trusted-oidc-idp-token':token}:{}),...options?.headers}});
  }
}

export const test=base.extend({context:async({context,baseURL},runContext)=>{
  if(baseURL)await authorizeProvider(context,baseURL);
  await runContext(context);
  if(process.env.FLUO_VERCEL_OIDC_TOKEN){
    // Revoke only this disposable test guest; preserve the separate redeploy proof.
    const auth=await context.request.get('/api/v1/auth/session');
    if(auth.ok())await context.request.post('/api/v1/auth/logout',{headers:{'X-CSRF-Token':(await auth.json()).csrf_token}});
  }
}});
export async function enterGuest(page:Page){
  await page.goto('/');
  await expect(page.locator('h1')).toHaveText(/Your private guest workspace|Condensate return/);
  const entry=page.getByRole('button',{name:'Start guest workspace',exact:true});
  if(await entry.isVisible())await entry.click();
  await expect(page.locator('h1')).toHaveText('Condensate return');
}
export async function csrfHeaders(page:Page){const auth=await(await page.request.get('/api/v1/auth/session')).json();return {'X-CSRF-Token':auth.csrf_token};}
