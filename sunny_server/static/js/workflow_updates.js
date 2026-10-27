// Native links preserve browser context menus, middle-click and Ctrl+click.
const routeBaseGo=go,extraRoutes={suppliers:suppliersPage,sharedPrices:priceListsPage,partnerTypes:partnerTypesPage};
function routePage(page){if(!document.querySelector('.nav [data-p="'+CSS.escape(page)+'"]'))page='dashboard';if(extraRoutes[page]){$('title').textContent=({suppliers:'Nhà cung cấp',sharedPrices:'Bảng giá chung',partnerTypes:'Loại đối tác'})[page];extraRoutes[page]()}else routeBaseGo(page);document.querySelectorAll('.nav [data-p]').forEach(a=>a.classList.toggle('on',a.dataset.p===page))}
go=function(page){if(location.hash!=='#'+page)history.pushState(null,'',location.pathname+'?view='+encodeURIComponent(page)+'#'+page);routePage(page)};
for(const button of [...document.querySelectorAll('.nav button')]){const page=button.dataset.p||'partnerTypes',a=document.createElement('a');a.dataset.p=page;a.href=location.pathname+'?view='+encodeURIComponent(page)+'#'+page;a.textContent=button.textContent;a.className=button.className;a.onclick=e=>{if(e.button||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();go(page)};button.replaceWith(a)}
window.addEventListener('popstate',()=>routePage(location.hash.slice(1)||new URLSearchParams(location.search).get('view')||'dashboard'));
window.addEventListener('hashchange',()=>routePage(location.hash.slice(1)||'dashboard'));
routePage(location.hash.slice(1)||new URLSearchParams(location.search).get('view')||'dashboard');

const searchableCostForm=costForm;
costForm=function(index=-1){searchableCostForm(index);const select=$('ct');attachPartnerQuickSearch(select,orderedTicketTypes().filter(t=>[...select.options].some(o=>o.value===t.name)).map(t=>({id:t.name,name:t.name,code:t.id})),{label:t=>t.name+' · '+t.code,search:t=>t.name+' '+t.code,placeholder:'Tìm theo tên hoặc mã vé...'});modalInitialState=modalState()};

function enableModalDrag(modal){
 const handle=modal.querySelector('.modalhead')||modal.querySelector('h2');if(!handle)return;handle.classList.add('modal-drag-handle');handle.title='Giữ chuột trái để di chuyển';
 handle.onpointerdown=e=>{if(e.button!==0||e.target.closest('button,input,select,textarea,a'))return;const rect=modal.getBoundingClientRect(),startX=e.clientX,startY=e.clientY;handle.setPointerCapture(e.pointerId);e.preventDefault();
 const move=event=>{modal.style.position='fixed';modal.style.margin='0';modal.style.left=Math.max(0,Math.min(innerWidth-rect.width,rect.left+event.clientX-startX))+'px';modal.style.top=Math.max(0,Math.min(Math.max(0,innerHeight-rect.height),rect.top+event.clientY-startY))+'px'};
 const end=()=>{handle.removeEventListener('pointermove',move);handle.removeEventListener('pointerup',end);handle.removeEventListener('pointercancel',end);handle.removeEventListener('lostpointercapture',end)};
 handle.addEventListener('pointermove',move);handle.addEventListener('pointerup',end);handle.addEventListener('pointercancel',end);handle.addEventListener('lostpointercapture',end)
 };
}
const draggableShow=show;
show=function(content,onClose=null){const modal=$('modal');for(const key of ['position','margin','left','top'])modal.style[key]='';draggableShow(content,onClose);enableModalDrag(modal)};
window.addEventListener('resize',()=>{const modal=$('modal');if(modal.style.position!=='fixed')return;const r=modal.getBoundingClientRect();modal.style.left=Math.max(0,Math.min(r.left,innerWidth-r.width))+'px';modal.style.top=Math.max(0,Math.min(r.top,innerHeight-r.height))+'px'});
