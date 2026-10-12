"""Synthesizes the SFX track from sfx.json (timeline exported by index.html)."""
import json, sys, wave, numpy as np
SR=48000; DUR=float(sys.argv[2]) if len(sys.argv)>2 else 30.4
rng=np.random.default_rng(4)
def env(n,a,d):  # attack/decay envelope in seconds
    t=np.arange(n)/SR; return np.minimum(t/max(a,1e-4),1)*np.exp(-np.maximum(t-a,0)/d)
def noise(n): return rng.standard_normal(n)
def lp(x,c):     # one-pole lowpass, c can be array (0..1)
    y=np.zeros_like(x); c=np.broadcast_to(c,x.shape); s=0.
    for i in range(len(x)): s+=c[i]*(x[i]-s); y[i]=s
    return y
def sweep(f0,f1,n,curve=2):
    f=f0+(f1-f0)*(np.linspace(0,1,n)**curve); return np.sin(2*np.pi*np.cumsum(f)/SR)
def whoosh(len_=.9,big=False):
    # soft air whoosh: low-passed noise, smooth bell envelope, gentle filter sweep
    n=int(SR*len_); t=np.linspace(0,1,n); shape=np.sin(np.pi*t)**3
    c=.004+.045*shape; x=lp(lp(noise(n),c),c)*shape
    return x/np.abs(x).max()*.55
def pop():
    n=int(SR*.14); return sweep(900,180,n,.5)*env(n,.002,.035)*.9+lp(noise(n),.4)*env(n,.0005,.006)*.4
def click():
    n=int(SR*.06); return (lp(noise(n),.6)*env(n,.0003,.004)+sweep(2500,1800,n)*env(n,.0005,.008)*.5)*.9
def tick():
    n=int(SR*.05); return sweep(3200,3000,n)*env(n,.0005,.01)*.6
def ding(f=1760):
    n=int(SR*1.2); t=np.arange(n)/SR
    x=(np.sin(2*np.pi*f*t)+.5*np.sin(2*np.pi*f*2.01*t)+.25*np.sin(2*np.pi*f*3.02*t))*env(n,.002,.25)
    return x*.45
def cash():
    a=ding(2637)*.7; b=np.concatenate([np.zeros(int(SR*.09)),ding(3520)*.6])[:len(a)]
    n=int(SR*.12); c=np.zeros(len(a)); c[:n]=lp(noise(n),.5)*env(n,.001,.03)*.6
    return a+b+c
def impact():
    n=int(SR*1.4); x=sweep(110,38,n,.4)*env(n,.003,.35)*1.0+lp(noise(n),.08)*env(n,.001,.08)*1.5
    return np.tanh(x*1.3)*.85
def flutter():
    n=int(SR*.5); t=np.arange(n)/SR; am=(np.sin(2*np.pi*22*t)>0)*1.
    return lp(noise(n),.15)*am*env(n,.02,.18)*.5
def riser():
    n=int(SR*1.1); t=np.linspace(0,1,n); return (sweep(200,1400,n,1.5)*.25+lp(noise(n),.02+.3*t)*.6)*t**2*.7
def suck():
    return whoosh(.4)[::-1]*.9
def scratch():
    n=int(SR*.3); return lp(noise(n),.25)*env(n,.005,.08)*(1+np.sin(np.linspace(0,30,n)))*.4
GEN=dict(whoosh=lambda:whoosh(),swoosh=lambda:whoosh(.7,True),pop=pop,click=click,tick=tick,ding=ding,cash=cash,
         impact=impact,flutter=flutter,riser=riser,suck=suck,scratch=scratch)
out=np.zeros((int(SR*DUR)+SR,2))
for i,e in enumerate(json.load(open(sys.argv[1]))):
    x=GEN[e['type']]()*e['g']; s=int(max(e['t'],0)*SR)
    if e['type'] in('whoosh','swoosh','suck'): s=max(0,s-int(SR*.42))  # peak lands on the cut
    pan=np.sin(i*1.7)*.35; seg=out[s:s+len(x)]; m=len(seg)
    seg[:,0]+=x[:m]*(1-pan); seg[:,1]+=x[:m]*(1+pan)
out=out[:int(SR*DUR)]; out=np.tanh(out*.9)*.9
w=wave.open(sys.argv[3] if len(sys.argv)>3 else 'sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
