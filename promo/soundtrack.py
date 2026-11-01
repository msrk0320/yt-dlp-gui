"""Synthesizes soundtrack.wav (45 s) for promo.html: sleek, minimal, in D major.

Electric piano + warm pad + soft pluck arpeggio + sub, a light pulse in the middle,
and a few quiet UI/air effects, all through one convolution reverb.
Bars are aligned so the logo reveal (13.45 s) and the end card (40.95 s) land on downbeats.
Needs numpy only.  Run: python3 soundtrack.py
"""
import numpy as np, wave

SR, DUR = 48000, 45.0
N = int(SR * DUR)
rng = np.random.default_rng(3)
BAR = 2.75                      # 87.27 bpm
BEAT = BAR / 4
ORIGIN = -0.3                   # bar k starts at ORIGIN + k*BAR (bar 5 = 13.45, bar 15 = 40.95)
bar_t = lambda k: ORIGIN + k * BAR
hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)

dry = np.zeros((N, 2)); send = np.zeros((N, 2))   # send = reverb bus

def place(sig, t, pan=0.0, gain=1.0, verb=0.3):
    i = int(round(t * SR))
    if i >= N or i + len(sig) <= 0: return
    a, b = max(0, -i), min(len(sig), N - i)
    s = sig[a:b] * gain
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    st = np.stack([s * l, s * r], 1) * 1.414
    dry[i + a:i + b] += st
    send[i + a:i + b] += st * verb

def tt(d): return np.arange(int(d * SR)) / SR

def fade_out(x, d=.08):
    n = min(len(x), int(d * SR)); x[-n:] *= np.linspace(1, 0, n) ** 2; return x

def spectral(x, lo=20, hi=20000):          # brick-ish band filter via FFT with soft edges
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, len(x))

# ---------------- instruments ----------------
def epiano(m, d=2.6, vel=.7):
    f, t = hz(m), tt(d)
    idx = (.6 + vel * 1.1) * np.exp(-t / .45)
    tone = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
    tine = .06 * vel * np.sin(2 * np.pi * f * 7.02 * t) * np.exp(-t / .03)
    amp = np.minimum(1, t / .004) * np.exp(-t / (2.0 if f < 330 else 1.3))
    trem = 1 + .06 * np.sin(2 * np.pi * 4.2 * t)
    return fade_out((tone + tine) * amp * trem * vel)

def bell(m, d=3.5, vel=.6):
    f, t = hz(m), tt(d)
    idx = 1.6 * np.exp(-t / .7)
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 3.5 * t))
    s += .25 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / .5)
    return fade_out(s * np.minimum(1, t / .003) * np.exp(-t / 1.6) * vel)

def pluck(m, d=.9, vel=.5):
    f, t = hz(m), tt(d)
    idx = 1.3 * np.exp(-t / .07)
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 2 * t))
    return fade_out(s * np.minimum(1, t / .002) * np.exp(-t / .32) * vel)

def pad(notes, d, bright=1.0, att=1.4, rel=1.2):
    t = tt(d); s = np.zeros(len(t))
    for m in notes:
        for c in (-6, 0, 6):                      # gentle chorus
            f = hz(m) * 2 ** (c / 1200)
            ph = rng.uniform(0, 6.28)
            s += np.sin(2 * np.pi * f * t + ph) + .28 * bright * np.sin(4 * np.pi * f * t + ph) + .1 * bright ** 2 * np.sin(6 * np.pi * f * t)
    env = np.minimum(1, t / att) * np.minimum(1, np.maximum(0, (d - t) / rel))
    return s * env / (3 * len(notes))

def sub(m, d):
    t = tt(d); f = hz(m)
    s = np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t)
    return s * np.minimum(1, t / .03) * (.45 + .55 * np.exp(-t / .9)) * np.minimum(1, np.maximum(0, (d - t) / .3))

def kick():
    t = tt(.45)
    f = 46 + 70 * np.exp(-t * 32)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5) * np.minimum(1, t / .003)

