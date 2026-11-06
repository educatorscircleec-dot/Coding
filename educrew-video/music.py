"""Original 30 s instrumental bed for the EduCrew spot (no vocals).
120 BPM, D major, I–V–vi–IV: soft e-piano arpeggios, warm pad, bass, light
drums, transition swooshes at each scene change, subtle office ambience
(keyboard taps, room tone). Writes a 48 kHz stereo WAV.
usage: python3 music.py out.wav
"""
import sys, wave
import numpy as np

SR = 48000
DUR = 30.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(3)
L = np.zeros(N); R = np.zeros(N)
BEAT = 0.5  # 120 BPM


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * np.sqrt(0.5 * (1 - pan))
    R[i:i + len(sig)] += sig * np.sqrt(0.5 * (1 + pan))


def env(n, a=0.005, d=0.4):
    x = np.arange(n) / SR
    e = np.exp(-x / d)
    att = np.minimum(1, x / a)
    return e * att


def epiano(f, dur, d=0.6):
    n = int(dur * SR); x = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * x) + 0.35 * np.sin(2 * np.pi * 2 * f * x) * np.exp(-x / 0.15)
         + 0.12 * np.sin(2 * np.pi * 3 * f * x) * np.exp(-x / 0.08))
    return s * env(n, 0.004, d)


def pad(freqs, dur):
    n = int(dur * SR); x = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.12):
            ff = f * 2 ** (det / 12)
            s += np.sin(2 * np.pi * ff * x + rng.random() * 6) * 0.33
    a = np.minimum(1, x / 0.35) * np.minimum(1, (dur - x) / 0.35)
    return s * a / len(freqs)


def kick():
    n = int(0.35 * SR); x = np.arange(n) / SR
    f = 50 + 90 * np.exp(-x / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.12)


def hat(d=0.04):
    n = int(0.12 * SR); x = np.arange(n) / SR
    s = rng.standard_normal(n); s = np.diff(np.concatenate([[0], s]))
    return s * np.exp(-x / d) * 0.5


def clap():
    n = int(0.25 * SR); x = np.arange(n) / SR
    s = rng.standard_normal(n)
    s = s - np.convolve(s, np.ones(8) / 8, 'same')
    e = np.exp(-x / 0.06) * (1 + 0.6 * (np.sin(2 * np.pi * 90 * x) > 0))
    return s * e * 0.4


def swoosh(dur=0.9):
    n = int(dur * SR); x = np.arange(n) / SR
    s = rng.standard_normal(n)
    # sweeping one-pole low-pass
    out = np.zeros(n); y = 0.0
    cut = 0.02 + 0.25 * np.sin(np.pi * x / dur) ** 2
    for i in range(n):
        y += cut[i] * (s[i] - y); out[i] = y
    return out * np.sin(np.pi * x / dur) ** 2 * 0.9


def click():
    n = int(0.02 * SR); x = np.arange(n) / SR
    return rng.standard_normal(n) * np.exp(-x / 0.003)


# D major: D A Bm G
CHORDS = [(62, [62, 66, 69, 74]), (57, [57, 61, 64, 69]), (59, [59, 62, 66, 71]), (55, [55, 59, 62, 67])]
bar = 4 * BEAT
nbars = int(DUR / bar) + 1
for b in range(nbars):
    root, notes = CHORDS[b % 4]
    t0 = b * bar
    final = t0 >= 28.0
    # pad
    add(pad([midi(n) for n in notes[:3]], bar + 0.4), t0, 0.0, 0.10)
    # bass: root on 1, octave on & of 2, fifth on 3 & 4
    bpat = [(0, root - 24, .45), (1.5, root - 12, .2), (2, root - 17, .3), (3, root - 24, .3), (3.5, root - 12, .2)]
    for off, m, d in bpat:
        if t0 + off * BEAT < DUR:
            add(epiano(midi(m), 0.6, d) * 1.0, t0 + off * BEAT, 0.0, 0.32)
    # arpeggio 8ths (starts after door opens)
    if t0 >= 1.0 and not final:
        seq = [0, 2, 1, 3, 2, 1, 3, 2]
        for i, idx in enumerate(seq):
            m = notes[idx] + 12
            add(epiano(midi(m), 0.7, 0.35), t0 + i * BEAT / 2, -0.35 if i % 2 else 0.35, 0.10)
    # melody hooks every other bar
    if 5.0 <= t0 < 28 and b % 2 == 1:
        mel = [notes[3] + 12, notes[2] + 12, notes[3] + 12, notes[1] + 24]
        for i, m in enumerate(mel):
            add(epiano(midi(m), 1.0, 0.5), t0 + i * BEAT, 0.1, 0.09)
    # drums from 1 s to 28 s
    for beat in range(4):
        tb = t0 + beat * BEAT
        if tb < 1.0 or tb >= 28.0:
            continue
        if beat in (0, 2):
            add(kick(), tb, 0, 0.55)
        if beat in (1, 3) and tb >= 5.0:
            add(clap(), tb, 0.05, 0.22)
        add(hat(), tb + BEAT / 2, 0.3, 0.12)
        if tb >= 10:
            add(hat(0.015), tb + BEAT / 4, -0.3, 0.06)
            add(hat(0.015), tb + 3 * BEAT / 4, -0.3, 0.06)

# final sustained chord + shimmer
add(pad([midi(n) for n in [62, 66, 69, 74, 78]], 2.5), 27.6, 0, 0.18)
for i, m in enumerate([74, 78, 81, 86]):
    add(epiano(midi(m), 2.2, 1.2), 27.8 + i * 0.12, (-1) ** i * 0.4, 0.10)

# transitions: door creak-swoosh at 0.7 and swooshes into each scene
for ts in (0.9, 4.6, 9.6, 14.6, 19.6, 24.6):
    add(swoosh(0.9), ts - 0.45, 0, 0.18)

# office ambience: room tone + sporadic keyboard taps during typing scenes
room = rng.standard_normal(N)
room = np.convolve(room, np.ones(200) / 200, 'same') * 0.6
L += room * 0.04; R += room * 0.04
for a, b in ((5.0, 10.0), (10.5, 14.5), (15.2, 17.6)):
    tt = a
    while tt < b:
        add(click(), tt, rng.uniform(-0.5, 0.5), 0.05)
        tt += rng.uniform(0.07, 0.2)

mix = np.stack([L, R], 1)
# fade in/out
fade = np.ones(N)
fade[: int(0.3 * SR)] = np.linspace(0, 1, int(0.3 * SR))
fo = int(1.2 * SR); fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
mix *= fade[:, None]
mix = np.tanh(mix * 1.6) / np.tanh(1.6)
mix /= np.max(np.abs(mix)) / 0.89
pcm = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[1] if len(sys.argv) > 1 else 'music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok')
