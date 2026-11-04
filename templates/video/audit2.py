import sys
from playwright.sync_api import sync_playwright
JS='''(t)=>{setT(t);const out=[];
const vis=d=>{let e=d,o=1;while(e&&e.id!=='c'){o*=parseFloat(e.style.opacity||1);e=e.parentElement}return o};
document.querySelectorAll('#c *').forEach(d=>{
 if(d.closest('svg')&&d.tagName!=='svg')return; if(d.tagName==='IMG')return;
 const hasTxt=[...d.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());
 const isSvg=d.tagName==='svg'&&d.closest('div.a')&&d.id!=='';
 if(!hasTxt&&!(d.tagName==='svg'&&d.getAttribute('width')&&d.getAttribute('width')<600)&&!(d.tagName==='IMG'))return;
 if(vis(d)<.99)return;
 const r=document.createRange();r.selectNodeContents(d);let rs=[...r.getClientRects()].filter(q=>q.width>2&&q.height>2);
 if(d.tagName==='svg')rs=[d.getBoundingClientRect()];
 if(!rs.length)return;let l=1e9,rt=-1e9,tp=1e9,bt=-1e9;rs.forEach(q=>{l=Math.min(l,q.left);rt=Math.max(rt,q.right);tp=Math.min(tp,q.top);bt=Math.max(bt,q.bottom)});
 const h=bt-tp;out.push({id:d.tagName==='svg'?'[icon]':(d.textContent||'').trim().slice(0,20),l,r:rt,t:tp+h*.2,b:bt-h*.2})});return out}'''
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--allow-file-access-from-files'])
    for f in sys.argv[1:]:
        pg=b.new_page(viewport={'width':1080,'height':1920}); pg.goto('file://'+f); pg.wait_for_timeout(700); pg.evaluate("document.fonts.ready")
        probs=set()
        for k in range(0,190):
            els=pg.evaluate(JS,k*0.1)
            for e in els:
                if e['id']=='[icon]' and 'checks' not in f: continue
                if e['l']<84 or e['r']>996: probs.add(f"margin {e['id']!r} l={e['l']:.0f} r={e['r']:.0f}")
            for i in range(len(els)):
                for j in range(i+1,len(els)):
                    a,c=els[i],els[j]
                    if a['l']<c['r']-4 and c['l']<a['r']-4 and a['t']<c['b']-4 and c['t']<a['b']-4: probs.add(f"overlap {a['id']!r} / {c['id']!r}")
        print(f.split('/')[-2] if 'wk2v' in f else f.split('/')[-1], sorted(probs) or 'OK'); pg.close()
    b.close()