def shaker():
    x = spectral(rng.standard_normal(int(.06 * SR)), 6000, 16000)
    t = tt(.06); return x * np.minimum(1, t / .006) * np.exp(-t / .018)

def air(d=.7, lo=500, hi=6000):
    x = spectral(rng.standard_normal(int(d * SR)), lo, hi)
    u = np.linspace(0, 1, len(x)); return x * np.sin(np.pi * u ** .7) ** 3

def click():
    t = tt(.05)
    return (np.sin(2 * np.pi * 1700 * t) * np.exp(-t / .006) + .4 * np.sin(2 * np.pi * 3400 * t) * np.exp(-t / .003))

def tick():
    x = spectral(rng.standard_normal(int(.02 * SR)), 2500, 9000)
    t = tt(.02); return x * np.exp(-t / .003)

def thump():
    t = tt(1.2)
    f = 38 + 30 * np.exp(-t * 12)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3) * np.minimum(1, t / .01)

def reverse_swell(notes, d=2.2):
    s = sum(epiano(m, d, .55) for m in notes) / len(notes)
    s = s[::-1].copy(); u = np.linspace(0, 1, len(s)); return s * u ** 1.5

# ---------------- harmony ----------------
V = {
    'D':  (38, [54, 57, 61, 64]),   # Dmaj9
    'Bm': (47, [57, 61, 62, 66]),   # Bm9
    'G':  (43, [59, 62, 66, 69]),   # Gmaj9
    'A':  (45, [57, 59, 64, 69]),   # Asus2
    'Em': (40, [55, 59, 62, 66]),   # Em9
}
BARS = ['G', 'Bm', 'Em', 'A', 'G',            # 0-4  intro / dark build (to 13.45)
        'D', 'Bm', 'G', 'A', 'D', 'Bm', 'G', 'A', 'Em', 'A',   # 5-14 groove
        'D']                                  # 15   end card (40.95)
DARK = lambda t: (9.42 <= t < 13.45) or (32.5 <= t < 40.4)

for k, name in enumerate(BARS):
    t0 = bar_t(k); b, notes = V[name]
    last = k == len(BARS) - 1
    d = (DUR - t0) if last else BAR + 1.2
    bright = .35 if DARK(t0 + .1) else 1.0
    if k == 4: bright = .2
    place(pad(notes, d, bright, att=1.6 if k else 2.5), max(t0, 0) if k else 0, 0, .2 if k < 5 else .17, .55)
    if k >= 5 or k == 0:
        place(sub(b, (DUR - t0) if last else BAR), t0, 0, .11 if k >= 5 else .08, 0)
    # electric piano voicing (rolled), skipped in the dark build
    if not (3 < k < 5):
        for j, m in enumerate(notes):
            place(epiano(m, 3.4 if last else 2.6, .55 if k < 5 else .5), t0 + j * .018 + (0 if k else .25), -.35 + j * .23, .16, .35)
        if k >= 5 and not last:                 # soft re-strike on beat 3
            for j, m in enumerate(notes[1:]):
                place(epiano(m + 12 if j == 2 else m, 1.6, .32), t0 + 2 * BEAT + j * .015, .3 - j * .3, .11, .4)

# end card: bloom + bell
for j, m in enumerate([74, 81, 86]): place(bell(m, 4.0, .5), 40.95 + j * .11, -.3 + j * .3, .13, .7)

# arpeggio (pluck) from bar 6, eighth notes
PAT = [0, 2, 1, 3, 2, 4, 3, 1]
for k in range(6, 15):
    _, notes = V[BARS[k]]
    tones = notes + [n + 12 for n in notes]
    for e in range(8):
        t = bar_t(k) + e * BEAT / 2
        dk = DARK(t)
        if 32.5 <= t < 35.45 and e % 2: continue      # thinner in the breakdown
        vel = (.5 if e % 2 == 0 else .36) * (.7 if dk else 1)
        place(pluck(tones[PAT[e]] + 12, .9, vel), t, .45 if e % 2 else -.45, .12, .45)

