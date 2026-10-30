const fs=require('fs'),path=require('path'),assert=require('assert'),{chromium}=require('playwright');
(async()=>{const browser=await chromium.launch({headless:true,channel:process.env.BROWSER_CHANNEL||'msedge'});try{
 const context=await browser.newContext(),errors=[];let allowed=true,submitted=null,requests=0;
 const row={id:'one',bookingCode:'ST-PAID',date:'2026-10-30',agent:'nv1',ticketId:'eco',ticketType:'Eco',qty:2,sellPrice:500000,revenue:1000000,paid:1000000,balance:0,paymentMethod:'cash',paymentPending:false,paymentStatus:'completed',paymentRevision:0};
 await context.route('http://sunny.test/**',async route=>{const req=route.request(),url=new URL(req.url());
  if(url.pathname==='/api/counter/')return route.fulfill({json:{today:'2026-10-30',seller:'nv1',tickets:[{id:'eco',name:'Eco',product:'Hội An',ready:true}],bookings:[row],canCreate:true}});
  if(url.pathname==='/api/counter/bookings/one/')return route.fulfill({json:{booking:row,version:1,canChange:false,canReopenPayment:allowed&&!row.paymentPending,history:[]}});
  if(url.pathname.endsWith('/reopen-payment/')){requests++;submitted=req.postDataJSON();Object.assign(row,{paid:0,balance:1000000,paymentPending:true,paymentStatus:'pending_payment',paymentMethod:submitted.paymentMethod,paymentRevision:1});return route.fulfill({json:{booking:row}})}
  if(url.pathname.startsWith('/static/'))return route.fulfill({body:fs.readFileSync(path.join(__dirname,url.pathname.slice(1))),contentType:'application/javascript'});
  return route.fulfill({contentType:'text/html',body:fs.readFileSync(__dirname+'/templates/counter.html','utf8').replace(/{%.*?%}/g,'')})
 });
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());await page.goto('http://sunny.test/counter/');
 await page.getByRole('button',{name:'Chi tiết / Sửa'}).click();await page.locator('.reopen-payment').waitFor();assert.equal(await page.locator('.detail-form select').first().isDisabled(),true);
 await page.locator('.reopen-payment').click();assert.equal(requests,0);assert.match(await page.locator('.detail-status').innerText(),/lý do/);
 await page.locator('.reopen-method').selectOption('bank_transfer');await page.locator('.reopen-reason').fill('Bấm nhầm khi chưa nhận tiền');await page.locator('.reopen-payment').click();await page.waitForFunction(()=>!document.querySelector('dialog'));
 assert.equal(requests,1);assert.deepEqual(submitted,{version:1,paymentRevision:0,paymentMethod:'bank_transfer',reason:'Bấm nhầm khi chưa nhận tiền',confirmed:true});assert.match(await page.locator('#counterRows').innerText(),/Chờ thanh toán/);assert.match(await page.locator('#counterRows').innerText(),/Chuyển khoản/);
 allowed=false;Object.assign(row,{paymentPending:false});await page.getByRole('button',{name:'Chi tiết / Sửa'}).click();await page.locator('.detail-summary').filter({hasText:'ST-PAID'}).waitFor();assert.equal(await page.locator('.reopen-payment').count(),0);assert.deepEqual(errors,[]);
 console.log('PASS: separate permission, reason required, explicit reopen, new method and pending list, button hidden without permission.');
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
