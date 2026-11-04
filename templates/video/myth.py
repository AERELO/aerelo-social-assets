from eng import build
body=r'''
const ringY=x=>1590-70*(x/1080)-26*Math.sin(Math.PI*x/1080);
let pts=[];for(let x=-20;x<=1100;x+=20)pts.push(x+','+ringY(x).toFixed(1));
C.insertAdjacentHTML('beforeend',`<svg style="position:absolute;left:0;top:0" width="1080" height="1920"><path d="M${pts.join(' L')}" fill="none" stroke="#0C2027" stroke-opacity=".25" stroke-width="2"/><g id="dot"><circle r="26" fill="#F5C13A" fill-opacity=".3"/><circle r="13" fill="#F5C13A"/></g></svg>`);
const dot=document.getElementById('dot');
const l=mk('Common myth','top:300px;',"a m");reg(l,.2,.6,0,-20,5.3);
[["“I’ll add",-140,0],['the website',0,80],['later.”',140,0]].forEach((w,i)=>{const e=mk(w[0],`top:${430+i*150}px;font-size:136px;`,"a h");reg(e,.5+i*.5,.7,w[1],w[2],5.3,eb)});
const bar=mk('','top:930px;left:440px;width:200px;height:4px;background:#F5C13A;border-radius:2px',"a");bar.style.left='440px';reg(bar,2.4,.5,0,0,5.3);
const w=mk('Meanwhile','top:300px;',"a m");reg(w,5.6,.6,0,-20,11.2);
[['Fewer people find you.',-140,0],['Fewer can book or buy.',140,0],['Someone else gets the call.',0,60]].forEach((x,i)=>{
 const d=mk('<span style="display:inline-block;width:18px;height:18px;border-radius:9px;background:#F5C13A;margin-right:28px;vertical-align:12px"></span>'+x[0],`top:${470+i*170}px;font-size:70px;`,"a h");reg(d,6.0+i*.9,.7,x[1],x[2],11.2,eb)});
const c1=mk('Start with the job','top:420px;font-size:112px;',"a h");reg(c1,11.6,.7,-140,0,null,eb);
const c2=mk('your site must do.','top:570px;font-size:112px;',"a h");reg(c2,12.1,.7,140,0,null,eb);
const cta=mk('Message us to begin','top:1000px;left:240px;width:600px;height:104px;border-radius:52px;background:#F5C13A;color:#121515;font-size:38px;font-weight:400;line-height:104px;text-align:center',"a");cta.style.left='240px';reg(cta,13.6,.7,0,50,null,eb);
const lg=mk('<img src="file:///home/claude/work/logo/aerelo-mark-small-ink.svg" style="height:84px;display:block;margin:0 auto 18px"><div style="font-family:Outfit;font-weight:300;font-size:32px;letter-spacing:.3em;text-transform:uppercase">Aerelo</div>','top:1180px;',"a");reg(lg,14.4,.7,0,30,null);
function extra(t){const x=cl(t/17.0)*1000+40;dot.setAttribute('transform',`translate(${x},${ringY(x)})`)}
'''
build('myth','#F7F5F0','#0C2027','#3E5257',body,17.0,'/home/claude/work/wk2v/music_myth.py')
