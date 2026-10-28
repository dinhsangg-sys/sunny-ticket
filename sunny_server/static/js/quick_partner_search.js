const openPartnerDropdowns=new Map();let quickSelectSequence=0;
document.addEventListener('pointerdown',event=>{for(const [box,close] of [...openPartnerDropdowns]){if(!box.isConnected||!box.contains(event.target))close()}},true);
function partnerSearchText(value){return String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[đĐ]/g,'d').toLowerCase().trim()}
function attachPartnerQuickSearch(select,agents,config={}){
 const label=config.label||(a=>a.name+' ('+a.id+')'),search=config.search||(a=>a.name+' '+a.id);let composing=false;
 const box=document.createElement('div');box.className='partner-quick-search';
 const trigger=document.createElement('button');trigger.type='button';trigger.className='select partner-select-trigger';trigger.setAttribute('aria-expanded','false');
 const panel=document.createElement('div');panel.className='partner-select-panel';panel.hidden=true;
 const input=document.createElement('input');input.className='input';input.type='search';input.placeholder=config.placeholder||'Tìm theo tên hoặc mã đối tác...';input.setAttribute('aria-label','Tìm nhanh '+select.name);
 const list=document.createElement('div');list.className='partner-quick-results';list.setAttribute('role','listbox');
 const owner=select.closest('label');if(owner&&!owner.htmlFor){if(!select.id)select.id='quick-select-'+(++quickSelectSequence);owner.htmlFor=select.id}select.before(box);box.append(trigger,panel);panel.append(input,list);select.hidden=true;select.required=false;let matches=[],active=-1;
 function sync(){const a=agents.find(a=>String(a.id)===select.value);trigger.textContent=(a?label(a):'Chọn đối tác...')+' ▾'}
 function close(){openPartnerDropdowns.delete(box);panel.hidden=true;trigger.setAttribute('aria-expanded','false')}
 function choose(a){select.value=a.id;sync();close();trigger.focus();select.dispatchEvent(new Event('input',{bubbles:true}));select.dispatchEvent(new Event('change',{bubbles:true}))}
 function render(){const q=partnerSearchText(input.value);matches=agents.filter(a=>!q||partnerSearchText(search(a)).includes(q));active=-1;list.replaceChildren();if(!matches.length){list.textContent='Không tìm thấy đối tác';return}for(const a of matches){const b=document.createElement('button');b.type='button';b.textContent=label(a);b.setAttribute('role','option');b.setAttribute('aria-selected',String(String(a.id)===select.value));b.onclick=()=>choose(a);list.append(b)}}
 trigger.onclick=()=>{if(!panel.hidden)return close();for(const closeOther of [...openPartnerDropdowns.values()])closeOther();openPartnerDropdowns.set(box,close);panel.hidden=false;trigger.setAttribute('aria-expanded','true');input.value='';render();input.focus()};input.addEventListener('compositionstart',()=>{composing=true});input.addEventListener('compositionend',()=>{composing=false;render()});input.oninput=e=>{if(!composing&&!e.isComposing)render()};
 box.onfocusout=e=>{if(e.relatedTarget&&!box.contains(e.relatedTarget))close()};
 box.onkeydown=e=>{if(composing||e.isComposing||e.keyCode===229)return;if(e.key==='Escape'){e.preventDefault();close();trigger.focus();return}if(['ArrowDown','ArrowUp'].includes(e.key)&&!panel.hidden){e.preventDefault();active=Math.max(0,Math.min(matches.length-1,active+(e.key==='ArrowDown'?1:-1)));[...list.children].forEach((b,i)=>b.classList.toggle('active',i===active));list.children[active]?.scrollIntoView({block:'nearest'})}if(e.key==='Enter'&&e.target===input){e.preventDefault();if(matches.length)choose(matches[Math.max(active,0)])}};
 select.addEventListener('change',sync);sync();
}