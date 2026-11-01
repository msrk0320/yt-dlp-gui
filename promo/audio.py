"""Synthesizes the promo soundtrack (numpy only) so every hit lines up with the
scene timeline in scene.html. 120 BPM, 38 s, 44.1 kHz stereo WAV."""
import numpy as np, sys, wave
SR=44100; BPM=120; BEAT=60/BPM; DUR=38.0
N=int(SR*DUR); t=np.arange(N)/SR
L=np.zeros(N); R=np.zeros(N)
def add(sig,at,gain=1.0,pan=0.0):
    i=int(at*SR); n=min(len(sig),N-i)
    if n<=0: return
    L[i:i+n]+=sig[:n]*gain*(1-max(pan,0)); R[i:i+n]+=sig[:n]*gain*(1+min(pan,0))
def env(n,a,d,s=0.0,r=0.05,sus=0.0):
    e=np.ones(n); A=int(a*SR);D=int(d*SR);S=int(sus*SR);Rr=int(r*SR)
    e[:A]=np.linspace(0,1,A) if A else 1
    if D: e[A:A+D]=np.linspace(1,s,D)
    e[A+D:A+D+S]=s
    tail=n-(A+D+S)
    if tail>0: e[A+D+S:]=s*np.exp(-np.arange(tail)/max(Rr,1)*4)
    return e
def lp(x,cut):  # one-pole lowpass
    a=np.exp(-2*np.pi*cut/SR); y=np.zeros_like(x); z=0.0
    for i in range(len(x)): z=a*z+(1-a)*x[i]; y[i]=z
    return y
def hp(x,cut): return x-lp(x,cut)
rng=np.random.default_rng(7)
def kick(len_=0.5):
    n=int(len_*SR); tt=np.arange(n)/SR
    f=45+160*np.exp(-tt*28); ph=np.cumsum(2*np.pi*f/SR)
    return np.tanh(np.sin(ph)*2.2)*np.exp(-tt*7)*(1+np.exp(-tt*120)*0.6)
def hat(len_=0.08,open_=False):
    n=int(len_*SR); x=hp(rng.standard_normal(n),7000); return x*np.exp(-np.arange(n)/SR*(18 if open_ else 70))*0.5
def clap():
    n=int(0.25*SR); x=hp(rng.standard_normal(n),1200); e=np.zeros(n)
    for k,o in enumerate([0,0.012,0.024,0.036]): i=int(o*SR); e[i:]+=np.exp(-np.arange(n-i)/SR*(60 if k<3 else 14))
    return x*e*0.35
def bass(freq,len_):
    n=int(len_*SR); tt=np.arange(n)/SR
    saw=2*((tt*freq)%1)-1; sub=np.sin(2*np.pi*freq*tt)
    return (lp(saw,900)*0.6+sub*0.6)*env(n,0.004,0.08,0.7,0.06,max(len_-0.14,0))
def pad(freqs,len_,cut=1800):
    n=int(len_*SR); tt=np.arange(n)/SR; x=np.zeros(n)
    for f in freqs:
        for det in (-0.4,0.4,0): x+=2*((tt*(f*(1+det/100)))%1)-1
    return lp(x/len(freqs)/3,cut)*env(n,0.6,0.5,0.8,1.2,max(len_-2.3,0))
def pluck(freq,len_=0.35):
    n=int(len_*SR); tt=np.arange(n)/SR
    return (np.sin(2*np.pi*freq*tt)+0.3*np.sin(2*np.pi*freq*2*tt))*np.exp(-tt*14)*0.5
def whoosh(len_=0.8,rise=True):
    n=int(len_*SR); x=rng.standard_normal(n); y=np.zeros(n); z=0; tt=np.arange(n)/SR
    for i in range(n):
        c=(300+5000*(tt[i]/len_)**2) if rise else (5000*np.exp(-tt[i]*6)+300)
        a=np.exp(-2*np.pi*c/SR); z=a*z+(1-a)*x[i]; y[i]=z
    e=np.sin(np.pi*np.minimum(tt/len_,1))**(1 if rise else 0.4)
    return hp(y,200)*e*0.9
def impact():
    n=int(1.6*SR); tt=np.arange(n)/SR
    boom=np.sin(2*np.pi*(38+40*np.exp(-tt*12))*tt)*np.exp(-tt*3)
    crack=hp(rng.standard_normal(n),2500)*np.exp(-tt*25)*0.5
    return np.tanh((boom+crack)*1.8)*0.9
def click():
    n=int(0.03*SR); return hp(rng.standard_normal(n),3000)*np.exp(-np.arange(n)/SR*300)*0.6
def ding():
    n=int(1.2*SR); tt=np.arange(n)/SR
    return (np.sin(2*np.pi*1318*tt)*np.exp(-tt*5)+np.sin(2*np.pi*1760*tt)*np.exp(-tt*4)*0.7+np.sin(2*np.pi*2637*tt)*np.exp(-tt*7)*0.3)*0.25
