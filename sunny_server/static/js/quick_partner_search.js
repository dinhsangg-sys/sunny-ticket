function partnerSearchText(value){return String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[đĐ]/g,'d').toLowerCase().trim()}
function attachPartnerQuickSearch(select,agents){
 const box=document.createElement('div');box.className='partner-quick-search';
 const input=document.createElement('input');input.className='input';input.type='search';input.placeholder='Tìm theo tên hoặc mã đối tác...';input.setAttribute('aria-label','Tìm nhanh '+select.name);
 const list=document.createElement('div');list.className='partner-quick-results';list.setAttribute('role','listbox');list.hidden=true;
 select.before(box);box.append(input,list);let matches=[],active=-1;
 function choose(a){select.value=a.id;input.value=a.name+' ('+a.id+')';list.hidden=true;select.dispatchEvent(new Event('input',{bubbles:true}));select.dispatchEvent(new Event('change',{bubbles:true}))}
 function render(){const q=select.value?'':partnerSearchText(input.value);matches=agents.filter(a=>!q||partnerSearchText(a.name+' '+a.id).includes(q)).slice(0,40);active=-1;list.replaceChildren();list.hidden=false;if(!matches.length){list.textContent='Không tìm thấy đối tác';return}for(const a of matches){const b=document.createElement('button');b.type='button';b.textContent=a.name+' ('+a.id+')';b.setAttribute('role','option');b.onpointerdown=e=>e.preventDefault();b.onmousedown=e=>e.preventDefault();b.onclick=()=>choose(a);list.append(b)}}
 input.oninput=()=>{select.value='';select.dispatchEvent(new Event('input',{bubbles:true}));render()};input.onfocus=render;input.onblur=()=>{list.hidden=true};
 input.onkeydown=e=>{if(e.key==='Escape'){list.hidden=true;return}if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();if(list.hidden)render();active=Math.max(0,Math.min(matches.length-1,active+(e.key==='ArrowDown'?1:-1)));[...list.children].forEach((b,i)=>b.classList.toggle('active',i===active))}if(e.key==='Enter'&&!list.hidden){e.preventDefault();if(matches.length)choose(matches[Math.max(active,0)])}};
 select.addEventListener('change',()=>{const a=agents.find(a=>a.id===select.value);input.value=a?a.name+' ('+a.id+')':''});
 const initial=agents.find(a=>a.id===select.value);if(initial)input.value=initial.name+' ('+initial.id+')';
}
