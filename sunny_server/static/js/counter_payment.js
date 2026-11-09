const counterPaymentDialogs=new Set();
async function counterConfirmPayment(id){
 if(counterPaymentDialogs.has(id))return false;
 counterPaymentDialogs.add(id);let dialog;
 try{
  const state=await ticketRequest('/api/counter/bookings/'+encodeURIComponent(id)+'/'),row=state.booking;
  if(!row.paymentPending){await counterLoad();return true}
  if(!state.canConfirmPayment)throw Error('Chưa được cấp quyền xác nhận thanh toán tại quầy.');
  dialog=document.createElement('dialog');dialog.className='counter-ticket-dialog counter-payment-dialog';
  dialog.innerHTML='<h2>Xác nhận đã thanh toán</h2><p class="payment-summary"></p><label>Phương thức thanh toán<select class="select payment-method"></select></label><section class="payment-card" hidden><p>Chọn đủ hai thông tin. Phí bên bán chịu, đã gồm VAT, theo ngày xác nhận thu tiền.</p><label>Loại thẻ<select class="select card-scheme"><option value="">Chọn loại thẻ…</option><option value="napas">NAPAS</option><option value="visa">Visa</option><option value="mastercard">Mastercard</option><option value="jcb">JCB</option><option value="unionpay">UnionPay</option></select></label><label>Nơi phát hành<select class="select card-origin"><option value="">Chọn nơi phát hành…</option><option value="domestic">Trong nước</option><option value="foreign">Nước ngoài</option></select></label><button type="button" class="btn card-requote">Tính lại phí</button><p class="card-quote" role="status"></p></section><p>Chỉ xác nhận sau khi đã nhận đủ tiền thực tế. Thao tác ghi nhận khoản thu; không tự trừ tiền thẻ.</p><p class="payment-status" role="status"></p><button type="button" class="btn primary payment-confirm">Xác nhận đã nhận đủ tiền</button> <button type="button" class="btn payment-cancel">Để sau</button>';
  const find=s=>dialog.querySelector(s),method=find('.payment-method'),confirmButton=find('.payment-confirm');let busy=false,completed=false,cardQuote=null,quoteSequence=0;
  find('.payment-summary').textContent=row.bookingCode+' · Tổng tiền: '+counterMoney(row.revenue)+' · Đã thu: '+counterMoney(row.paid)+' · Cần thu: '+counterMoney(row.balance);
  for(const [value,label] of Object.entries(counterPaymentLabels))method.append(new Option(label,value));method.value=row.paymentMethod||'cash';
  function restore(){dialog.querySelectorAll('button,select').forEach(el=>el.disabled=busy);method.disabled=busy||state.sepayActive;confirmButton.disabled=busy||state.sepayActive||(method.value==='card'&&!cardQuote)}
  async function refreshQuote(){const sequence=++quoteSequence;cardQuote=null;find('.payment-card').hidden=method.value!=='card';restore();if(method.value!=='card')return;const scheme=find('.card-scheme').value,origin=find('.card-origin').value;if(!scheme||!origin){find('.card-quote').textContent='Chọn loại thẻ và nơi phát hành để tính phí.';return}find('.card-quote').textContent='Đang tính phí…';try{const result=await ticketRequest('/api/counter/bookings/'+encodeURIComponent(id)+'/card-fee-quote/','POST',{scheme,origin});if(sequence!==quoteSequence||!dialog.isConnected)return;cardQuote=result.quote;find('.card-quote').textContent='Phí: '+Number(cardQuote.rate).toLocaleString('vi-VN')+'% = '+counterMoney(cardQuote.feeAmount)+' · Thực nhận: '+counterMoney(cardQuote.netAmount)+' · Khách thanh toán đủ: '+counterMoney(cardQuote.amount)}catch(e){if(sequence===quoteSequence)find('.card-quote').textContent=e.message}finally{if(sequence===quoteSequence)restore()}}
  method.onchange=refreshQuote;find('.card-scheme').onchange=refreshQuote;find('.card-origin').onchange=refreshQuote;find('.card-requote').onclick=refreshQuote;
  if(state.sepayActive){const info=document.createElement('p');info.textContent='Đang chờ SePay xác nhận chuyển khoản. Không xác nhận thủ công khi phiên QR còn hoạt động.';find('.payment-status').append(info);const cancelBank=document.createElement('button');cancelBank.className='btn';cancelBank.textContent='Hủy phiên QR để đổi cách thu';cancelBank.onclick=async()=>{if(!confirm('Hủy phiên chờ? QR ngân hàng cũ không tự vô hiệu; nếu khách đã chuyển tiền cần đối soát trước khi thu lại.'))return;cancelBank.disabled=true;try{await counterCancelSePay(row.sepayIntentId);dialog.close()}catch(e){info.textContent=e.message;cancelBank.disabled=false}};find('.payment-status').append(cancelBank)}
  document.body.append(dialog);dialog.showModal();refreshQuote();
  const result=new Promise(resolve=>{dialog.onclose=()=>{quoteSequence++;resolve(completed)}});
  dialog.oncancel=event=>{if(busy)event.preventDefault()};find('.payment-cancel').onclick=()=>{if(!busy)dialog.close()};
  confirmButton.onclick=async()=>{
   if(busy||state.sepayActive||method.value==='card'&&!cardQuote)return;busy=true;restore();
   try{await ticketRequest('/api/counter/bookings/'+encodeURIComponent(id)+'/confirm-payment/','POST',{version:state.version,paymentRevision:row.paymentRevision||0,paymentMethod:method.value,confirmed:true,...(method.value==='card'?{cardFeeQuote:cardQuote}:{})});completed=true;dialog.close();await counterLoad();counterElement('counterMessage').textContent='Đã xác nhận thanh toán và hoàn thành '+row.bookingCode+'.'}
   catch(e){find('.payment-status').textContent=e.message+' Nếu chưa rõ kết quả, đóng cửa sổ và tải lại booking để kiểm tra.';if(method.value==='card')cardQuote=null}
   finally{busy=false;restore()}
  };
  return await result;
 }finally{dialog?.remove();counterPaymentDialogs.delete(id)}
}
