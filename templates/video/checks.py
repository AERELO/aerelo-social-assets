from eng import build
body=r'''
const ringY=x=>1590-70*(x/1080)-26*Math.sin(Math.PI*x/1080);
let pts=[];for(let x=-20;x<=1100;x+=20)pts.push(x+','+ringY(x).toFixed(1));
C.insertAdjacentHTML('beforeend',`<svg style="position:absolute;left:0;top:0" width="1080" height="1920"><path d="M${pts.join(' L')}" fill="none" stroke="#F4F9F9" stroke-opacity=".22" stroke-width="2"/><g id="dot"><circle r="26" fill="#F5C13A" fill-opacity=".25"/><circle r="13" fill="#F5C13A"/></g></svg>`);
const dot=document.getElementById('dot');
const l=mk('Homepage check','top:300px;',"a m");reg(l,.2,.6,0,-20,3.6);
[['Four checks.',-140,0],['Ten seconds.',140,0]].forEach((w,i)=>{const e=mk(w[0],`top:${430+i*160}px;font-size:132px;`,"a h");reg(e,.5+i*.5,.7,w[1],0,3.7,eb)});
const q=['What do you do?','Is it for me?','Can I trust you?','What happens next?'],T=[4.2,6.0,7.8,9.6];
const cks=[];
q.forEach((s,i)=>{
 const y=560+i*210;
 const r=mk(`<span style="position:absolute;left:100px;top:${y+12}px;font-size:26px;font-family:'DM Mono';letter-spacing:.2em;color:#A9B2B4">0${i+1}</span><span style="position:absolute;left:190px;top:${y-8}px;font-size:64px;font-family:Jost;font-weight:300">${s}</span><svg style="position:absolute;left:880px;top:${y-4}px" width="110" height="110" viewBox="0 0 110 110"><circle cx="55" cy="55" r="46" fill="none" stroke="rgba(244,249,249,.3)" stroke-width="3"/><path class="ck" d="M30 57 L47 74 L82 36" fill="none" stroke="#F5C13A" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>`,'top:0;height:1920px;text-align:left',"a");
 reg(r,T[i]-.5,.5,-60,0,11.2);cks.push(r)});
const c1=mk('Does your','top:420px;font-size:112px;',"a h");reg(c1,11.6,.7,-140,0,null,eb);
const c2=mk('homepage pass?','top:570px;font-size:112px;color:#F5C13A',"a h");reg(c2,12.1,.7,140,0,null,eb);
const cta=mk('Message us to begin','top:1000px;left:240px;width:600px;height:104px;border-radius:52px;background:#F5C13A;color:#121515;font-size:38px;font-weight:400;line-height:104px;text-align:center',"a");cta.style.left='240px';reg(cta,13.8,.7,0,50,null,eb);
const lg=mk('<img src="file:///home/claude/work/logo/aerelo-mark-small-light.svg" style="height:84px;display:block;margin:0 auto 18px"><div style="font-family:Outfit;font-weight:300;font-size:32px;letter-spacing:.3em;text-transform:uppercase">Aerelo</div>','top:1180px;',"a");reg(lg,14.6,.7,0,30,null);
function extra(t){cks.forEach((r,i)=>r.querySelector('.ck').setAttribute('stroke-dashoffset',1-eo(cl((t-T[i])/.35))));const x=cl(t/17)*1000+40;dot.setAttribute('transform',`translate(${x},${ringY(x)})`)}
'''
build('checks','#121515','#F4F9F9','#A9B2B4',body,17.0,'/home/claude/work/wk2v/music_run.py')
