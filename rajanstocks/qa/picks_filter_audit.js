const {chromium}=require('playwright');const mock=require('./picks_filter_mock.json');
const BY=Object.fromEntries(mock.picks.map(p=>[p.s,p]));const TOP=new Set(mock.top.map(t=>t.s));
(async()=>{const b=await chromium.launch();const ctx=await b.newContext({viewport:{width:390,height:900}});const p=await ctx.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.route('**/api/m/picks*',r=>r.fulfill({json:mock}));
await p.goto('http://localhost:8765/#pic');await p.waitForSelector('.pk-sec',{timeout:20000});await p.waitForTimeout(2500);
await p.click('[data-pksec=browse]');
const read=()=>p.evaluate(()=>{const cards=[...document.querySelectorAll('#pkRes .pk-grid > *')];const meta=(document.querySelector('#pkRes .pk-meta')||{}).textContent||'';
 return {meta,empty:(document.querySelector('#pkRes .empty')||{}).textContent||'',cards:cards.map(c=>({n:c.querySelector('b').textContent,badge:(c.querySelector('.pk-sig .badge')||{}).textContent,act:(c.querySelector('.pk-act')||{}).textContent})),on:[...document.querySelectorAll('#pkPanel .on, #pkPanel .chip.on')].map(x=>x.textContent.trim())}});
const click=async (k,v)=>{await p.click(`#pkPanel [data-pkf="${k}:${v}"]`);await p.waitForTimeout(60)};
const sel=async(id,v)=>{await p.selectOption(id,v);await p.waitForTimeout(60)};
const bugs={};const bug=(c,m)=>{(bugs[c]=bugs[c]||[]).push(m)};
const reset=async()=>{await p.evaluate(()=>{Object.assign(App.pk,{sig:'TOP',kind:'STOCK',hz:'ALL',mkt:'ALL',sort:'strength',size:0,page:0,q:'',str:'ALL'});renderPicks()})};
const IDX=/^(NIFTY|SENSEX|BANKNIFTY|MIDCPNIFTY|FINNIFTY|NIFTYIT)$/;
for(const sig of ['TOP','ALL','BUY','SELL','EVERY'])for(const hz of ['ALL','INTRA','SWING','POS'])for(const mkt of ['ALL','FNO','CASH'])for(const str of ['ALL','STRONG','HIGH','WEAK']){
  await reset();await click('sig',sig);await click('hz',hz);await click('mkt',mkt);await sel('#pkStr',str);
  const r=await read();const eff=(sig==='TOP'&&mkt==='CASH')?'ALL':sig;const tag=`${sig}/${hz}/${mkt}/${str}`;const hzk={INTRA:'intraday',SWING:'swing',POS:'positional'}[hz];
  for(const c of r.cards){const m=BY[c.n];if(!m){bug('unknown',tag+c.n);continue}
    if(IDX.test(c.n))bug('index in stocks',tag+' '+c.n);
    if(mkt==='FNO'&&m.universe==='cash')bug('cash in FNO',tag+' '+c.n);if(mkt==='CASH'&&m.universe!=='cash')bug('fno in Cash',tag+' '+c.n);
    const s=m.strength;if(str==='STRONG'&&s<65)bug('STRONG<65',tag+' '+c.n);if(str==='HIGH'&&s<75)bug('HIGH<75',tag+' '+c.n);if(str==='WEAK'&&s>=65)bug('WEAK>=65',tag+' '+c.n);
    if(eff==='BUY'&&!/BUY/.test(c.badge))bug('buy list badge',tag+' '+c.badge+' '+c.n);if(eff==='SELL'&&!/SELL/.test(c.badge))bug('sell list badge',tag+' '+c.badge+' '+c.n);
    if(hzk&&(eff==='BUY'||eff==='SELL')){const sd=m.plans[hzk].side;if(sd!==eff)bug('plan side',tag+' '+sd+' '+c.n)}
    if(eff==='TOP'&&!TOP.has(c.n))bug('not in top',tag+' '+c.n);
    const wantBuy=/BUY/.test(c.badge||'');const act=c.act||'';if(wantBuy&&/^Sell futures/.test(act))bug('action text',tag+' '+c.n+' '+act.slice(0,40));if(!wantBuy&&/SELL/.test(c.badge||'')&&/^Buy futures/.test(act))bug('action text',tag+' '+c.n+' '+act.slice(0,40))}
  const cnt=(r.meta.match(/^(\d+)/)||[])[1];if(r.cards.length!==(cnt?+cnt:0))bug('count',tag+' '+cnt+' vs '+r.cards.length);
  if(!r.cards.length&&!r.empty)bug('empty no message',tag);
  // completeness for plain filters
  if(hz==='ALL'&&str==='ALL'&&(eff==='BUY'||eff==='SELL')){const exp=mock.picks.filter(m=>m.kind==='stock'&&m.signal===eff&&(mkt==='ALL'||(mkt==='FNO'?m.universe!=='cash':m.universe==='cash'))).length;if(exp!==r.cards.length)bug('missing stocks',tag+' exp '+exp+' got '+r.cards.length)}
}
await reset();await click('sig','EVERY');
const sorts={strength:(a,b)=>b.strength-a.strength,chgdesc:(a,b)=>b.chg-a.chg,chgasc:(a,b)=>a.chg-b.chg,volx:(a,b)=>b.volx-a.volx,name:(a,b)=>a.s.localeCompare(b.s)};
for(const k of Object.keys(sorts)){await p.evaluate(k=>{App.pk.sort=k;renderPicks()},k);const r=await read();const v=r.cards.map(c=>BY[c.n]);
 for(let i=1;i<v.length;i++)if(sorts[k](v[i-1],v[i])>0){bug('sort '+k,v[i-1].s+' '+v[i].s);break}}
await p.evaluate(()=>{App.pk.sort='strength';renderPicks()});
console.log('size opts',(await p.$$eval('#pkSize option',e=>e.map(o=>o.value+':'+o.textContent))).join(' | '));
for(const size of ['15','30','100']){await sel('#pkSize',size);const seen=new Set();let pages=0;
  for(let i=0;i<20;i++){const r=await read();r.cards.forEach(c=>{if(seen.has(c.n))bug('page overlap',c.n);seen.add(c.n)});pages++;const nx=await p.$('[data-pkpage]:not([disabled]):text("Next")');if(!nx)break;await nx.click();await p.waitForTimeout(80)}
  if(seen.size!==80)bug('pagination coverage','size '+size+' saw '+seen.size+' of 80 over '+pages+' pages')}
await reset();await click('sig','EVERY');await p.fill('#pkQ','stk1');await p.waitForTimeout(300);let r=await read();if(r.cards.length!==10)bug('search','stk1 -> '+r.cards.length);
await p.fill('#pkQ','');await p.waitForTimeout(200);
await click('sig','BUY');await click('hz','SWING');await p.click('[data-pkreset]');await p.waitForTimeout(200);r=await read();console.log('after reset on:',r.on.join(','),'|',r.meta.slice(0,30));
for(const sig of ['TOP','ALL','BUY','SELL']){await p.click('#pkPanel [data-pkf="kind:INDEX"]');await p.waitForTimeout(80);await click('sig',sig);r=await read();
  for(const c of r.cards){if(!IDX.test(c.n))bug('idx stock',sig+c.n);if(sig==='BUY'&&/PUT/.test(c.badge))bug('idx buy put',c.n);if(sig==='SELL'&&/CALL/.test(c.badge))bug('idx sell call',c.n)}
  console.log('INDEX',sig,r.cards.map(c=>c.n+':'+c.badge).join(', '))}
await p.click('#pkPanel [data-pkf="kind:STOCK"]');await p.waitForTimeout(100);r=await read();console.log('back to stocks',r.meta.slice(0,40),'| on:',r.on.join(','));
for(const k in bugs)console.log('BUG',k,bugs[k].length,bugs[k].slice(0,4).join(' ; '));
console.log('DONE bugs',Object.keys(bugs).length,'errs',errs);await b.close()})()
