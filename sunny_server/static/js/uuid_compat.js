// Chrome exposes getRandomValues on HTTP LAN pages but randomUUID only in secure contexts.
// Keep native randomUUID when present; otherwise generate UUID v4 with Web Crypto entropy.
(()=>{
 const crypto=globalThis.crypto;
 if(!crypto||typeof crypto.randomUUID==='function')return;
 if(typeof crypto.getRandomValues!=='function')return;
 Object.defineProperty(crypto,'randomUUID',{configurable:true,writable:true,value:function(){
  const bytes=new Uint8Array(16);crypto.getRandomValues(bytes);
  bytes[6]=(bytes[6]&15)|64;bytes[8]=(bytes[8]&63)|128;
  const hex=Array.from(bytes,byte=>byte.toString(16).padStart(2,'0')).join('');
  return hex.slice(0,8)+'-'+hex.slice(8,12)+'-'+hex.slice(12,16)+'-'+hex.slice(16,20)+'-'+hex.slice(20);
 }});
})();
