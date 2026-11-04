import math,pathlib,sys
from playwright.sync_api import sync_playwright
B=pathlib.Path('/home/claude/work'); F=B/'fonts/node_modules/@fontsource'
CSS=f"""@font-face{{font-family:'Jost';font-weight:300;src:url('file://{F}/jost/files/jost-latin-300-normal.woff2')}}
@font-face{{font-family:'Outfit';font-weight:300;src:url('file://{F}/outfit/files/outfit-latin-300-normal.woff2')}}
@font-face{{font-family:'Outfit';font-weight:400;src:url('file://{F}/outfit/files/outfit-latin-400-normal.woff2')}}
@font-face{{font-family:'DM Mono';font-weight:400;src:url('file://{F}/dm-mono/files/dm-mono-latin-400-normal.woff2')}}
body{{margin:0}}"""
TH={'night':dict(bg='#121515',fg='#F4F9F9',sub='#A9B2B4',lab='#A9B2B4',ring='#F4F9F9',ro=.28,logo='aerelo-mark-small-light.svg',dim='#7C8588',num='#5BC0CC',rule='rgba(244,249,249,.14)',btnt='#121515'),
    'paper':dict(bg='#F7F5F0',fg='#0C2027',sub='#3E5257',lab='#3E5257',ring='#0C2027',ro=.28,logo='aerelo-mark-small-ink.svg',dim='#6B7B80',num='#066B76',rule='rgba(12,32,39,.14)',btnt='#0C2027')}
def mono(c,s=24): return f"font-family:'DM Mono',monospace;font-size:{s}px;letter-spacing:.2em;text-transform:uppercase;color:{c};"
def dots(a,n,t):
    o=[]
    for i in range(n):
        x=14+i*40
        o.append(f'<circle cx="{x}" cy="14" r="13" fill="#F5C13A" fill-opacity=".25"/><circle cx="{x}" cy="14" r="6.5" fill="#F5C13A"/>' if i==a else f'<circle cx="{x}" cy="14" r="5" fill="none" stroke="{t["dim"]}" stroke-width="1.5"/>')
    return f'<svg width="{28+(n-1)*40}" height="28" viewBox="0 0 {28+(n-1)*40} 28" style="display:block">'+''.join(o)+'</svg>'
def ringsvg(i,n,t,dotx=None):
    W=1080*n
    def y(x): u=min(max(x/W,0),1); return 1130-420*u-60*math.sin(math.pi*u)
    pts=' L'.join(f'{lx},{y(i*1080+lx):.1f}' for lx in range(-40,1121,20))
    dl=900-130*i if dotx is None else dotx; dy=y(i*1080+dl)
    return f'<svg style="position:absolute;left:0;top:0" width="1080" height="1350"><path d="M{pts}" fill="none" stroke="{t["ring"]}" stroke-opacity="{t["ro"]}" stroke-width="2"/><circle cx="{dl}" cy="{dy:.1f}" r="26" fill="#F5C13A" fill-opacity=".25"/><circle cx="{dl}" cy="{dy:.1f}" r="13" fill="#F5C13A"/></svg>'
def foot(t,right):
    return f'<div style="position:relative;display:flex;align-items:center;justify-content:space-between"><div style="display:flex;align-items:center;gap:20px"><img src="file://{B}/logo/{t["logo"]}" style="height:64px;display:block"><div style="font-family:Outfit;font-weight:300;font-size:30px;letter-spacing:.3em;text-transform:uppercase;color:{t["fg"]}">Aerelo</div></div><div style="{mono(t["lab"],22)}">{right}</div></div>'
def wrap(t,inner): return f'<div style="width:1080px;height:1350px;box-sizing:border-box;padding:96px 88px 80px 88px;background:{t["bg"]};color:{t["fg"]};font-family:Outfit,sans-serif;display:flex;flex-direction:column;position:relative;overflow:hidden">{inner}</div>'
def topbar(t,label,i=None,n=None):
    d=dots(i,n,t) if n else ''
    return f'<div style="position:relative;display:flex;align-items:center;justify-content:space-between"><div style="{mono(t["lab"])}">{label}</div>{d}</div><div style="position:relative;margin-top:28px;width:60px;height:3px;background:#F5C13A"></div>'
def single(th,label,head,size,sub,right='Above the ordinary.',dotx=860):
    t=TH[th]
    return wrap(t,ringsvg(0,1,t,dotx).replace('1130-420','1130')+topbar(t,label)+f'<h1 style="position:relative;margin:90px 0 0;font-family:Jost;font-weight:300;font-size:{size}px;line-height:1.0;letter-spacing:-.015em">{head}</h1><div style="flex:1"></div><div style="position:relative;width:820px;font-size:38px;line-height:1.35;color:{t["sub"]};margin-bottom:96px">{sub}</div>'+foot(t,right))
