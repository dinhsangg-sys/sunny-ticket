function svBankPanel(order,container,onPaid){
 let active=true,timer=null,current=null;container.replaceChildren();
 const state=document.createElement('p');state.setAttribute('role','status');
 const image=document.createElement('img');image.alt='QR chuyển khoản SePay';image.style.cssText='display:block;width:min(100%,280px);height:auto;margin:12px auto';image.hidden=true;
 const detail=document.createElement('p'),display=document.createElement('a');display.className='btn';display.target='_blank';display.rel='noopener';display.textContent='Mở QR trên màn hình phụ';display.hidden=true;
 const retry=document.createElement('button');retry.className='btn';retry.textContent='Tạo lại / Kiểm tra QR';
 const cancel=document.createElement('button');cancel.className='btn';cancel.textContent='Hủy QR đang chờ';cancel.hidden=true;
 container.append(state,image,detail,display,retry,cancel);
 function render(intent){current=intent;image.hidden=!intent?.qrUrl;display.hidden=!intent?.displayUrl;cancel.hidden=intent?.state!=='pending';if(intent?.qrUrl)image.src=intent.qrUrl;if(intent?.displayUrl)display.href=intent.displayUrl;detail.textContent=intent?intent.accountName+' · '+intent.bank+' · '+intent.account+' · '+svMoney(intent.amount)+' · Nội dung: '+intent.paymentContent:'';state.textContent=intent?.state==='pending'?(intent.mode==='test'?'QR THỬ NGHIỆM — không chuyển tiền thật.':'Chờ SePay xác nhận tiền vào ngân hàng…'):({'paid':'Đã nhận thanh toán',expired:'QR đã hết hạn. Tạo lại để tiếp tục.',cancelled:'QR đã hủy.',unavailable:'SePay chưa sẵn sàng.'})[intent?.state]||'Chưa có QR.'}
 async function poll(){if(!active)return;try{const result=await svRequest('/souvenirs/api/orders/'+order.id+'/sepay/');if(!active)return;if(result.status==='paid'){active=false;await onPaid();return}if(result.deleted||result.status!=='pending'){render(null);state.textContent='Đơn đã thay đổi. Đóng và tải lại danh sách.';return}render(result.intent)}catch(e){if(active)state.textContent=e.message}if(active)timer=setTimeout(poll,3000)}
 async function create(){retry.disabled=true;state.textContent='Đang tạo QR…';try{const intent=await svRequest('/souvenirs/api/orders/'+order.id+'/sepay/','POST',{revision:order.revision});if(!active)return;render(intent);clearTimeout(timer);timer=setTimeout(poll,3000)}catch(e){if(active)state.textContent=e.message}finally{retry.disabled=false}}
 retry.onclick=create;cancel.onclick=async()=>{cancel.disabled=true;try{await svRequest('/souvenirs/api/orders/'+order.id+'/sepay/','POST',{action:'cancel'});clearTimeout(timer);if(active)render({...current,state:'cancelled',qrUrl:null,displayUrl:null})}catch(e){if(active)state.textContent=e.message}finally{cancel.disabled=false}};
 create();return ()=>{active=false;clearTimeout(timer)};
}

let svOrderPollTimer=null;
function svStartOrderPolling(){
 if(svOrderPollTimer||!svData.sepayEnabled||!svData.orders.some(o=>o.status==='pending'))return;
 svOrderPollTimer=setTimeout(async()=>{
  svOrderPollTimer=null;
  if(document.hidden){svStartOrderPolling();return}
  try{const fresh=await svRequest('/souvenirs/api/sales/');const justPaid=fresh.orders.filter(o=>o.status==='paid'&&svData.orders.some(old=>old.id===o.id&&old.status==='pending'));
   if(JSON.stringify(fresh.orders)!==JSON.stringify(svData.orders)){svData={...svData,...fresh};svRenderOrders();if(justPaid.length){svMessage('Đã cập nhật thanh toán: '+justPaid.map(o=>o.code).join(', '));if(sv('svReport'))await svReport()}}
  }catch(e){svMessage('Chưa đồng bộ trạng thái đơn: '+e.message)}finally{svStartOrderPolling()}
 },3000);
}
