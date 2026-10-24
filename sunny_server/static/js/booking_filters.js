const bookingColumnDefinitions=[['bookingCode','Mã booking','text'],['date','Ngày','date'],['ticketType','Loại vé','select'],['party','Khách hàng / Đại lý','text'],['qty','SL','number'],['sellPrice','Giá vé','number'],['revenue','Tổng tiền','number'],['paid','Đã thu','number'],['due','Còn nợ','number'],['status','Thanh toán','select']];
let bookingColumnFilters={};
function bookingColumnValue(x,key){return key==='party'?bookingPartyName(x):key==='paid'?paidAmount(x):key==='due'?dueAmount(x):key==='status'?payStatus(x):x[key]}
function bookingColumnMatches(x){return bookingColumnDefinitions.every(([key,,type])=>{const f=bookingColumnFilters[key];if(!f)return true;const value=bookingColumnValue(x,key);if(type==='text')return partnerSearchText(value).includes(partnerSearchText(f.value));if(type==='select')return !f.value||String(value)===f.value;const v=type==='number'?Number(value):String(value||'');return (!f.min||(type==='number'?v>=Number(f.min):v>=f.min))&&(!f.max||(type==='number'?v<=Number(f.max):v<=f.max))})}
function updateBookingFilterHeaders(){document.querySelectorAll('.booking-column-filter').forEach(b=>{const active=!!bookingColumnFilters[b.dataset.key];b.classList.toggle('active',active);b.setAttribute('aria-label',b.dataset.label+(active?' — đang lọc':' — lọc cột'));b.textContent=b.dataset.label+(active?' ●':' ▾')})}
function openBookingColumnFilter(index){
 const [key,label,type]=bookingColumnDefinitions[index],old=bookingColumnFilters[key]||{};
 document.querySelector('.booking-filter-dialog')?.remove();const dialog=document.createElement('dialog');dialog.className='booking-filter-dialog';
 const title=document.createElement('h3');title.textContent='Lọc: '+label;dialog.append(title);
 const fields={};function field(name,labelText,inputType,value){const label=document.createElement('label');label.textContent=labelText;const input=document.createElement('input');input.className='input';input.type=inputType;input.value=value||'';if(inputType==='number')input.step='any';label.append(input);dialog.append(label);fields[name]=input}
 if(type==='text')field('value','Chứa nội dung','search',old.value);
 else if(type==='select'){const select=document.createElement('select');select.className='select';select.append(new Option('Tất cả',''));const options=key==='status'?[['unpaid','Chưa thanh toán'],['partial','Thanh toán một phần'],['paid','Đã thanh toán']]:[...new Set(db.bookings.map(x=>x.ticketType))].sort().map(v=>[v,v]);options.forEach(([v,n])=>select.append(new Option(n,v)));select.value=old.value||'';dialog.append(select);fields.value=select}
 else{field('min','Từ',type,old.min);field('max','Đến',type,old.max)}
 const error=document.createElement('p');error.className='red';error.setAttribute('role','alert');dialog.append(error);
 const buttons=document.createElement('div');buttons.className='toolbar';dialog.append(buttons);
 function button(label,action){const b=document.createElement('button');b.className='btn';b.textContent=label;b.onclick=action;buttons.append(b)}
 function close(){dialog.close();dialog.remove()}
 button('Áp dụng',()=>{const value=Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,v.value.trim()]));if(Object.values(fields).some(v=>!v.checkValidity())){error.textContent='Giá trị lọc không hợp lệ.';return}if(value.min&&value.max&&(type==='number'?Number(value.min)>Number(value.max):value.min>value.max)){error.textContent='Giá trị Từ phải nhỏ hơn hoặc bằng Đến.';return}if(Object.values(value).some(Boolean))bookingColumnFilters[key]=value;else delete bookingColumnFilters[key];filterB();close()});
 button('Bỏ lọc cột',()=>{delete bookingColumnFilters[key];filterB();close()});button('Đóng',close);dialog.oncancel=()=>dialog.remove();document.body.append(dialog);dialog.showModal();
}
const compactFilterBookings=filterB;
filterB=function(){compactFilterBookings();const body=$('bt');if(!body)return;for(const row of body.rows){if(row.cells.length<11){row.cells[0].colSpan=12;continue}const actions=row.cells[10],remove=actions.querySelector('button:last-child'),cell=row.insertCell();cell.className='booking-delete';if(remove)cell.append(remove);actions.className='booking-main-actions';for(const i of [2,3]){row.cells[i].title=row.cells[i].textContent;const span=document.createElement('span');span.className='booking-cell-ellipsis';span.textContent=row.cells[i].textContent;row.cells[i].replaceChildren(span)}}updateBookingFilterHeaders()};
const compactBookingsPage=bookings;
bookings=function(){compactBookingsPage();const table=$('bt')?.closest('table');if(!table)return;const headers=table.querySelector('thead tr');headers.children[10].className='booking-main-actions';const th=document.createElement('th');th.textContent='Xóa';th.className='booking-delete';headers.append(th);bookingColumnDefinitions.forEach(([key,label],i)=>{const b=document.createElement('button');b.className='booking-column-filter';b.dataset.key=key;b.dataset.label=label;b.onclick=()=>openBookingColumnFilter(i);headers.children[i].replaceChildren(b)});updateBookingFilterHeaders()};
const compactClearBookingFilters=clearBookingFilters;
clearBookingFilters=function(){bookingColumnFilters={};compactClearBookingFilters();$('bm').value='';filterB()};
const topBookingForm=bookingForm;
bookingForm=function(id=''){topBookingForm(id);const modal=$('modal');$('fd')?.focus({preventScroll:true});modal.scrollTop=0;requestAnimationFrame(()=>{if($('modal')===modal&&$('fd'))modal.scrollTop=0})};
const resetPartnerSearchGo=go;
go=function(page){if(page==='agents'&&!$('aq')&&uiFilters.agents)uiFilters.agents.q='';return resetPartnerSearchGo(page)};
