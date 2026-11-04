import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile
sr=44100; S=1.2; DUR=19*S
N=int(sr*DUR); L=np.zeros(N); R=np.zeros(N)
rng=np.random.default_rng(7)
def add(sig,t,pan=0.0,g=1.0):
    i=int(t*sr); 
    if i>=N: return
    s=sig[:max(0,N-i)]
    L[i:i+len(s)]+=s*g*(1-pan)/2*1.4; R[i:i+len(s)]+=s*g*(1+pan)/2*1.4
def tt(d): return np.arange(int(sr*d))/sr
def pluck(f,d=1.6,amp=0.30):
    t=tt(d); env=np.exp(-3.2*t)*np.minimum(1,t/0.006)
    return amp*env*(np.sin(2*np.pi*f*t)+0.28*np.sin(2*np.pi*2*f*t)+0.10*np.sin(2*np.pi*3*f*t))
def stab(freqs,d=2.2,amp=0.14):
    return sum(pluck(f,d,amp) for f in freqs)
def sub(d=1.4,amp=0.55):
    t=tt(d); f=45+75*np.exp(-9*t); ph=2*np.pi*np.cumsum(f)/sr
    return amp*np.sin(ph)*np.exp(-3.2*t)*np.minimum(1,t/0.004)
def tick(d=0.22,amp=0.25):
    t=tt(d); n=rng.standard_normal(len(t)); sos=butter(4,3500,'hp',fs=sr,output='sos'); n=sosfilt(sos,n)
    return amp*(n*np.exp(-90*t)*0.6+np.sin(2*np.pi*1760*t)*np.exp(-28*t)*0.5)
def tock(f=220,d=0.3,amp=0.30):
    t=tt(d); return amp*np.sin(2*np.pi*f*t)*np.exp(-14*t)*np.minimum(1,t/0.003)
def whoosh(d=0.6,amp=0.10):
    t=tt(d); n=rng.standard_normal(len(t)); env=np.sin(np.pi*np.clip(t/d,0,1))**2
    out=np.zeros_like(n)
    sos=butter(2,[300,3000],'bp',fs=sr,output='sos'); return amp*sosfilt(sos,n)*env
def pad(freqs,t0,t1,amp=0.05,att=1.6,rel=1.8):
    d=t1-t0+rel; t=tt(d); env=np.minimum(1,t/att)*np.where(t<(t1-t0),1,np.exp(-(t-(t1-t0))*3.0/rel*1.0))
    sig=np.zeros(len(t))
    for f in freqs:
        for det in (-0.004,0.0,0.004):
            ff=f*(1+det)
            for h,a in ((1,1),(2,0.35),(3,0.18),(4,0.08)):
                sig+=a*np.sin(2*np.pi*ff*h*t+rng.uniform(0,6.28))
    sig*=amp/len(freqs)/3*env
    add(sig,t0,0,1.0)
N_=lambda n: 440*2**((n-69)/12)
A2,C3,E3,F2,G2,D3=110,130.81,164.81,87.31,98,146.83
Am=[110,164.81,220,261.63,329.63]; F=[87.31,130.81,174.61,220,261.63]; C=[130.81,196,261.63,329.63]; G=[98,146.83,196,246.94,293.66]
# pad progression, scaled to the video
pad(Am,0.0,8.64,0.06); pad(F,8.64,13.8,0.06); pad(C,13.8,16.92,0.06); pad(G,16.92,19.08,0.06,att=0.8,rel=0.6); pad(Am,19.08,DUR,0.07,att=0.6,rel=0.01)
# low drone
t=tt(DUR); drone=0.045*np.sin(2*np.pi*55*t)*np.minimum(1,t/2.0)*np.minimum(1,(DUR-t)/1.5); add(drone,0,0,1)
# hook words
add(pluck(440),0.6,-0.4); add(pluck(523.25),1.2,0.0); add(pluck(659.25),1.8,0.4)
add(stab([440,523.25,659.25,880]),2.76,0,1.0); add(sub(),2.76,0,1.0)
add(whoosh(),5.16,0,1)
# then ask + questions
add(pluck(329.63,1.6,0.22),6.0,0)
add(pluck(440,1.8,0.26)+pluck(659.25,1.8,0.2),6.6,-0.3)
add(pluck(523.25,1.8,0.26)+pluck(698.46,1.8,0.2),8.64,0.3)
add(whoosh(),10.8,0,1)
# countdown ticks on the beat
for k,T in enumerate([9.9,10.7,11.5,12.3,13.1]):
    tm=T*S; add(tick(),tm,0,1); add(tock(220 if k<4 else 261.63),tm,0,1)
    if k<4: add(pluck([440,493.88,523.25,587.33][k]*0.5,1.0,0.12),tm,0,1)
add(stab([261.63,329.63,392,523.25]),13.1*S,0,1.0)
# closing words
add(pluck(392,1.6,0.26),14.1*S,-0.4); add(pluck(493.88,1.6,0.26),14.55*S,0,1); add(pluck(587.33,1.6,0.26),15.0*S,0.4)
add(stab([220,261.63,329.63,440,659.25],3.0,0.15),15.9*S,0,1); add(sub(1.6,0.6),15.9*S,0,1)
add(pluck(1318.5,1.4,0.10),16.7*S,0.3); add(pluck(880,1.6,0.12),17.0*S,-0.2)
# reverb
ir_t=tt(2.4); ir=rng.standard_normal(len(ir_t))*np.exp(-2.6*ir_t); ir[:int(0.012*sr)]=0
def rv(x): 
    w=fftconvolve(x,ir)[:N]; w/= (np.max(np.abs(w))+1e-9); return w
dryL,dryR=L.copy(),R.copy()
wL=rv(L); wR=rv(R[::-1][::-1]*1.0)
mix=lambda d,w: d*0.78+w*0.22*np.max(np.abs(d))
L2=mix(dryL,wL); R2=mix(dryR,wR)
# fades
f_in=np.minimum(1,np.arange(N)/(0.4*sr)); f_out=np.minimum(1,(N-np.arange(N))/(1.6*sr))
L2*=f_in*f_out; R2*=f_in*f_out
pk=max(np.max(np.abs(L2)),np.max(np.abs(R2))); g=0.89/pk
st=np.stack([L2*g,R2*g],1)
wavfile.write('music.wav',sr,(st*32767).astype(np.int16)); print('ok',DUR,pk)
