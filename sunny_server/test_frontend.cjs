// Regression checks execute the actual helper/listener code without a browser dependency.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(__dirname+'/static/js/legacy.js','utf8');
const context={};vm.createContext(context);
vm.runInContext(source.slice(0,source.indexOf('function serverRequest(')),context);
assert(context.serverErrorMessage(403,'{"code":"csrf_failed"}').includes('CSRF'));
assert(!context.serverErrorMessage(403,'<html>secret traceback</html>').includes('<html>'));
assert(context.serverErrorMessage(409,'').includes('người khác'));
let click;
class Input{constructor(type){this.type=type;this.count=0;}showPicker(){this.count++;}}
Object.assign(context,{document:{addEventListener:(name,fn)=>{click=fn}},HTMLInputElement:Input});
vm.runInContext(source.slice(source.lastIndexOf("document.addEventListener('click',event=>")),context);
for(const type of ['date','month']){const input=new Input(type);click({target:input});assert.equal(input.count,1);}
const disabled=new Input('date');disabled.disabled=true;click({target:disabled});assert.equal(disabled.count,0);
const other=new Input('text');click({target:other});assert.equal(other.count,0);
const unsupported=new Input('date');unsupported.showPicker=undefined;click({target:unsupported});
const rejected=new Input('date');rejected.showPicker=()=>{throw Error('NotAllowed')};click({target:rejected});
click({target:{}});
console.log('PASS: date/month picker delegation, fallbacks and safe error messages.');
