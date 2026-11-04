from eng import build
body=r'''
const ringY=x=>1590-70*(x/1080)-26*Math.sin(Math.PI*x/1080);
let pts=[];for(let x=-20;x<=1100;x+=20)pts.push(x+','+ringY(x).toFixed(1));
C.insertAdjacentHTML('beforeend',`<svg style="position:absolute;left:0;top:0" width="1080" height="1920"><path d="M${pts.join(' L')}" fill="none" stroke="#0C2027" stroke-opacity=".25" stroke-width="2"/><g id="dot"><circle r="26" fill="#F5C13A" fill-opacity=".3"/><circle r="13" fill="#F5C13A"/></g></svg>`);
const dot=document.getElementById('dot');
const l=mk('First impressions','top:300px;',"a m");reg(l,.2,.6,0,-20,3.4);
[['How do people',-140,0],['judge whether a',0,80],['site is credible?',140,0]].forEach((w,i)=>{const e=mk(w[0],`top:${420+i*150}px;font-size:116px;`,"a h");reg(e,.5+i*.5,.7,w[1],w[2],3.5,eb)});
const b1=mk('A Stanford study asked participants','top:400px;font-size:44px;color:#3E5257;font-weight:300',"a");reg(b1,3.6,.6,0,-30,11.0);
const b2=mk('to judge website credibility.','top:465px;font-size:44px;color:#3E5257;font-weight:300',"a");reg(b2,3.8,.6,0,-30,11.0);
const g=mk('0%','top:640px;font-size:300px;color:#0C2027',"a h");reg(g,4.2,.5,0,40,11.0);
const ul=mk('','top:990px;left:380px;width:320px;height:6px;background:#F5C13A;border-radius:3px',"a");ul.style.left='380px';reg(ul,5.8,.5,0,0,11.0);
const g2=mk('of participants judged credibility','top:1040px;font-size:48px;font-weight:300',"a");reg(g2,5.6,.6,0,20,11.0);
const g3=mk('partly by design','top:1105px;font-size:48px;font-weight:300',"a");reg(g3,6.0,.6,0,20,11.0);
const src=mk('Source: Stanford, 2002','top:1470px;font-size:21px;letter-spacing:.14em',"a m");reg(src,5.0,.6,0,0,null);items[items.length-1].base=.8;
const c1=mk('Looks are','top:400px;font-size:112px;',"a h");reg(c1,11.4,.7,-140,0,null,eb);
const c2=mk('part of','top:550px;font-size:112px;',"a h");reg(c2,11.8,.7,140,0,null,eb);
const c3=mk('trust.','top:700px;font-size:112px;',"a h");reg(c3,12.2,.7,0,70,null,eb);
const cta=mk('Message us to begin','top:1000px;left:240px;width:600px;height:104px;border-radius:52px;background:#F5C13A;color:#121515;font-size:38px;font-weight:400;line-height:104px;text-align:center',"a");cta.style.left='240px';reg(cta,13.8,.7,0,50,null,eb);
const lg=mk('<img src="file:///home/claude/work/logo/aerelo-mark-small-ink.svg" style="height:84px;display:block;margin:0 auto 18px"><div style="font-family:Outfit;font-weight:300;font-size:32px;letter-spacing:.3em;text-transform:uppercase">Aerelo</div>','top:1180px;',"a");reg(lg,14.6,.7,0,30,null);
function extra(t){g.textContent=(eo(cl((t-4.4)/1.6))*46.1).toFixed(1)+'%';const x=cl(t/18)*1000+40;dot.setAttribute('transform',`translate(${x},${ringY(x)})`)}
'''
build('stan','#F7F5F0','#0C2027','#3E5257',body,18.0,'/home/claude/work/wk2v/music_run.py')
