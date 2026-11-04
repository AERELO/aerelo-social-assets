from eng import build
body=r'''
const ringY=x=>1590-70*(x/1080)-26*Math.sin(Math.PI*x/1080);
let pts=[];for(let x=-20;x<=1100;x+=20)pts.push(x+','+ringY(x).toFixed(1));
C.insertAdjacentHTML('beforeend',`<svg style="position:absolute;left:0;top:0" width="1080" height="1920"><path d="M${pts.join(' L')}" fill="none" stroke="#F4F9F9" stroke-opacity=".22" stroke-width="2"/><g id="dot"><circle r="26" fill="#F5C13A" fill-opacity=".25"/><circle r="13" fill="#F5C13A"/></g></svg>`);
const dot=document.getElementById('dot');
const l=mk('Mobile speed','top:300px;',"a m");reg(l,.2,.6,0,-20,3.6);
[['One tenth',-140,0],['of a second.',140,0]].forEach((w,i)=>{const e=mk(w[0],`top:${420+i*150}px;font-size:132px;`,"a h");reg(e,.5+i*.5,.7,w[1],0,3.7,eb)});
const clk=mk('<div style="position:relative;width:520px;height:520px;margin:0 auto"><svg width="520" height="520" viewBox="0 0 520 520"><circle cx="260" cy="260" r="240" fill="none" stroke="rgba(244,249,249,.25)" stroke-width="4"/><path id="sw" d="M260 20 A240 240 0 1 1 259.9 20" fill="none" stroke="#F5C13A" stroke-width="8" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/><text x="260" y="290" text-anchor="middle" font-family="Jost" font-weight="300" font-size="110" fill="#F4F9F9">0.1s</text></svg></div>','top:900px;',"a");reg(clk,1.6,.7,0,40,3.7);
// scene B
const b1=mk('Deloitte and Google looked at','top:380px;font-size:44px;color:#A9B2B4;font-weight:300',"a");reg(b1,3.8,.6,0,-30,11.0);
const b2=mk('mobile retail sites.','top:445px;font-size:44px;color:#A9B2B4;font-weight:300',"a");reg(b2,4.0,.6,0,-30,11.0);
const g=mk('+0%','top:620px;font-size:300px;color:#F5C13A',"a h");reg(g,4.6,.5,0,40,11.0);
const g2=mk('retail conversions','top:970px;font-size:54px;font-weight:300',"a");reg(g2,5.4,.6,0,20,11.0);
const g3=mk('from a 0.1s faster mobile site','top:1050px;font-size:40px;color:#A9B2B4;font-weight:300',"a");reg(g3,6.0,.6,0,20,11.0);
const src=mk('Source: Deloitte and Google, 2020','top:1470px;font-size:21px;letter-spacing:.14em',"a m");reg(src,5.0,.6,0,0,null);items[items.length-1].base=.8;
// scene C
const c1=mk('Speed is','top:380px;font-size:112px;',"a h");reg(c1,11.4,.7,-140,0,null,eb);
const c2=mk('part of the','top:530px;font-size:112px;',"a h");reg(c2,11.8,.7,140,0,null,eb);
const c3=mk('first impression.','top:680px;font-size:112px;color:#F5C13A',"a h");reg(c3,12.2,.7,0,70,null,eb);
const cta=mk('Message us to begin','top:1000px;left:240px;width:600px;height:104px;border-radius:52px;background:#F5C13A;color:#121515;font-size:38px;font-weight:400;line-height:104px;text-align:center',"a");cta.style.left='240px';reg(cta,14.0,.7,0,50,null,eb);
const lg=mk('<img src="file:///home/claude/work/logo/aerelo-mark-small-light.svg" style="height:84px;display:block;margin:0 auto 18px"><div style="font-family:Outfit;font-weight:300;font-size:32px;letter-spacing:.3em;text-transform:uppercase">Aerelo</div>','top:1180px;',"a");reg(lg,14.8,.7,0,30,null);
function extra(t){
 document.getElementById('sw').setAttribute('stroke-dashoffset',1-eio(cl((t-1.9)/1.2)));
 g.textContent='+'+(eo(cl((t-4.9)/1.6))*8.4).toFixed(1)+'%';
 const x=cl(t/17.5)*1000+40;dot.setAttribute('transform',`translate(${x},${ringY(x)})`);
}
'''
build('speed','#121515','#F4F9F9','#A9B2B4',body,17.5,'/home/claude/work/wk2v/music_speed.py')
