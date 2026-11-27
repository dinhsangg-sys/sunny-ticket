document.addEventListener('DOMContentLoaded',()=>{document.querySelectorAll('.sunny-editor').forEach(root=>{
const box=root.querySelector('.sunny-editable'),field=root.querySelector('textarea'),status=root.querySelector('.sunny-editor-status'),file=root.querySelector('input[type=file]'),preview=root.querySelector('.sunny-preview');let range=null;
const sync=()=>{field.value='<!--sunny-rich-->'+box.innerHTML;};
const remember=()=>{const s=getSelection();if(s.rangeCount&&box.contains(s.anchorNode))range=s.getRangeAt(0).cloneRange();};
const restore=()=>{box.focus();if(range){const s=getSelection();s.removeAllRanges();s.addRange(range);}};
box.addEventListener('input',sync);box.addEventListener('keyup',remember);box.addEventListener('mouseup',remember);
box.addEventListener('paste',e=>{e.preventDefault();document.execCommand('insertText',false,e.clipboardData.getData('text/plain'));sync();});
box.addEventListener('drop',e=>e.preventDefault());
root.querySelectorAll('[data-command]').forEach(b=>b.addEventListener('click',()=>{restore();document.execCommand(b.dataset.command,false,b.dataset.value||null);sync();remember();}));
root.querySelector('[data-link]').addEventListener('click',()=>{const url=prompt('Địa chỉ liên kết (https://...)');if(url&&/^https?:\/\//i.test(url)){restore();document.execCommand('createLink',false,url);sync();}});
root.querySelector('[data-image]').addEventListener('click',()=>{remember();file.click();});
file.addEventListener('change',async()=>{if(!file.files[0])return;status.textContent='Đang tải ảnh…';const data=new FormData();data.append('image',file.files[0]);try{const token=document.querySelector('[name=csrfmiddlewaretoken]').value;const r=await fetch('/online/editor/upload/',{method:'POST',headers:{'X-CSRFToken':token},body:data});const result=await r.json();if(!r.ok)throw Error(result.error||'Không tải được ảnh.');restore();const img=document.createElement('img');img.src=result.url;img.alt=prompt('Mô tả ảnh / chú thích ngắn')||'';const selection=getSelection();if(selection.rangeCount){const pos=selection.getRangeAt(0);pos.deleteContents();pos.insertNode(img);pos.setStartAfter(img);pos.collapse(true);}else box.append(img);sync();remember();status.textContent='Đã chèn ảnh. Có thể viết chú thích bên dưới.';}catch(e){status.textContent=e.message;}finally{file.value='';}});
root.querySelector('[data-preview]').addEventListener('click',e=>{const show=preview.hidden;if(show){preview.innerHTML=box.innerHTML;}preview.hidden=!show;box.hidden=show;e.target.textContent=show?'Tiếp tục soạn':'Xem trước';});
box.closest('form').addEventListener('submit',()=>{if(field.value.startsWith('<!--sunny-rich-->'))sync();});
});});
