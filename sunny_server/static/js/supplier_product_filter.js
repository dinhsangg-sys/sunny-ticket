function supplierProductMatches(booking){
 const selected=$('bsProduct')?.value||'';
 return !selected||selected===(reportBookingProduct(booking)===null?'unknown':'product:'+reportBookingProduct(booking));
}
function supplierBookingTicketKey(booking){
 const ticket=booking.ticketId&&ticketForRef(booking.ticketId)||ticketForRef(booking.ticketType);
 return ticket?String(ticket.id):'legacy:'+booking.ticketType;
}
const supplierRowsBeforeProduct=bulkVisibleSupplierRows;
bulkVisibleSupplierRows=function(){return supplierRowsBeforeProduct().filter(supplierProductMatches)};
const supplierTicketOptionsBeforeProduct=bulkTicketOptions;
bulkTicketOptions=function(){
 const all=supplierTicketOptionsBeforeProduct(),selected=$('bsProduct')?.value||'';
 if(!selected)return all;
 const keys=new Set(db.bookings.filter(supplierProductMatches).map(supplierBookingTicketKey));
 for(const ticket of db.ticketTypes){const product=typeof ticket.product==='string'&&ticket.product.trim()?ticket.product.trim():null;if(selected===(product===null?'unknown':'product:'+product))keys.add(String(ticket.id))}
 return all.filter(ticket=>keys.has(ticket.key));
};
const supplierFormBeforeProduct=bulkSupplierPaymentForm;
bulkSupplierPaymentForm=async function(){
 await supplierFormBeforeProduct();if($('mb').style.display!=='flex'||!$('bsSupplier')||$('bsProduct'))return;
 const label=document.createElement('label');label.textContent='Sản phẩm';const select=document.createElement('select');select.id='bsProduct';select.className='select';select.setAttribute('aria-label','Lọc sản phẩm thanh toán tiền vé');select.append(new Option('Tất cả sản phẩm',''));
 const products=[...new Set([...db.ticketTypes.map(t=>typeof t.product==='string'?t.product.trim():null),...db.bookings.map(reportBookingProduct)].filter(Boolean))].sort((a,b)=>a.localeCompare(b,'vi'));
 for(const product of products)select.append(new Option(product,'product:'+product));
 if(db.bookings.some(b=>reportBookingProduct(b)===null)||db.ticketTypes.some(t=>!t.product?.trim()))select.append(new Option('Chưa xác định sản phẩm','unknown'));
 select.onchange=()=>{bsTicketSelection=null;$('bsTicketSearch').value='';bulkRenderTicketOptions();renderBulkSupplierRows()};label.append(select);$('bsSupplier').closest('label').after(label);bulkRenderTicketOptions();renderBulkSupplierRows();modalInitialState=modalState();
};
