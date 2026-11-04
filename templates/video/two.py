from eng import build
body=r'''
const ringY=x=>1590-70*(x/1080)-26*Math.sin(Math.PI*x/1080);
let pts=[];for(let x=-20;x<=1100;x+=20)pts.push(x+','+ringY(x).toFixed(1));
C.insertAdjacentHTML('beforeend',`<svg style="position:absolute;left:0;top:0" width="1080" height="1920"><path d="M${pts.join(' L')}" fill="none" stroke="#F4F9F9" stroke-opacity=".22" stroke-width="2"/><g id="dot"><circle r="26" fill="#F5C13A" fill-opacity=".25"/><circle r="13" fill="#F5C13A"/></g></svg>`);
const dot=document.getElementById('dot');
const l=mk('Two more jobs','top:300px;',"a m");reg(l,.2,.6,0,-20,2.4);
[['Commerce.',-140,0],['Membership.',140,0]].forEach((w,i)=>{const e=mk(w[0],`top:${450+i*170}px;font-size:136px;`,"a h");reg(e,.5+i*.5,.7,w[1],0,2.5,eb)});
const k1=mk('Commerce','top:300px;',"a m");reg(k1,2.8,.5,0,-20,5.6);
const a1=mk('Sell products','top:470px;font-size:132px;',"a h");reg(a1,3.0,.7,-140,0,5.6,eb);
const a2=mk('online.','top:620px;font-size:132px;color:#F5C13A',"a h");reg(a2,3.5,.7,140,0,5.6,eb);
const k2=mk('Membership','top:300px;',"a m");reg(k2,6.0,.5,0,-20,10.2);
const b1=mk('Gate content.','top:470px;font-size:116px;',"a h");reg(b1,6.2,.7,-140,0,10.2,eb);
const b2=mk('Manage members.','top:610px;font-size:116px;color:#F5C13A',"a h");reg(b2,6.9,.7,140,0,10.2,eb);
const c1=mk('Which job','top:420px;font-size:112px;',"a h");reg(c1,10.6,.7,-140,0,null,eb);
const c2=mk('is yours?','top:570px;font-size:112px;color:#F5C13A',"a h");reg(c2,11.1,.7,140,0,null,eb);
const cta=mk('Message us to begin','top:1000px;left:240px;width:600px;height:104px;border-radius:52px;background:#F5C13A;color:#121515;font-size:38px;font-weight:400;line-height:104px;text-align:center',"a");cta.style.left='240px';reg(cta,12.6,.7,0,50,null,eb);
const lg=mk('<img src="file:///home/claude/work/logo/aerelo-mark-small-light.svg" style="height:84px;display:block;margin:0 auto 18px"><div style="font-family:Outfit;font-weight:300;font-size:32px;letter-spacing:.3em;text-transform:uppercase">Aerelo</div>','top:1180px;',"a");reg(lg,13.4,.7,0,30,null);
function extra(t){const x=cl(t/16)*1000+40;dot.setAttribute('transform',`translate(${x},${ringY(x)})`)}
'''
build('two','#121515','#F4F9F9','#A9B2B4',body,16.0,'/home/claude/work/wk2v/music_run.py')
