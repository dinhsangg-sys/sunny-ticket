const fs=require('fs'),vm=require('vm'),assert=require('assert'),{webcrypto}=require('crypto');
const source=fs.readFileSync(__dirname+'/static/js/uuid_compat.js','utf8');
const context={crypto:{getRandomValues:array=>webcrypto.getRandomValues(array)}};vm.createContext(context);vm.runInContext(source,context);
const values=new Set();for(let i=0;i<1000;i++){const value=context.crypto.randomUUID();assert.match(value,/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);values.add(value)}assert.equal(values.size,1000);
const first=context.crypto.randomUUID;vm.runInContext(source,context);assert.equal(context.crypto.randomUUID,first);
const native=()=> 'native',secure={crypto:{randomUUID:native}};vm.createContext(secure);vm.runInContext(source,secure);assert.equal(secure.crypto.randomUUID,native);
console.log('PASS: crypto-backed UUID v4, version/variant bits, uniqueness sample, repeated load and native implementation preserved.');
