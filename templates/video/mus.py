# generic music: usage python3 mus.py <json spec> ; spec in cwd music.json {dur, chords:[[freqs,t0,t1]], hits:[[t,type,args]]}
import numpy as np,json
spec=json.load(open('music.json'))
D=spec['dur']
exec(open('/home/claude/work/reel/music.py').read().split('# pad progression')[0].replace('S=1.2; DUR=19*S',f'S=1.0; DUR={D}'))
CH={'Am':[110,164.81,220,261.63,329.63],'F':[87.31,130.81,174.61,220,261.63],'C':[130.81,196,261.63,329.63],'G':[98,146.83,196,246.94,293.66]}
for n,a,b in spec['chords']: pad(CH[n],a,b,0.06 if n!='Am' or a<D-3 else 0.07,**({'att':.6,'rel':.01} if b>=D else {}))
t=tt(DUR); add(0.045*np.sin(2*np.pi*55*t)*np.minimum(1,t/2)*np.minimum(1,(DUR-t)/1.5),0,0,1)
for h in spec['hits']:
    T,k=h[0],h[1]
    if k=='pl': add(pluck(h[2],1.6,.26),T,h[3] if len(h)>3 else 0)
    elif k=='st': add(stab(h[2],3.0 if len(h)>3 else 2.2,.15 if len(h)>3 else .14),T,0,1)
    elif k=='sub': add(sub(1.6,.6),T,0,1)
    elif k=='wh': add(whoosh(),T,0,1)
    elif k=='tk': add(tick(),T,0,h[2] if len(h)>2 else .6)
    elif k=='tc': add(tock(h[2],.4,.3),T,0,1)
exec('ir_t=tt(2.4)'+open('/home/claude/work/reel/music.py').read().split('ir_t=tt(2.4)')[1])