# pulse: kick on 1 & 3, shaker 16ths (bars 7-11, 13-14)
for k in list(range(7, 12)) + [13, 14]:
    for b in range(4):
        tb = bar_t(k) + b * BEAT
        if b in (0, 2): place(kick(), tb, 0, .2, .04)
        for s in range(4):
            if k < 8: continue
            g = .05 if s == 2 else .025
            place(shaker(), tb + s * BEAT / 4 + (.012 if s % 2 else 0), .25, g, .2)

# dark build: reverse swells, low thump
place(reverse_swell(V['D'][1], 2.4), 13.45 - 2.4, 0, .5, .5)
place(reverse_swell([62, 66, 69, 74], 1.6), 40.95 - 1.6, 0, .45, .5)
place(thump(), 12.05, 0, .3, .15)
place(thump(), 33.05, 0, .2, .15)

# ---------------- quiet sound design ----------------
for t, p in [(2.6, 0), (6.75, .5), (9.3, 0), (16.95, -.6), (19.03, 0), (26.13, .6), (32.45, 0), (37.28, 0), (40.35, 0)]:
    place(air(.6), t, p, .055, .5)
place(air(.35, 800, 7000), 21.95, .2, .04, .4)                 # zoom-out on click
for t in (21.86, 28.85, 29.0, 36.97): place(click(), t, .15, .09, .15)
for i in range(31): place(tick(), 20.25 + i * .029 + rng.uniform(-.006, .006), -.1, .018, .1)
for i in range(0, 170, 3): place(tick(), 33.55 + i * .01, .1, .014, .1)
for i in range(30): place(tick(), 43.0 + i * .023, 0, .012, .1)
place(bell(81, 2.5, .45), 25.0, .3, .12, .6)                   # "Done."
place(bell(86, 3.0, .5), 30.8, 0, .12, .7)                    # notification chime
place(bell(81, 3.0, .45), 30.95, 0, .1, .7)
for t, m in [(38.9, 74), (39.35, 76), (39.85, 78)]:            # Free. Open source. No ads.
    place(epiano(m, 1.8, .5), t, 0, .12, .5)
place(bell(86, 2.5, .3), 14.4, 0, .07, .7)                    # logo lands
place(bell(81, 2.0, .25), 17.35, .2, .05, .7)                 # "Any site."

# ---------------- reverb (FFT convolution, stereo decorrelated IR) ----------------
def make_ir(d=3.0, rt=2.6, pre=.022):
    t = tt(d); out = []
    for ch in range(2):
        n = rng.standard_normal(len(t))
        early = spectral(n, 200, 9000) * np.exp(-t * 6.9 / .6)
        late = spectral(rng.standard_normal(len(t)), 150, 3500) * np.exp(-t * 6.9 / rt)
        ir = (early * .5 + late) * np.minimum(1, t / .015)
        ir = np.concatenate([np.zeros(int(pre * SR)), ir]); out.append(ir / np.sqrt(np.sum(ir ** 2)))
    return out
ir = make_ir()
nfft = 1 << int(np.ceil(np.log2(N + len(ir[0]))))
wet = np.zeros((N, 2))
for ch in range(2):
    wet[:, ch] = np.fft.irfft(np.fft.rfft(send[:, ch], nfft) * np.fft.rfft(ir[ch], nfft), nfft)[:N]
mix = dry + wet * .55

# ---------------- master ----------------
mix[:, 0] = spectral(mix[:, 0], 28, 15000); mix[:, 1] = spectral(mix[:, 1], 28, 15000)
fade = np.ones(N); fi, fo = int(.4 * SR), int(2.0 * SR)
fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
mix *= fade[:, None]
mix /= np.max(np.abs(mix))
mix = np.tanh(mix * 1.15) / np.tanh(1.15)          # gentle glue
mix *= .89 / np.max(np.abs(mix))
with wave.open('soundtrack.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote soundtrack.wav')