def riser(len_):
    n=int(len_*SR); tt=np.arange(n)/SR
    f=110*2**(tt/len_*2); ph=np.cumsum(2*np.pi*f/SR)
    return lp(np.sign(np.sin(ph))*0.3*(tt/len_)**2,3000)+whoosh(len_,True)*0.8

# ---- arrangement (chords: Am - F - C - G, 1 bar each) ----
CH=[(220,261.6,329.6),(174.6,220,261.6),(130.8*2,164.8*2,196*2),(196,246.9,293.7)]
BASSN=[55,43.65,65.4,49]
# intro pad 0-11 (low filter opening), main pad 11-31.5, outro pad 34-38
for bar in range(0,19):
    b0=bar*4*BEAT
    if b0>=31.5 and b0<34: continue
    cut=600+1400*min(1,b0/11)
    gain=0.22 if b0<11 else 0.18
    if b0>=34: gain=0.2; cut=1600
    add(pad(CH[bar%4],4*BEAT+0.2,cut),b0,gain)
# intro: soft kick on 1, hats on 8ths from bar 2
for bar in range(0,4):
    b0=bar*4*BEAT; add(lp(kick(),400),b0,0.45)
    if bar>=1:
        for e in range(8): add(hat(0.05),b0+e*BEAT/2,0.12 if e%2 else 0.2)
# scene transition whooshes
for ts in (2.2,4.5,7.1): add(whoosh(0.5,True),ts-0.4,0.5)
add(impact(),6.4,0.8)                       # "ugh."
add(riser(1.9),7.1,0.8)                     # build to 9
add(impact(),9.0,1.0); add(whoosh(0.5,False),9.0,0.6)   # drop / "Let's fix that"
# drop groove 9 -> 31.5 ; breakdown 31.5-34 ; final hit 34
for b in range(int(9/BEAT),int(31.5/BEAT)):
    ts=b*BEAT; add(kick(),ts,0.9)
    if b%2==1: add(clap(),ts,0.55)
    for h in range(2): add(hat(0.06,False),ts+h*BEAT/2,0.22 if h else 0.16)
    if b%4==3: add(hat(0.25,True),ts+BEAT/2,0.18)
    bar=(b//4)%4; root=BASSN[bar]
    for k,(off,ln) in enumerate([(0,0.22),(0.25,0.2),(0.5,0.22),(0.75,0.2)]):
        f=root*(2 if k==3 else 1); add(bass(f,ln),ts+off*BEAT,0.5 if k%2==0 else 0.35)
    if b%8 in (0,3,6): add(pluck(CH[bar][b%3]*2,0.4),ts,0.35,pan=0.3*(1 if b%2 else -1))
add(impact(),11.0,0.9)                      # brand reveal "Meet"
for ts in (13.0,15.0): add(whoosh(0.45,True),ts-0.35,0.5)
# demo foley
for i in range(45): add(click(),16.2+i*(1.8/45)+rng.uniform(-0.004,0.004),0.5,pan=rng.uniform(-0.3,0.3))  # typing
add(click(),18.5,1.2); add(pluck(880,0.3),18.52,0.45)      # Download click
add(pluck(660,0.3),18.7,0.35)                               # item appears
add(pluck(660,0.3),21.2,0.35)
add(ding(),23.1,1.0)                                        # complete
add(pluck(523,0.5),23.4,0.3)                                # toast
add(whoosh(0.4,True),25.7,0.4); add(pluck(784,0.3),26.0,0.4) # settings pop
for ts in (26.7,26.95,27.2,27.45): add(click(),ts,0.9); add(pluck(1046,0.2),ts,0.25)
for ts in (27.7,28.0,28.3): add(click(),ts,0.7)
add(click(),29.5,1.1); add(whoosh(0.35,True),29.3,0.4)      # history tab
for i in range(3): add(pluck(880+i*110,0.25),29.6+i*0.12,0.25)
add(whoosh(0.6,False),31.5,0.6)                             # breakdown
add(pluck(440,0.6),31.55,0.4); add(pluck(554,0.6),32.3,0.4)
add(riser(2.0),32.0,0.7)
add(impact(),34.0,1.0); add(ding(),34.3,0.6)                # outro hit
for b in range(int(34/BEAT),int(37/BEAT)):
    ts=b*BEAT; add(lp(kick(),500),ts,0.5)
# master: fade out, soft clip, normalize
fade=np.ones(N); fo=int(1.2*SR); fade[-fo:]=np.linspace(1,0,fo); fi=int(0.3*SR); fade[:fi]=np.linspace(0,1,fi)
mix=np.stack([L,R],1)*fade[:,None]
mix=np.tanh(mix*1.3)/np.tanh(1.3); mix*=0.95/np.max(np.abs(mix))
out=sys.argv[1] if len(sys.argv)>1 else 'track.wav'
with wave.open(out,'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype('<i2').tobytes())
print('wrote',out)
