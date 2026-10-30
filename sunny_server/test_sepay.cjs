const fs=require('fs'),path=require('path'),assert=require('assert'),{chromium}=require('playwright');
(async()=>{const browser=await chromium.launch({headless:true,channel:process.env.BROWSER_CHANNEL||'msedge'});try{
 const context=await browser.newContext(),errors=[];let paid=false,networkFailure=false,created=0,manual=0;
 const booking={id:'one',bookingCode:'ST-TEST',date:'2026-10-30',ticketType:'Eco',qty:2,sellPrice:500000,revenue:1000000,paid:0,paymentPending:true,paymentMethod:'cash',counterVersion:1};
 const png='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aZl8AAAAASUVORK5CYII=';
 const intent={id:'intent-one',state:'pending',bookingCode:'ST-TEST',code:'STP123456789012345678',paymentContent:'SEVQR STP123456789012345678',amount:1000000,bank:'TEST BANK',account:'0123456789',accountName:'SUNNY TEST',mode:'test',expiresAt:new Date(Date.now()+900000).toISOString(),qrUrl:png,displayUrl:'/pay/sepay/#signed-test-token'};
 await context.route('http://sunny.test/**',async route=>{const request=route.request(),url=new URL(request.url());
  if(url.pathname==='/api/counter/')return route.fulfill({json:{sepayEnabled:true,today:'2026-10-30',seller:'nv1',canCreate:true,canConfirmPayment:true,tickets:[],bookings:[{...booking,paymentPending:!paid,paid:paid?1000000:0,paymentConfirmedBy:paid?'SePay (TEST)':null}]}});
  if(url.pathname==='/api/counter/bookings/one/sepay/'){created++;assert.deepEqual(request.postDataJSON(),{});return route.fulfill({json:intent,status:201})}
  if(url.pathname==='/api/sepay/display/'){assert.equal(request.headers().authorization,'Bearer signed-test-token');if(networkFailure)return route.fulfill({status:503,json:{state:'unavailable'}});return route.fulfill({json:{...intent,state:paid?'paid':'pending'}})}
  if(url.pathname.endsWith('/confirm-payment/')){manual++;return route.fulfill({status:500,json:{error:'Unexpected manual confirmation'}})}
  if(url.pathname.startsWith('/static/'))return route.fulfill({body:fs.readFileSync(path.join(__dirname,url.pathname.slice(1))),contentType:'application/javascript'});
  const file=url.pathname==='/pay/sepay/'?'sepay_display.html':'counter.html';
  return route.fulfill({contentType:'text/html',body:fs.readFileSync(path.join(__dirname,'templates',file),'utf8').replace(/{%.*?%}/g,'')})
 });
 context.on('page',p=>p.on('pageerror',e=>errors.push(e.message)));
 const staff=await context.newPage();await staff.goto('http://sunny.test/counter/');
 await staff.getByRole('button',{name:'QR chuyển khoản / Màn hình phụ'}).waitFor();
 const popupPromise=context.waitForEvent('page');await staff.getByRole('button',{name:'QR chuyển khoản / Màn hình phụ'}).click();const display=await popupPromise;
 await display.locator('#displayQr').waitFor({state:'visible'});assert.equal(created,1);assert.equal(new URL(display.url()).hash,'');assert.match(await display.locator('#displayTest').innerText(),/không dùng chuyển tiền thật/);assert.match(await display.locator('#displayAmount').innerText(),/1\.000\.000/);
 assert.match(await display.locator('#displayDetails').innerText(),/Nội dung: SEVQR STP123456789012345678/);networkFailure=true;await display.locator('#displayQr').waitFor({state:'hidden',timeout:7000});assert.match(await display.locator('#displayState').innerText(),/Chưa lấy được xác nhận/);
 networkFailure=false;await display.locator('#displayQr').waitFor({state:'visible',timeout:7000});
 paid=true;await display.locator('#displayState[data-state=paid]').waitFor({timeout:7000});await display.locator('#displayQr').waitFor({state:'hidden'});
 await staff.waitForFunction(()=>document.getElementById('counterRows').textContent.includes('Đã thanh toán'),{},{timeout:7000});assert.match(await staff.locator('#counterMessage').innerText(),/SePay/);assert.equal(manual,0);assert.deepEqual(errors,[]);
 console.log('PASS: second window, token authorization, test QR, hide on network failure, recovery and automatic paid status on both screens without manual POST.');
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
