(() => {
 const input=document.getElementById('id_password'),toggle=document.getElementById('password-toggle'),caps=document.getElementById('caps-hint');
 if(!input||!toggle)return;
 toggle.hidden=false;
 toggle.addEventListener('click',()=>{const show=input.type==='password';input.type=show?'text':'password';toggle.setAttribute('aria-pressed',String(show));toggle.setAttribute('aria-label',show?'Ẩn mật khẩu':'Hiện mật khẩu')});
 input.addEventListener('keyup',event=>{if(caps)caps.hidden=!event.getModifierState('CapsLock')});
 input.addEventListener('blur',()=>{if(caps)caps.hidden=true});
 document.getElementById('login-errors')?.focus();
})();
