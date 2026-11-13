function svOrderDate(value){
 const date=new Date(value);if(!Number.isFinite(date.getTime()))return '—';
 const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(date);
 const p=Object.fromEntries(parts.map(x=>[x.type,x.value]));return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute}:${p.second}`;
}
function svOrderActions(cell,order){
 function button(text,run){const b=document.createElement('button');b.className='btn';b.textContent=text;b.onclick=run;cell.append(b)}
 if(svData.canEdit)button('Sửa đơn',()=>svEditOrder(order));
 if(svData.canDelete)button('Xóa đơn',async()=>{
  const reason=prompt('Lý do xóa đơn '+order.code+' (bắt buộc):');if(!reason?.trim())return;
  if(!confirm('Xóa '+order.code+'? Đơn sẽ không còn trong doanh thu. Thao tác này không hoàn tiền ngân hàng/POS.'))return;
  try{await svRequest('/souvenirs/api/orders/'+order.id+'/','POST',{action:'delete',revision:order.revision,confirmed:true,reason});await svLoad();if(sv('svReport'))await svReport();svMessage('Đã xóa đơn và cập nhật báo cáo.')}catch(e){svMessage(e.message)}
 });
 if(order.history?.length){const d=document.createElement('details'),title=document.createElement('summary');title.textContent='Lịch sử thay đổi';d.append(title);for(const h of order.history){const p=document.createElement('p');p.textContent=svOrderDate(h.at)+' · '+h.actor+' · '+({edit:'Sửa',delete:'Xóa',sepay:'SePay xác nhận'})[h.action]+' · '+h.reason;d.append(p)}cell.append(d)}
}
function svEditOrder(order){
 const dialog=document.createElement('dialog');dialog.className='modal';dialog.style.cssText='display:block;width:95%;max-width:850px;max-height:90vh;overflow:auto';
 dialog.innerHTML='<h2>Sửa đơn lưu niệm</h2><p class="order-info"></p><p>Đơn đã thanh toán sẽ được cập nhật doanh thu. Phí thẻ tính lại theo tỷ lệ đã lưu khi thu tiền. Không thực hiện thu/hoàn tiền ngân hàng hoặc POS.</p><div class="edit-lines"></div><label>Thêm sản phẩm<select class="select add-product"></select></label><button class="btn add-line">Thêm dòng</button><p>Tổng tiền: <strong class="edit-total"></strong></p><label>Ghi chú<textarea class="input edit-note" maxlength="1000"></textarea></label><label>Lý do sửa (bắt buộc)<input class="input edit-reason" maxlength="500"></label><p class="edit-message" role="status"></p><button class="btn primary edit-save">Lưu thay đổi</button> <button class="btn edit-close">Đóng</button>';
 const el=q=>dialog.querySelector(q);el('.order-info').textContent=order.code+' · Tạo '+svOrderDate(order.createdAt);el('.edit-note').value=order.note||'';
 let busy=false;const rows=[];
 function total(){el('.edit-total').textContent=svMoney(rows.reduce((s,r)=>s+Number(r.qty.value)*Number(r.price.value),0))}
 function add(item){if(rows.some(r=>r.product===item.product)){el('.edit-message').textContent='Sản phẩm đã có trong đơn.';return}const box=document.createElement('div');box.className='sv-cart-row';const label=document.createElement('span');label.textContent=item.name;const qty=document.createElement('input');qty.className='input';qty.type='number';qty.min='1';qty.max='10000';qty.step='1';qty.value=item.quantity;qty.setAttribute('aria-label','Số lượng '+item.name);const price=document.createElement('input');price.className='input';price.type='number';price.min='0';price.step='1';price.value=item.unitPrice;price.setAttribute('aria-label','Giá bán '+item.name);const remove=document.createElement('button');remove.className='btn';remove.textContent='Bỏ';const row={product:item.product,qty,price};rows.push(row);remove.onclick=()=>{rows.splice(rows.indexOf(row),1);box.remove();total()};qty.oninput=price.oninput=total;box.append(label,qty,price,remove);el('.edit-lines').append(box);total()}
 for(const item of order.lines)add(item);
 for(const p of svData.products)el('.add-product').append(new Option(p.name+' · '+svMoney(p.price),p.id));
 el('.add-line').onclick=()=>{const p=svData.products.find(p=>p.id===el('.add-product').value);if(p)add({product:p.id,name:p.name,quantity:1,unitPrice:p.price})};
 el('.edit-close').onclick=()=>{if(!busy)dialog.close()};dialog.oncancel=e=>{if(busy)e.preventDefault()};dialog.onclose=()=>dialog.remove();
 el('.edit-save').onclick=async()=>{
  if(busy)return;const reason=el('.edit-reason').value.trim();if(!reason){el('.edit-message').textContent='Nhập lý do sửa.';return}
  if(!rows.length||rows.some(r=>!r.qty.checkValidity()||!r.price.checkValidity()||!r.qty.value||!r.price.value)){el('.edit-message').textContent='Kiểm tra số lượng và giá từng dòng.';return}
  if(!confirm('Lưu thay đổi '+order.code+' với tổng '+el('.edit-total').textContent+'? Hãy đối soát khoản tiền chênh lệch thực tế.'))return;
  busy=true;dialog.querySelectorAll('input,textarea,select,button').forEach(e=>e.disabled=true);
  try{await svRequest('/souvenirs/api/orders/'+order.id+'/','POST',{action:'edit',revision:order.revision,confirmed:true,reason,note:el('.edit-note').value,items:rows.map(r=>({product:r.product,quantity:Number(r.qty.value),unitPrice:r.price.value}))});dialog.close();await svLoad();if(sv('svReport'))await svReport();svMessage('Đã sửa đơn và cập nhật báo cáo.')}catch(e){el('.edit-message').textContent=e.message}finally{busy=false;dialog.querySelectorAll('input,textarea,select,button').forEach(e=>e.disabled=false)}
 };document.body.append(dialog);dialog.showModal();
}
