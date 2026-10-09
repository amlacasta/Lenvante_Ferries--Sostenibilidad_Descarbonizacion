// Browser-free interaction smoke check for the bundled, offline dashboard.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const html=fs.readFileSync(new URL('../site/index.html',import.meta.url),'utf8');
const raw=html.match(/<script id="dataset" type="application\/json">([\s\S]*?)<\/script>/)?.[1];
const script=html.match(/<script>\s*('use strict';[\s\S]*?)<\/script>/)?.[1];
assert(raw&&script);
const data=JSON.parse(raw);const elements=new Map();
function el(id){if(!elements.has(id)){
  let obj={value:'',disabled:false,textContent:'',innerHTML:'',setAttribute(){},addEventListener(){}};
  if(id==='fuel'){Object.defineProperty(obj,'innerHTML',{get(){return this._html||''},set(v){this._html=v;let chosen=v.match(/value="(MGO|LNG)"[^>]*selected/);this.value=chosen?.[1]||v.match(/value="(MGO|LNG)"/)?.[1]||''}})}
  elements.set(id,obj)}return elements.get(id)}
el('dataset').textContent=raw;el('route').value='0';
for(const [id,value] of Object.entries({speed:100,occupancy:70,bio:10,eua:75,ops:0,demand:100,fuelprice:100}))el(id).value=String(value);
const tabs=['overview','fleet','routes','transition','regulation','simulator'].map(tab=>({dataset:{tab},setAttribute(){},addEventListener(){}}));
const document={getElementById:el,querySelectorAll(q){return q==='[data-tab]'?tabs:[...elements.values()]}};
const context=vm.createContext({document,window:{scrollTo(){}},Intl,Math,JSON,Number,String,Array,Object});
vm.runInContext(script,context,{timeout:2000});
for(const tab of tabs){vm.runInContext(`active='${tab.dataset.tab}';render()`,context,{timeout:2000});assert(el('app').innerHTML.length>1200,tab.dataset.tab)}
const idx=data.simulator_samples.findIndex(r=>r.ops_available&&r.fuel==='LNG');assert(idx>=0);
el('route').value=String(idx);vm.runInContext('resetRoute()',context,{timeout:2000});
const base=el('simulation').innerHTML;assert(base.includes('Intensidad FuelEU proxy'));
el('ops').value='80';el('speed').value='94';el('eua').value='130';el('bio').value='35';
vm.runInContext('calcSim()',context,{timeout:2000});
const changed=el('simulation').innerHTML;assert.notEqual(changed,base);
assert(changed.includes('Coste total')&&changed.includes('Horario'));
el('fuel').value='MGO';vm.runInContext('calcSim()',context,{timeout:2000});assert.notEqual(el('simulation').innerHTML,changed);
console.log('OK: six sections render; OPS, speed, EUA, biofuel and compatible fuel recalculate simulator.');
