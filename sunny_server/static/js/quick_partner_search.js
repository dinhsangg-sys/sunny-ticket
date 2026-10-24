function partnerSearchText(value){return String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[đĐ]/g,'d').toLowerCase().trim()}
function attachPartnerQuickSearch(select,agents){
 const box=document.createElement('div');box.className='partner-quick-search';
 const trigger=document.createElement('button');trigger.type='button';trigger.className='select partner-select-trigger';trigger.setAttribute('aria-expanded','false');
 const panel=document.createElement('div');panel.className='partner-select-panel';panel.hidden=true;
 const input=document.createElement('input');input.className='input';input.type='search';input.placeholder='Tìm theo tên hoặc mã đối tác...';input.setAttribute('aria-label','Tìm nhanh '+select.name);
 const list=document.createElement('div');list.className='partner-quick-results';list.setAttribute('role','listbox');
 select.before(box);box.append(trigger,panel);panel.append(input,list);select.hidden=true;select.required=false;let matches=[],active=-1;
 function sync(){const a=agents.find(a=>String(a.id)===select.value);trigger.textContent=(a?a.name+' ('+a.id+')':'Chọn đối tác...')+' ▾'}
 function close(){panel.hidden=true;trigger.setAttribute('aria-expanded','false')}
 function choose(a){select.value=a.id;sync();close();trigger.focus();select.dispatchEvent(new Event('input',{bubbles:true}));select.dispatchEvent(new Event('change',{bubbles:true}))}
 function render(){const q=partnerSearchText(input.value);matches=agents.filter(a=>!q||partnerSearchText(a.name+' '+a.id).includes(q));active=-1;list.replaceChildren();if(!matches.length){list.textContent='Không tìm thấy đối tác';return}for(const a of matches){const b=document.createElement('button');b.type='button';b.textContent=a.name+' ('+a.id+')';b.setAttribute('role','option');b.setAttribute('aria-selected',String(String(a.id)===select.value));b.onclick=()=>choose(a);list.append(b)}}
 trigger.onclick=()=>{if(!panel.hidden)return close();panel.hidden=false;trigger.setAttribute('aria-expanded','true');input.value='';render();input.focus()};input.oninput=render;
 box.onfocusout=e=>{if(!box.contains(e.relatedTarget))close()};
 box.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();close();trigger.focus();return}if(['ArrowDown','ArrowUp'].includes(e.key)&&!panel.hidden){e.preventDefault();active=Math.max(0,Math.min(matches.length-1,active+(e.key==='ArrowDown'?1:-1)));[...list.children].forEach((b,i)=>b.classList.toggle('active',i===active));list.children[active]?.scrollIntoView({block:'nearest'})}if(e.key==='Enter'&&e.target===input){e.preventDefault();if(matches.length)choose(matches[Math.max(active,0)])}};
 select.addEventListener('change',sync);sync();
}