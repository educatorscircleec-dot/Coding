"""Synthesises an original, royalty-free 30s background track for the ad.

Premium, upbeat 120 BPM marimba / glockenspiel / soft-pad bed with light
percussion. One chord per 5s scene, a soft intro (no drums) for scene 1,
whooshes into every cut (and the 12.5s library -> science move), and a warm
resolve + logo hit at 25s for the brand reveal.
Usage: python3 music.py [out.wav]
"""
import sys
import wave
import numpy as np

SR = 48000
DUR = 30.0
BPM = 120
BEAT = 60 / BPM
SCENE = 5.0
N = int(SR * DUR)
L = np.zeros(N)
R = np.zeros(N)
rng = np.random.default_rng(3)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2) * 1.414
    R[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2) * 1.414


def tt(d):
    return np.arange(int(d * SR)) / SR


def marimba(m, d=0.9):
    t = tt(d)
    f = hz(m)
    env = np.exp(-t * 7) * (1 - np.exp(-t * 900))
    return env * (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 25)
                  + 0.1 * np.sin(2 * np.pi * 10 * f * t) * np.exp(-t * 60))


def glock(m, d=1.6):
    t = tt(d)
    f = hz(m)
    env = np.exp(-t * 3.2) * (1 - np.exp(-t * 2000))
    return env * (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t * 8)
                  + 0.15 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t * 14))


def bass(m, d=0.45):
    t = tt(d)
    f = hz(m)
    env = np.exp(-t * 5) * (1 - np.exp(-t * 400))
    return env * (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) + 0.2 * np.sin(2 * np.pi * 3 * f * t))


def pad(notes, d):
    t = tt(d)
    env = np.minimum(1, t / 0.8) * np.minimum(1, (d - t) / 0.6)
    s = np.zeros_like(t)
    for m in notes:
        for det in (-0.004, 0.0, 0.004):
            f = hz(m) * (1 + det)
            s += np.sin(2 * np.pi * f * t + rng.random() * 6) + 0.2 * np.sin(4 * np.pi * f * t)
    return env * s / (len(notes) * 3)


def kick(d=0.35):
    t = tt(d)
    f = 45 + 90 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def hp_noise(d, k=1):
    n = rng.standard_normal(int(d * SR))
    for _ in range(k):
        n = np.diff(n, prepend=0)
    return n / (np.abs(n).max() + 1e-9)


def shaker(d=0.07):
    t = tt(d)
    return hp_noise(d, 2) * np.exp(-t * 60) * (1 - np.exp(-t * 600))


def clap():
    d = 0.2
    t = tt(d)
    env = np.exp(-t * 22)
    for off in (0.0, 0.011, 0.022):
        env += 0.6 * np.exp(-np.maximum(0, t - off) * 160) * (t >= off)
    return hp_noise(d, 1) * env * 0.5


def whoosh(d=0.6):
    t = tt(d)
    n = rng.standard_normal(len(t))
    out = np.zeros_like(n)
    a = 0.0
    for i in range(len(n)):
        a += (0.02 + 0.5 * (i / len(n)) ** 2) * (n[i] - a)
        out[i] = a
    return out / (np.abs(out).max() + 1e-9) * (t / d) ** 2.2


# (triad, bass note, glock hook) for scenes 1-5
CHORDS = [
    ([60, 64, 67], 48, [76, 79, 81, 79, 76]),
    ([57, 60, 64], 45, [76, 72, 74, 76, 79]),
    ([53, 57, 60], 41, [77, 76, 72, 74, 76]),
    ([55, 59, 62], 43, [74, 79, 83, 81, 79]),
    ([52, 55, 59], 40, [76, 79, 83, 86, 83]),  # Em -> lifts into the reveal
]
ARP = [0, 1, 2, 3, 2, 1, 0, 1, 2, 3, 4, 3, 2, 1, 0, 1, 2, 3, 4, 3]  # 20 eighths = 5s
HOOK = [0, 2, 4, 6, 8]

for s, (tri, bn, hook) in enumerate(CHORDS):
    t0 = s * SCENE
    tones = tri + [tri[0] + 12, tri[1] + 12]
    intro = s == 0
    add(pad(tri + [tri[0] - 12], SCENE + 0.4), t0, 0.18 if intro else 0.14)
    for k, idx in enumerate(ARP):
        g = 0.28 if k % 2 == 0 else 0.20
        if intro:
            g *= min(1, 0.35 + k / 14)  # gentle build
        add(marimba(tones[idx]), t0 + k * BEAT / 2, g, -0.35)
    for b, m in zip(HOOK, hook):
        add(glock(m), t0 + b * BEAT, 0.15, 0.4)
    bass_beats = (0, 4, 8) if intro else (0, 1.5, 3, 4, 5.5, 7, 8, 9.5)
    for b in bass_beats:
        add(bass(bn), t0 + b * BEAT, 0.40)
    if not intro:
        for b in range(10):
            if b % 2 == 0:
                add(kick(), t0 + b * BEAT, 0.5)
            else:
                add(clap(), t0 + b * BEAT, 0.09, 0.1)
        for e in range(20):
            add(shaker(), t0 + e * BEAT / 2, 0.04 if e % 2 else 0.018, 0.5 if e % 2 else -0.5)
    else:
        for e in range(10, 20):  # shaker sneaks in during the second half of the intro
            add(shaker(), t0 + e * BEAT / 2, 0.025 if e % 2 else 0.01, 0.5 if e % 2 else -0.5)
    if s < 4:
        add(whoosh(0.6), t0 + SCENE - 0.6, 0.05)
add(whoosh(0.45), 12.5 - 0.45, 0.035)  # library -> science glide

# 25s: brand reveal - riser, hit, warm C major resolve and outro
add(whoosh(0.9), 25.0 - 0.9, 0.07)
add(kick(0.6), 25.0, 0.65)
add(pad([48, 60, 64, 67, 72], 5.0), 25.0, 0.24)
add(bass(36, 2.5), 25.0, 0.45)
for i, m in enumerate([72, 76, 79, 84]):
    add(glock(m, 2.5), 25.0 + i * 0.09, 0.15, 0.4 - i * 0.25)
for k, m in enumerate([60, 64, 67, 72, 67, 64, 72, 76, 79, 76, 72, 67]):
    add(marimba(m, 1.2), 25.5 + k * BEAT / 2, 0.16 * (1 - k / 16), -0.3)
add(glock(84, 2.5), 27.0, 0.12, 0.2)
add(glock(79, 2.5), 28.0, 0.08, -0.2)

mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.3) / np.tanh(1.3)
t = np.arange(N) / SR
fade = np.minimum(1, t / 0.08) * np.clip((DUR - t) / 2.0, 0, 1) ** 1.5
mix *= fade[:, None]
mix *= 0.89 / np.abs(mix).max()

out = sys.argv[1] if len(sys.argv) > 1 else 'music.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', out)
