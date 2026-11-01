"""Synthesizes soundtrack.wav (45s) synced to promo.html cue times. Needs numpy."""
import numpy as np, wave
SR, DUR = 48000, 45.0
N = int(SR * DUR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(7)

def add(sig, t, pan=0.0, g=1.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if i >= N: return
    s = sig[: j - i] * g
    L[i:j] += s * (1 - pan) ** .5 * .7071 * 1.414 / 1.414
    R[i:j] += s * (1 + pan) ** .5 * .7071 * 1.414 / 1.414

def env(n, a=.005, d=.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)

def lp(x, cut):
    a = np.exp(-2 * np.pi * cut / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y

def lp_fast(x, cut):  # vectorized-ish one-pole via scipy-free cumulative trick (chunked)
    from numpy.lib.stride_tricks import sliding_window_view
    k = int(SR / cut / 2) | 1
    return np.convolve(x, np.ones(k) / k, 'same')

def note(f): return 440 * 2 ** ((f - 69) / 12)

# ---- SFX ----
def pop(f=900, d=.09):
    n = int(SR * d); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t * (1 - t * 2.5)) * env(n, .002, d / 4)

def whoosh(d=.6, up=True):
    n = int(SR * d); x = rng.standard_normal(n)
    x = lp_fast(x, 2500) - lp_fast(x, 300)
    t = np.linspace(0, 1, n); shape = np.sin(np.pi * t ** (.6 if up else 1.4)) ** 2
    return x * shape * 2.2

def click(): return pop(2600, .03) * .6 + whoosh(.03) * .4

def tick():
    n = int(SR * .018); x = rng.standard_normal(n) * env(n, .0005, .004)
    return x - lp_fast(x, 1500)

def impact(d=1.2):
    n = int(SR * d); t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * (45 + 80 * np.exp(-t * 18)) * t) * np.exp(-t * 3.5)
    nz = lp_fast(rng.standard_normal(n), 1200) * np.exp(-t * 9) * 1.5
    return sub + nz

def chime(base=76):
    d = 2.0; n = int(SR * d); t = np.arange(n) / SR; s = np.zeros(n)
    for k, (m, dl) in enumerate([(base, 0), (base + 7, .09), (base + 12, .18)]):
        o = int(dl * SR); f = note(m)
        s[o:] += (np.sin(2 * np.pi * f * t[: n - o]) + .3 * np.sin(2 * np.pi * f * 2.01 * t[: n - o])) * np.exp(-t[: n - o] * 3)
    return s * .35

def riser(d=1.0):
    n = int(SR * d); t = np.linspace(0, 1, n)
    x = rng.standard_normal(n); x = x - lp_fast(x, 600)
    return x * t ** 2.5 * .8 + np.sin(2 * np.pi * (200 + 900 * t ** 2) * np.arange(n) / SR) * t ** 3 * .15

# ---- music: warm pad + soft beat ----
BPM = 100; beat = 60 / BPM
chords = [[53, 57, 60, 64], [57, 60, 64, 67], [50, 57, 60, 65], [46, 53, 57, 62]]  # Fmaj7 Am7 Dm9-ish Bbmaj7
bar = beat * 4
t_all = np.arange(N) / SR
pad = np.zeros(N)
for bi in range(int(DUR / bar) + 1):
    ch = chords[bi % 4]; t0 = bi * bar
    i0 = int(t0 * SR); i1 = min(N, int((t0 + bar + .4) * SR))
    if i0 >= N: break
    tt = np.arange(i1 - i0) / SR
    seg = np.zeros(i1 - i0)
    for m in ch:
        for det in (-.12, .12):
            f = note(m + det / 1.0)
            seg += np.sin(2 * np.pi * f * tt) + .25 * np.sin(2 * np.pi * f * 2 * tt + .3)
    e = np.minimum(1, tt / .5) * np.minimum(1, (bar + .4 - tt) / .5)
    pad[i0:i1] += seg * e * .03
# bass on chord roots
bass = np.zeros(N)
for bi in range(int(DUR / bar) + 1):
    r = chords[bi % 4][0] - 12; t0 = bi * bar
    for k in (0, 2.5, 3):
        i0 = int((t0 + k * beat) * SR); n = int(beat * .9 * SR)
        if i0 + n >= N: continue
        tt = np.arange(n) / SR
        bass[i0:i0 + n] += np.sin(2 * np.pi * note(r) * tt) * env(n, .01, .35) * .22
# drums: start at 9.6 (dark scene), full at 12.0
kick = lambda: impact(.35) * .5
hat = lambda: tick() * .5
drum_on = lambda t: (9.6 <= t < 13.4) or (19.2 <= t < 29.5) or (33.0 <= t < 40.4)
k = 0.0
while k < DUR:
    if drum_on(k):
        add(kick(), k, 0, .9)
        add(hat(), k + beat / 2, .3, .5)
        if (k / beat) % 2 >= 1: add(pop(180, .12) * .4, k, -.1, .6); add(whoosh(.08) * .2, k, -.1, .6)  # snare-ish
    k += beat
music_gain = np.ones(N)
for a, b in [(0, 2.5)]:
    pass
L += pad + bass; R += pad + bass

# ---- cues (match promo.html timings) ----
for i, t in enumerate([.25, .36, .47, .58, 1.62, 1.74, 1.86]): add(pop(700 + i * 60), t, (i % 3 - 1) * .3, .35)
add(whoosh(.7), 2.6, 0, .6)
add(impact(.8), 3.15, 0, .5)
for i in range(18): add(pop(1300 + (i % 4) * 120, .05), 3.7 + i * .15, .2, .18)  # badge counts
add(whoosh(.5), 4.45, .4, .5)
add(whoosh(.7, False), 6.75, .5, .6)
add(pop(500, .15), 7.35, 0, .5)
add(whoosh(.25), 8.1, -.2, .5)   # strike
for i in range(5): add(pop(1000 + i * 150, .08), 8.75 + i * .085, (i % 2) * .6 - .3, .4)
add(whoosh(.5), 9.3, 0, .6)
for i in range(5): add(pop(800, .07), 9.95 + i * .12, 0, .25)
add(whoosh(.3), 10.95, .2, .4)
add(impact(1.2), 12.0, 0, .8)
add(riser(.5), 13.0, 0, .5)
add(riser(.9), 13.55, 0, .35)
add(impact(1.0), 14.4, 0, .5)
for i in range(10): add(tick() * 2, 15.12 + i * .045, .1, .5)
add(impact(.6), 16.4, 0, .4)
add(whoosh(.8), 16.95, -.5, .7)
add(impact(.8), 17.4, 0, .5)
add(whoosh(.5), 19.1, 0, .5)
for i in range(31): add(tick() * 2.5, 20.25 + i * .029, -.1, .6)  # typing URL
add(click(), 21.86, .3, 1.0)
add(pop(900), 22.0, 0, .3); add(pop(1100), 23.45, 0, .3)
add(pop(600), 22.55, .4, .4); add(pop(700), 23.05, .4, .4)
add(chime(79), 25.0, .3, .7)
add(whoosh(.5), 25.85, 0, .5)
add(whoosh(.5), 26.35, .5, .4)
for t in (26.6, 27.25, 27.9, 28.55): add(whoosh(.25), t - .05, -.3, .5); add(pop(1200, .05), t + .1, 0, .25)
add(click(), 28.85, .3, .7); add(click(), 29.0, .3, .7)
add(riser(.8), 29.3, 0, .4)
add(impact(1.0), 30.0, 0, .6)
add(chime(76), 30.8, 0, 1.0)
add(whoosh(.6), 32.5, 0, .7)
add(impact(.8), 33.0, 0, .5)
for i in range(0, 170, 2): add(tick() * 2, 33.55 + i * .01, .1, .4)  # terminal typing
add(whoosh(.5), 36.2, 0, .5)
add(click(), 36.97, 0, 1.0)
add(whoosh(.5), 37.15, 0, .5)
for i in range(22): add(pop(900 + i * 40, .04), 37.6 + .9 * (1 - (1 - i / 22) ** 3), 0, .2)
add(pop(1500, .1), 38.45, 0, .4)
for t in (38.9, 39.35, 39.85): add(impact(.6), t, 0, .55); add(whoosh(.4), t - .25, .2, .3)
add(riser(.6), 39.85, 0, .4)
add(whoosh(.7), 40.35, 0, .7)
add(impact(1.6), 40.95, 0, .8)
for i in range(10): add(tick() * 2, 42.35 + i * .045, .1, .5)
add(chime(72), 42.4, 0, .6)
for i in range(30): add(tick() * 1.6, 43.0 + i * .023, -.1, .4)

for t in (19.03, 26.13, 37.28): add(whoosh(.45), t, 0, .9)
add(whoosh(.35), 21.95, .2, .6)

# master: soft clip + fades
m = np.stack([L, R], 1)
fade = np.ones(N); fade[: int(.3 * SR)] = np.linspace(0, 1, int(.3 * SR)); fade[-int(1.2 * SR):] = np.linspace(1, 0, int(1.2 * SR))
m *= fade[:, None]
m = np.tanh(m * 1.4) / np.tanh(1.4)
m /= np.max(np.abs(m)) / .89
with wave.open('soundtrack.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((m * 32767).astype('<i2').tobytes())
print('wrote soundtrack.wav')
