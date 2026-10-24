const regularCostChoices=refreshCostChoices;
refreshCostChoices=function(keepInitial=false){
 const wasManual=$('fbuySelect')?.value==='manual',typedPrice=$('fbuy')?.value,typedName=$('manualCostSource')?.value||'';regularCostChoices(keepInitial);
 const select=$('fbuySelect'),previousChange=select.onchange,old=window.v2BookingOld;
 select.append(new Option('✏️ Nguồn nhập tay — tự nhập giá vốn','manual'));
 let name=$('manualCostSource');
 if(!name){const label=document.createElement('label');label.id='manualCostLabel';label.textContent='Tên nguồn nhập tay (không bắt buộc)';name=document.createElement('input');name.className='input';name.id='manualCostSource';name.placeholder='Ví dụ: Anh Nhân / vé phát sinh';label.append(name);select.parentElement.append(label)}
 if(wasManual||keepInitial&&old?.costSource==='manual'){select.value='manual';name.value=wasManual?typedName:(old.manualSourceName||'');if(wasManual)$('fbuy').value=typedPrice}
 function update(){const manual=select.value==='manual';$('manualCostLabel').hidden=!manual;if(manual){window.v2SelectedCost={supplierId:'__manual__',supplierName:name.value.trim()||'Nguồn nhập tay',costSource:'manual',manualSourceName:name.value.trim(),id:''};$('fbuy').style.display='block'}else previousChange?.();}
 select.onchange=()=>{if(select.value==='manual'&&old?.costSource!=='manual')$('fbuy').value='';update()};name.oninput=update;update();
};
const regularSaveBooking=saveBooking;
saveBooking=function(id){if($('fbuySelect')?.value==='manual'){
 const raw=$('fbuy').value.trim(),price=Number(raw);if(!raw||!Number.isFinite(price)||price<0)return alert('Nhập giá vốn hợp lệ cho nguồn nhập tay.');
 const name=$('manualCostSource')?.value.trim()||'',old=db.bookings.find(b=>b.id===id);
 if(old?.supplierPayments?.length&&(old.supplierId!=='__manual__'||old.supplierName!==(name||'Nguồn nhập tay')))return alert('Nguồn đã có chi tiền; cần đối soát trước khi đổi.');
 window.v2SelectedCost={supplierId:'__manual__',supplierName:name||'Nguồn nhập tay',costSource:'manual',manualSourceName:name,id:''};
}regularSaveBooking(id)};
const regularBookingsPage=bookings;
bookings=function(){regularBookingsPage();const table=$('bt')?.closest('table');if(table){table.classList.add('booking-table');table.closest('.tablebox').classList.add('booking-tablebox');const header=table.querySelector('thead tr th:last-child');header.textContent='Thao tác'}};