def single_ring(th,label,head,size,sub,right='Above the ordinary.'):
    t=TH[th]; W=1080
    pts=' L'.join(f'{x},{940-170*((x+40)/1160)-36*math.sin(math.pi*(x+40)/1160):.1f}' for x in range(-40,1121,20)); dy=940-170*(900/1160)-36*math.sin(math.pi*900/1160)
    r=f'<svg style="position:absolute;left:0;top:0" width="1080" height="1350"><path d="M{pts}" fill="none" stroke="{t["ring"]}" stroke-opacity=".28" stroke-width="2"/><circle cx="860" cy="{940-170*(900/1160)-36*math.sin(math.pi*900/1160):.1f}" r="26" fill="#F5C13A" fill-opacity=".25"/><circle cx="860" cy="{940-170*(900/1160)-36*math.sin(math.pi*900/1160):.1f}" r="13" fill="#F5C13A"/></svg>'
    return wrap(t,r+topbar(t,label)+f'<h1 style="position:relative;margin:90px 0 0;font-family:Jost;font-weight:300;font-size:{size}px;line-height:1.0;letter-spacing:-.015em">{head}</h1><div style="flex:1"></div><div style="position:relative;width:820px;font-size:38px;line-height:1.35;color:{t["sub"]};margin-bottom:96px">{sub}</div>'+foot(t,right))
def cover(th,n,label,head,size=150,hint='Swipe'):
    t=TH[th]
    return wrap(t,ringsvg(0,n,t)+topbar(t,label,0,n)+f'<h1 style="position:relative;margin:90px 0 0;font-family:Jost;font-weight:300;font-size:{size}px;line-height:1.0;letter-spacing:-.015em">{head}</h1><div style="flex:1"></div>'+foot(t,hint+' →'))
def content(th,i,n,num,title,lead):
    t=TH[th]
    return wrap(t,ringsvg(i,n,t)+topbar(t,f'{num} / {n-2:02d}',i,n)+f'<div style="position:relative;margin-top:110px;{mono(t["num"],30)}">{num}</div><h2 style="position:relative;margin:24px 0 0;font-family:Jost;font-weight:300;font-size:118px;line-height:1.04;letter-spacing:-.01em">{title}</h2><div style="position:relative;margin-top:56px;width:860px;font-size:44px;line-height:1.35;color:{t["sub"]}">{lead}</div><div style="flex:1"></div>'+foot(t,''))
def close(th,i,n,head,sub=''):
    t=TH[th]
    return wrap(t,ringsvg(i,n,t)+topbar(t,'Next',i,n)+f'<h2 style="position:relative;margin:110px 0 0;font-family:Jost;font-weight:300;font-size:104px;line-height:1.06;letter-spacing:-.01em">{head}</h2><div style="position:relative;margin-top:36px;width:820px;font-size:38px;line-height:1.35;color:{t["sub"]}">{sub}</div><div style="flex:1"></div><div style="position:relative;align-self:flex-start;background:#F5C13A;color:#121515;font-size:38px;font-weight:400;padding:30px 56px;border-radius:60px;margin-bottom:80px">Message us to begin</div>'+foot(t,'Above the ordinary.'))
def carousel(th,label,title,size,items,closeh,closesub=''):
    n=len(items)+2
    out=[cover(th,n,label,title,size)]
    for k,(a,b) in enumerate(items): out.append(content(th,k+1,n,f'{k+1:02d}',a,b))
    out.append(close(th,n-1,n,closeh,closesub)); return out
def render(slides,names,outdir):
    outdir=pathlib.Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--allow-file-access-from-files'])
        pg=b.new_page(viewport={'width':1080,'height':1350})
        for h,nm in zip(slides,names):
            f=outdir/(nm+'.html'); f.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{h}</body></html>")
            pg.goto('file://'+str(f)); pg.wait_for_timeout(500); pg.evaluate("document.fonts.ready"); pg.screenshot(path=str(outdir/(nm+'.png')))
        b.close()
if __name__=='__main__':
    O='/home/claude/work/wk2/out'
    S=[];N=[]
    S.append(single_ring('night','Design principle','One page.<br>One job.',168,'Decide what a page is for, then cut everything that does not help it.'));N.append('mon-single-one-page-one-job')
    S+=carousel('night','Homepage','What your<br>homepage must<br>answer, in order.',128,[('What do you do?','Say it in the first line. Plain words beat clever ones.'),('Is it for me?','Show who you help, so the right visitor recognises themselves.'),('Can I trust you?','Real work, real details and a clear way to reach you.'),('What happens next?','One clear action, repeated where a visitor is ready.')],'Start with the questions your site must answer.')
    N+=[f'mon-carousel-homepage-{i+1}' for i in range(6)]
    S.append(single_ring('paper','Included','Copywriting and SEO are included.',124,'Not an add-on. Part of the build.'));N.append('tue-single-copywriting-seo-included')
    S+=carousel('paper','Content','Words come<br>before design.',150,[('Write the page first','Layout should serve the message, not the other way round.'),('Lead with the visitor','Start with their problem, not your history.'),('One message per section','If a section makes two points, split it.'),('Name the next step','Every page ends with something to do.')],'Copywriting and SEO are included.','Message us and we will start with your words.')
    N+=[f'tue-carousel-words-before-design-{i+1}' for i in range(6)]
    render(S,N,O)
