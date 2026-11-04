# shared: build an html reel from a scene spec, render frames, mux with music
import sys,pathlib,subprocess,json
from playwright.sync_api import sync_playwright
HEAD='''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:'Jost';font-weight:300;src:url('file:///home/claude/work/fonts/node_modules/@fontsource/jost/files/jost-latin-300-normal.woff2')}
@font-face{font-family:'Outfit';font-weight:300;src:url('file:///home/claude/work/fonts/node_modules/@fontsource/outfit/files/outfit-latin-300-normal.woff2')}
@font-face{font-family:'Outfit';font-weight:400;src:url('file:///home/claude/work/fonts/node_modules/@fontsource/outfit/files/outfit-latin-400-normal.woff2')}
@font-face{font-family:'DM Mono';font-weight:400;src:url('file:///home/claude/work/fonts/node_modules/@fontsource/dm-mono/files/dm-mono-latin-400-normal.woff2')}
body{margin:0;background:%(bg)s}#c{position:relative;width:1080px;height:1920px;background:%(bg)s;overflow:hidden;color:%(fg)s;font-family:'Outfit',sans-serif}
.a{position:absolute;left:0;width:1080px;text-align:center;white-space:nowrap}.h{font-family:'Jost',sans-serif;font-weight:300;letter-spacing:-.01em;line-height:1.08}
.m{font-family:'DM Mono',monospace;font-size:24px;letter-spacing:.2em;text-transform:uppercase;color:%(sub)s}
</style></head><body><div id="c"></div><script>
const C=document.getElementById('c');const items=[];
const cl=x=>Math.max(0,Math.min(1,x)),eo=p=>1-Math.pow(1-p,3),eio=p=>p<.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2,eb=p=>{const c=1.5;return 1+(c+1)*Math.pow(p-1,3)+c*Math.pow(p-1,2)};
function mk(html,css,cls){const d=document.createElement('div');d.className=cls||'a';d.style.cssText=css;d.innerHTML=html;C.appendChild(d);return d}
function reg(el,t0,dur,dx,dy,out,ease){items.push({el,t0,dur,dx,dy,out,ease:ease||eo})}
const GOLD='#F5C13A',SUB='%(sub)s',FG='%(fg)s';
%(body)s
function setT(t){items.forEach(o=>{const p=cl((t-o.t0)/o.dur),e=o.ease(p);let op=cl(e);if(o.out!=null)op*=1-cl((t-o.out)/.35);o.el.style.opacity=op;o.el.style.transform=`translate(${o.dx*(1-e)}px,${o.dy*(1-e)}px)`});if(typeof extra==='function')extra(t)}
setT(0);
</script></body></html>'''
def build(name,bg,fg,sub,body,dur,music):
    d=pathlib.Path('/home/claude/work/wk2v')/name; d.mkdir(exist_ok=True)
    (d/'r.html').write_text(HEAD%dict(bg=bg,fg=fg,sub=sub,body=body))
    only=[float(x) for x in sys.argv[1:]]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--allow-file-access-from-files'])
        pg=b.new_page(viewport={'width':1080,'height':1920}); pg.goto('file://'+str(d/'r.html')); pg.wait_for_timeout(800); pg.evaluate("document.fonts.ready")
        if only:
            for t in only: pg.evaluate(f"setT({t})"); pg.screenshot(path=str(d/f'chk_{t}.png'))
            b.close(); return
        (d/'frames').mkdir(exist_ok=True)
        for i in range(int(30*dur)): pg.evaluate(f"setT({i/30})"); pg.screenshot(path=str(d/'frames'/f'f_{i:04d}.png'))
        b.close()
    subprocess.run(['python3',music],cwd=d,check=True)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(d/'frames/f_%04d.png'),'-i',str(d/'music.wav'),'-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','loudnorm=I=-16:TP=-1.5','-shortest',str(d/(name+'.mp4'))],check=True)
