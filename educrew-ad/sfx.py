"""Realistic sound-effects track (no music, no synthetic swishes) for the 30s EduCrew ad,
muxed onto the video WITHOUT re-encoding the picture (-c:v copy).

All sounds are real recordings from FSD50K's CC0 (public-domain) subset
(Hugging Face dataset Atotti/fsd50k-cc0-Qwen3-Omni-captioned), stored in sfx_sources/
and named by role. Freesound clip ids: murmur 260123, type1 155574, type2 416196,
page 390876, desk 13840, marker 376503, pencil 335936,
mouse 378083.

Usage: python3 sfx.py in.mp4 out.mp4
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
DUR = 30.0
N = int(SR * DUR)
SRC = Path(__file__).parent / "sfx_sources"
L = np.zeros(N)
R = np.zeros(N)


def load(name):
    x, sr = sf.read(SRC / f"{name}.flac")
    assert sr == SR
    return x if x.ndim == 1 else x.mean(1)


def cut(name, a, b, fade_in=0.005, fade_out=0.04):
    """slice [a,b) seconds, short fades to avoid clicks, normalise to 0 dBFS peak"""
    x = load(name)[int(a * SR):int(b * SR)].copy()
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    if fi:
        x[:fi] *= np.linspace(0, 1, fi)
    if fo:
        x[-fo:] *= np.linspace(1, 0, fo)
    return x / (np.abs(x).max() + 1e-9)


def db(g):
    return 10 ** (g / 20)


def place(sig, t, gain_db, pan=0.0):
    i = int(t * SR)
    j = min(N, i + len(sig))
    g = db(gain_db)
    L[i:j] += sig[: j - i] * g * np.sqrt((1 - pan) / 2) * np.sqrt(2)
    R[i:j] += sig[: j - i] * g * np.sqrt((1 + pan) / 2) * np.sqrt(2)


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], lfilter([1 - a], [1, -a], x))


# ---------------- background: real indoor murmur of people (conference/lecture room) ----------------
m = load("murmur")
m = m / np.sqrt(np.mean(m ** 2))  # RMS normalise
# two layers at different offsets so no single phrase stands out; softened highs = distant, unintelligible
mA = np.concatenate([m[int(1.0 * SR):], m[: int(1.0 * SR)]])
mB = np.concatenate([m[int(11.5 * SR):], m[: int(11.5 * SR)]])
need = int(28.0 * SR)
bedL = np.resize(mA, need)
bedR = np.resize(mB, need)
bedL, bedR = lowpass(bedL, 2600), lowpass(bedR, 2600)


def detransient(x):
    """duck short spikes (chairs, cups, clatter) that rise above the slow speech envelope"""
    from scipy.ndimage import uniform_filter1d
    fast = np.sqrt(uniform_filter1d(x ** 2, int(0.01 * SR)) + 1e-12)
    slow = np.sqrt(uniform_filter1d(x ** 2, int(0.4 * SR)) + 1e-12)
    g = np.minimum(1.0, 1.4 * slow / fast)
    g = uniform_filter1d(g, int(0.005 * SR))
    return x * g


bedL, bedR = detransient(bedL), detransient(bedR)
env = np.ones(need)
fi, fo = int(0.8 * SR), int(2.5 * SR)
env[:fi] = np.linspace(0, 1, fi)
env[int(25.0 * SR):int(25.0 * SR) + fo] = np.linspace(1, 0, fo)
env[int(25.0 * SR) + fo:] = 0
gbed = db(-35)
L[:need] += (0.75 * bedL + 0.25 * bedR) * env * gbed
R[:need] += (0.25 * bedL + 0.75 * bedR) * env * gbed

# ---------------- foley, timed to picture ----------------
# Only desk, laptop-typing, page-turn, marker, pencil and mouse recordings are used:
# no glass, dice/clatter or bag-like paper sounds.
TYPE_A = ("type1", 4.7, 7.0)    # steady soft laptop typing
TYPE_B = ("type1", 7.0, 9.3)
TYPE_C = ("type1", 9.3, 11.8)
TYPE_D = ("type1", 2.1, 3.2)
PAGES = {1: (0.75, 1.15), 2: (2.75, 3.15), 3: (4.35, 5.15), 4: (7.75, 8.55), 5: (8.85, 10.35), 6: (11.35, 11.85)}


def typing(seg, t, g, pan=0.0):
    name, a, b = seg
    place(cut(name, a, b, 0.02, 0.2), t, g, pan)


def page(k, t, g, pan=0.0):
    a, b = PAGES[k]
    place(cut("page", a - 0.05, b + 0.1, 0.01, 0.12), t, g, pan)


# Clip 1 (0-5s): hand places tiny sign on desk, laptop typing, a page turned
place(cut("desk", 1.36, 1.62), 1.05, -8)             # sign set down on desk
typing(TYPE_A, 1.6, -13, 0.25)
page(1, 3.95, -9, -0.3)

# Clip 2 (5-10s): marker on whiteboard, workbook pages, laptop typing, pencil
place(cut("marker", 0.05, 1.05, 0.03, 0.1), 5.75, -19, -0.25)
place(cut("marker", 1.58, 2.25, 0.03, 0.1), 6.55, -20, -0.25)
typing(TYPE_B, 7.0, -15, 0.3)
page(2, 8.2, -9, -0.2)
place(cut("pencil", 0.0, 0.7, 0.01, 0.12), 9.0, -18, 0.1)

# Clip 3 (10-15s): library - pages turning, flicking through a book; light typing
page(3, 10.3, -8, -0.4)
page(5, 11.25, -10, -0.2)
page(6, 13.1, -9, 0.2)
typing(TYPE_D, 13.8, -17, 0.35)

# Clip 4 (15-20s): specialists typing on two laptops, assessment sheet turned in, pen ticks
typing(TYPE_C, 15.15, -13, -0.3)
place(cut("type2", 0.5, 2.3, 0.02, 0.2), 16.0, -21, 0.4)
page(4, 17.05, -8, 0.35)
place(cut("pencil", 1.30, 1.70, 0.01, 0.08), 18.55, -16, -0.2)
place(cut("pencil", 2.0, 2.35, 0.01, 0.08), 18.95, -17, -0.2)
typing(TYPE_D, 19.1, -16, 0.2)

# Clip 5 (20-25s): digital studio - several laptops typing, checklist ticks, page, mouse click
typing(TYPE_B, 20.25, -13, -0.35)
place(cut("type2", 2.3, 4.4, 0.02, 0.2), 20.8, -20, 0.4)
place(cut("pencil", 0.30, 0.62, 0.01, 0.06), 22.4, -16, -0.3)
place(cut("pencil", 1.30, 1.62, 0.01, 0.06), 22.75, -17, -0.3)
place(cut("pencil", 2.0, 2.32, 0.01, 0.06), 23.1, -17, -0.3)
place(cut("mouse", 0.10, 0.45, 0.002, 0.05), 23.55, -13, 0.2)
page(1, 24.0, -11, 0.0)

# End card (25-30s): room settles; a last soft page turn and desk touch as the logo lands
page(2, 25.0, -17, 0.0)
place(cut("desk", 1.36, 1.62), 26.05, -16, 0.0)

# ---------------- master ----------------
mix = np.stack([L, R], 1)
mix *= 0.9 / np.abs(mix).max()
fo = int(0.5 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]


def main(src, out):
    wav = Path(out).with_suffix(".sfx.wav")
    sf.write(wav, mix, SR, subtype="PCM_24")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-af", "loudnorm=I=-18:TP=-2:LRA=11,alimiter=limit=0.84:level=false", "-ar", "48000",
         "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out],
        check=True,
    )
    wav.unlink()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
