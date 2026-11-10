const fs=require('fs'),path=require('path'),assert=require('assert'),{spawnSync}=require('child_process'),{chromium}=require('playwright');
const python=process.env.PYTHON||(process.platform==='win32'?path.join(__dirname,'../.venv/Scripts/python.exe'):'python3');
const r=spawnSync(python,[path.join(__dirname,'test_souvenirs_fixtures.py')],{encoding:'utf8'});if(r.status)throw Error(r.stderr);const fixture=JSON.parse(r.stdout);
(async()=>{const browser=await chromium.launch({headless:true,channel:process.env.BROWSER_CHANNEL||'msedge'});try{
for(const mode of ['allowed','blocked','error']){
 const context=await browser.newContext({viewport:{width:390,height:844}});
 await context.addInitScript(mode=>{
  // Playback is simulated; ignore decoder errors from the placeholder fixture.
  document.addEventListener('error',e=>{if(e.target instanceof HTMLMediaElement)e.stopImmediatePropagation()},true);
  window.playCalls=[];let paused=true;
  Object.defineProperty(HTMLMediaElement.prototype,'paused',{get(){return paused}});
  HTMLMediaElement.prototype.play=function(){window.playCalls.push(this.muted);if(mode==='error')return Promise.reject(new DOMException('Bad file','NotSupportedError'));if(mode==='blocked'&&!this.muted&&!window.clicked)return Promise.reject(new DOMException('Gesture required','NotAllowedError'));paused=false;this.dispatchEvent(new Event('playing'));return Promise.resolve()};
 },mode);
 await context.route('https://**/**',route=>{const u=new URL(route.request().url());if(u.pathname.startsWith('/static/'))return route.fulfill({body:fs.readFileSync(path.join(__dirname,u.pathname.slice(1))),contentType:u.pathname.endsWith('.js')?'application/javascript':'text/css'});if(u.pathname.includes('/assets/'))return route.fulfill({body:Buffer.from(fixture.image,'base64'),contentType:'image/png'});return route.fulfill({body:fixture.video_detail,contentType:'text/html'})});
 const page=await context.newPage();await page.goto('https://souvenirs.test/p/test/');await page.waitForFunction(()=>window.playCalls.length>0);
 if(mode==='allowed'){await page.waitForFunction(()=>document.getElementById('svListen').hidden);assert.deepEqual(await page.evaluate(()=>window.playCalls),[false])}
 else if(mode==='blocked'){await page.waitForFunction(()=>window.playCalls.length===2);assert.deepEqual(await page.evaluate(()=>window.playCalls),[false,true]);assert(await page.locator('#svListen').isVisible());await page.evaluate(()=>window.clicked=true);await page.locator('#svListen').click();await page.waitForFunction(()=>document.getElementById('svListen').hidden);assert.equal(await page.locator('video').evaluate(v=>v.muted),false)}
 else {await page.waitForFunction(()=>document.getElementById('svVideoStatus').textContent.includes('Chưa phát'));assert(await page.locator('#svListen').isVisible())}
 for(const viewport of [{width:390,height:844},{width:1366,height:900}]){await page.setViewportSize(viewport);const box=await page.locator('#svIntroVideo').boundingBox();assert(box.y<viewport.height/2);assert(box.y+box.height<viewport.height);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))}
 await context.close();
}
console.log('PASS: featured video visible above fold desktop/mobile; audible autoplay, blocked-muted fallback, one-click sound and media error states.');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
