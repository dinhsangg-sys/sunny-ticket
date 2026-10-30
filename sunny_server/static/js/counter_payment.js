const counterPaymentDialogs=new Set();
async function counterConfirmPayment(id){
 if(counterPaymentDialogs.has(id))return false;
 counterPaymentDialogs.add(id);let dialog;
 try{
  const state=await ticketRequest('/api/counter/bookings/'+encodeURIComponent(id)+'/'),row=state.booking;
  if(!row.paymentPending){await counterLoad();return true}
  if(!state.canConfirmPayment)throw Error('Chưa được cấp quyền xác nhận thanh toán tại quầy.');
  dialog=document.createElement('dialog');dialog.className='counter-ticket-dialog counter-payment-dialog';
  dialog.innerHTML='<h2>Xác nhận đã thanh toán</h2><p class="payment-summary"></p><label>Phương thức thanh toán<select class="select payment-method"></select></label><p>Chỉ xác nhận sau khi đã nhận đủ tiền thực tế. Thao tác này ghi nhận khoản thu và hoàn thành booking; không tự trừ tiền thẻ hoặc kiểm tra ngân hàng.</p><p class="payment-status" role="status"></p><button class="btn primary payment-confirm">Xác nhận đã nhận đủ tiền</button> <button class="btn payment-cancel">Để sau</button>';
  dialog.querySelector('.payment-summary').textContent=row.bookingCode+' · Tổng tiền: '+counterMoney(row.revenue)+' · Đã thu: '+counterMoney(row.paid)+' · Cần thu: '+counterMoney(row.balance);
  const method=dialog.querySelector('.payment-method');for(const [value,label] of Object.entries(counterPaymentLabels))method.append(new Option(label,value));method.value=row.paymentMethod||'cash';
  document.body.append(dialog);dialog.showModal();let busy=false,completed=false;
  const result=new Promise(resolve=>{dialog.onclose=()=>resolve(completed)});
  dialog.oncancel=event=>{if(busy)event.preventDefault()};dialog.querySelector('.payment-cancel').onclick=()=>{if(!busy)dialog.close()};
  dialog.querySelector('.payment-confirm').onclick=async()=>{
   if(busy)return;busy=true;dialog.querySelectorAll('button,select').forEach(el=>el.disabled=true);
   try{await ticketRequest('/api/counter/bookings/'+encodeURIComponent(id)+'/confirm-payment/','POST',{version:state.version,paymentMethod:method.value,confirmed:true});completed=true;dialog.close();await counterLoad();counterElement('counterMessage').textContent='Đã xác nhận thanh toán và hoàn thành '+row.bookingCode+'.'}
   catch(e){dialog.querySelector('.payment-status').textContent=e.message+' Nếu chưa rõ kết quả, đóng cửa sổ và tải lại booking để kiểm tra.'}
   finally{busy=false;dialog.querySelectorAll('button,select').forEach(el=>el.disabled=false)}
  };
  return await result;
 }finally{dialog?.remove();counterPaymentDialogs.delete(id)}
}
