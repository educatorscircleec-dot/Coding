"""Synthesise a sound-effects-only track (no music) timed to the 30s EduCrew ad,
then mux it onto the video WITHOUT re-encoding the picture (-c:v copy).

Usage: python3 sfx.py in.mp4 out.mp4
"""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
DUR = 30.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
L = np.zeros(N)
R = np.zeros(N)


def env(n, a, d, curve=4.0):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-np.maximum(t - a, 0) * curve / max(d, 1e-4))
    return e


def lp(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    s = 0.0
    for i, v in enumerate(x):
        s = (1 - a) * v + a * s
        y[i] = s
    return y


def bp(x, lo, hi):
    return lp(x, hi) - lp(x, lo)


def place(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    j = min(N, i + len(sig))
    if j <= i:
        return
    gl, gr = gain * np.sqrt((1 - pan) / 2), gain * np.sqrt((1 + pan) / 2)
    L[i:j] += sig[: j - i] * gl
    R[i:j] += sig[: j - i] * gr


def panned_place(sig, t, gain, pan_from, pan_to):
    i = int(t * SR)
    j = min(N, i + len(sig))
    p = np.linspace(pan_from, pan_to, j - i)
    L[i:j] += sig[: j - i] * gain * np.sqrt((1 - p) / 2)
    R[i:j] += sig[: j - i] * gain * np.sqrt((1 + p) / 2)


# ---------------- sound designs ----------------
def whoosh(dur=0.9, lo=300, hi=2600):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    t = np.linspace(0, 1, n)
    # sweep band upward then back: filter by blending two bands
    a = bp(x, lo, hi * 0.5)
    b = bp(x, lo * 2, hi)
    sweep = np.sin(np.pi * t)
    y = a * (1 - sweep) + b * sweep
    e = np.sin(np.pi * t) ** 2
    return y * e / (np.abs(y).max() + 1e-9)


def tap(freq=900, dur=0.12, noise=0.6):
    """small wooden/plastic object set down on a desk"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * freq * t) * env(n, 0.001, 0.05, 6) + 0.5 * np.sin(2 * np.pi * freq * 2.7 * t) * env(n, 0.001, 0.02, 6)
    click = bp(rng.standard_normal(n), 1500, 7000) * env(n, 0.0005, 0.01, 6) * noise
    y = body + click
    return y / np.abs(y).max()


def key_burst(dur, rate=9.0):
    """soft laptop typing"""
    n = int(dur * SR)
    y = np.zeros(n)
    t = 0.0
    while t < dur - 0.06:
        k = tap(rng.uniform(1800, 2600), 0.05, 1.2) * rng.uniform(0.5, 1.0)
        i = int(t * SR)
        y[i : i + len(k)] += k[: n - i]
        t += rng.exponential(1 / rate) + 0.04
    return y / (np.abs(y).max() + 1e-9)


def paper(dur=0.5, bright=5000):
    """paper slide / page turn rustle"""
    n = int(dur * SR)
    x = bp(rng.standard_normal(n), 800, bright)
    crackle = (rng.random(n) < 0.004) * rng.standard_normal(n) * 3
    x = x + bp(crackle, 1500, 8000)
    t = np.linspace(0, 1, n)
    e = np.sin(np.pi * t) ** 0.8 * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t) ** 2)
    y = x * e
    return y / np.abs(y).max()


def marker(dur=0.35):
    """marker stroke on whiteboard"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 1400 + 300 * np.sin(2 * np.pi * 3 * t)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    y = (bp(rng.standard_normal(n), 2000, 6000) + tone) * np.sin(np.pi * np.linspace(0, 1, n)) ** 0.6
    return y / np.abs(y).max()


def clack(n_hits=3):
    """number tiles / dice clacking"""
    out = np.zeros(int(0.6 * SR))
    t = 0
    for _ in range(n_hits):
        k = tap(rng.uniform(2200, 3400), 0.08, 1.0) * rng.uniform(0.6, 1.0)
        i = int(t * SR)
        out[i : i + len(k)] += k
        t += rng.uniform(0.07, 0.16)
    return out / np.abs(out).max()


def glass(freq=2100, dur=1.4):
    """glass beaker clink"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    partials = [(1, 1), (2.32, 0.5), (4.25, 0.3), (6.1, 0.15)]
    y = sum(a * np.sin(2 * np.pi * freq * m * t) * env(n, 0.001, dur / (1 + m), 3) for m, a in partials)
    y += bp(rng.standard_normal(n), 3000, 9000) * env(n, 0.0005, 0.01, 6) * 0.5
    return y / np.abs(y).max()


def pen_tick():
    """pen ticking a checklist"""
    n = int(0.18 * SR)
    t = np.linspace(0, 1, n)
    y = bp(rng.standard_normal(n), 1500, 6000) * (np.sin(np.pi * t) ** 2)
    return y / np.abs(y).max()


def soft_pop():
    """caption appearing: subtle UI pop"""
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    f = 520 + 380 * np.exp(-t * 40)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 0.08, 5)
    return y / np.abs(y).max()


def riser(dur=1.4):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    x = rng.standard_normal(n)
    y = bp(x, 400, 1200) * (1 - t) + bp(x, 1500, 7000) * t
    return y * t ** 2 / np.abs(y).max()


def shimmer(dur=2.6, base=880):
    """logo reveal sparkle (single non-melodic sound effect)"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for k in range(28):
        st = rng.uniform(0, 0.9)
        f = base * rng.uniform(2.0, 6.0)
        i = int(st * SR)
        m = n - i
        y[i:] += np.sin(2 * np.pi * f * t[:m]) * env(m, 0.002, rng.uniform(0.3, 0.9), 4) * rng.uniform(0.2, 0.6)
    # soft low impact underneath
    y += np.sin(2 * np.pi * 70 * t) * env(n, 0.01, 0.6, 4) * 1.2
    return y / np.abs(y).max()


def murmur(dur):
    """distant room / studio ambience"""
    n = int(dur * SR)
    x = lp(rng.standard_normal(n), 500) + 0.3 * bp(rng.standard_normal(n), 300, 2500)
    mod = 0.8 + 0.2 * np.sin(2 * np.pi * 0.17 * np.arange(n) / SR)
    return x * mod / np.abs(x).max()


# ---------------- timeline (matches render.py) ----------------
# continuous studio room tone 0-25.8s, fading under the end card
amb = murmur(26.5)
fade = np.ones(len(amb))
fade[: int(0.6 * SR)] = np.linspace(0, 1, int(0.6 * SR))
fade[-int(1.5 * SR):] = np.linspace(1, 0, int(1.5 * SR))
L[: len(amb)] += amb * fade * 0.045
R[: len(amb)] += np.roll(amb, 900) * fade * 0.045

# caption pops (captions fade in at +0.45s of each scene)
for s in range(5):
    place(soft_pop(), s * 5 + 0.5, 0.18)

# scene transitions: whooshes following camera direction
panned_place(whoosh(1.0), 4.55, 0.32, -0.6, 0.6)   # 1->2 (L->R)
panned_place(whoosh(1.0), 9.55, 0.32, -0.6, 0.6)   # 2->3 (L->R)
panned_place(whoosh(1.0), 14.55, 0.30, 0.0, 0.0)   # 3->4 (zoom)
panned_place(whoosh(1.0), 19.55, 0.32, 0.6, -0.6)  # 4->5 (R->L)

# Clip 1: workspace - camera zoom-in swish, sign placed on desk, laptop typing, paper
panned_place(whoosh(1.6, 200, 1400), 0.0, 0.14, 0.0, 0.0)
place(tap(420, 0.25, 0.8), 1.05, 0.45)            # tiny sign set on desk
place(tap(650, 0.15, 0.6), 1.12, 0.18)
place(key_burst(1.4), 2.0, 0.12, 0.2)
panned_place(whoosh(1.6, 200, 1500), 2.0, 0.10, -0.5, 0.5)  # glide L->R
place(paper(0.45), 3.6, 0.14, -0.3)

# Clip 2: maths - marker on whiteboard, tiles clack, ruler tap
place(marker(0.35), 5.9, 0.16, -0.2)
place(marker(0.25), 6.35, 0.13, -0.2)
place(clack(4), 7.3, 0.30, 0.3)
place(tap(1300, 0.12), 8.4, 0.22, 0.1)
place(paper(0.35, 6000), 8.9, 0.11)

# Clip 3: ELA library -> science
place(paper(0.7, 7000), 10.8, 0.18, -0.4)          # page turn
place(paper(0.25, 5000), 11.6, 0.10, -0.3)         # vocab card
place(glass(2300), 12.8, 0.16, 0.35)               # beaker clink
place(glass(3100, 1.0), 13.05, 0.08, 0.4)
place(tap(500, 0.2), 13.9, 0.12, 0.2)              # globe nudge

# Clip 4: curriculum office - typing, hand slides assessment sheet, push-in/pull-back
place(key_burst(1.6, 11), 15.6, 0.12, -0.3)
panned_place(whoosh(1.4, 200, 1200), 15.8, 0.10, 0.0, 0.0)
place(paper(0.8, 4500), 17.0, 0.26, 0.4)           # sheet slid into place
place(tap(700, 0.15, 0.5), 17.75, 0.15, 0.4)
place(pen_tick(), 18.6, 0.12, -0.2)
place(pen_tick(), 18.85, 0.10, -0.2)

# Clip 5: digital studio - typing, checklist ticks, laptop close, zoom-out
place(key_burst(1.2, 10), 20.8, 0.10, 0.4)
place(pen_tick(), 22.0, 0.14, -0.3)
place(pen_tick(), 22.3, 0.12, -0.3)
place(pen_tick(), 22.6, 0.12, -0.3)
place(tap(950, 0.12), 23.2, 0.12, 0.2)
panned_place(whoosh(1.8, 200, 1300), 22.8, 0.12, 0.3, -0.3)

# End card: dissolve whoosh, logo reveal shimmer, details settle
panned_place(whoosh(1.4, 250, 1800), 24.8, 0.24, 0.0, 0.0)
place(riser(0.9), 25.2, 0.10)
place(shimmer(2.8), 25.95, 0.30)
place(soft_pop(), 27.05, 0.16)
place(tap(300, 0.4, 0.2), 27.1, 0.10)

# ---------------- master ----------------
mix = np.stack([L, R], 1)
# gentle soft-clip limiter and normalise to about -1 dBFS peak
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix *= 0.89 / np.abs(mix).max()
fo = int(0.4 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]


def main(src, out):
    wav = Path(out).with_suffix(".sfx.wav")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out],
        check=True,
    )


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
