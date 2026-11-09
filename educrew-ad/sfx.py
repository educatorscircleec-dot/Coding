"""Realistic sound-effects track (no music, no synthetic swishes) for the 30s EduCrew ad,
muxed onto the video WITHOUT re-encoding the picture (-c:v copy).

All sounds are real recordings from FSD50K's CC0 (public-domain) subset
(Hugging Face dataset Atotti/fsd50k-cc0-Qwen3-Omni-captioned), stored in sfx_sources/
and named by role. Freesound clip ids: murmur 260123, type1 155574, type2 416196,
page 390876, paperdrop 105076, desk 13840, marker 376503, pencil 335936,
dice 126465, glass 163732, mouse 378083.

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
env = np.ones(need)
fi, fo = int(0.8 * SR), int(2.5 * SR)
env[:fi] = np.linspace(0, 1, fi)
env[int(25.0 * SR):int(25.0 * SR) + fo] = np.linspace(1, 0, fo)
env[int(25.0 * SR) + fo:] = 0
gbed = db(-35)
L[:need] += (0.75 * bedL + 0.25 * bedR) * env * gbed
R[:need] += (0.25 * bedL + 0.75 * bedR) * env * gbed

# ---------------- foley, timed to picture ----------------
# Clip 1 (0-5s): hand places tiny sign on desk, laptop typing, papers
place(cut("desk", 1.36, 1.62), 1.05, -8)             # sign set down on desk
place(cut("type1", 0.0, 1.5, fade_out=0.15), 2.0, -13, 0.25)
place(cut("paperdrop", 0.0, 1.0, fade_out=0.2), 3.55, -16, -0.3)

# Clip 2 (5-10s): marker on whiteboard, number tiles, pencil on worksheet
place(cut("marker", 0.05, 1.05, 0.03, 0.1), 5.75, -19, -0.25)
place(cut("marker", 1.58, 2.25, 0.03, 0.1), 6.55, -20, -0.25)
place(cut("dice", 0.94, 1.75, 0.003, 0.25), 7.35, -17, 0.3)
place(cut("pencil", 0.0, 1.05, 0.01, 0.12), 8.45, -17, 0.1)

# Clip 3 (10-15s): library page turns -> science corner glass clink, globe nudged
place(cut("page", 0.0, 1.0, 0.01, 0.15), 10.6, -8, -0.4)
place(cut("page", 2.05, 2.75, 0.01, 0.12), 11.55, -10, -0.3)
place(cut("glass", 0.70, 0.98, 0.002, 0.08), 12.8, -10, 0.35)
place(cut("desk", 1.62, 1.78), 13.9, -15, 0.2)

# Clip 4 (15-20s): specialists typing, hand slides assessment sheet in, pen ticks
place(cut("type2", 0.6, 2.3, 0.01, 0.2), 15.5, -15, -0.3)
place(cut("paperdrop", 0.0, 1.0, fade_out=0.2), 17.0, -11, 0.35)
place(cut("pencil", 1.30, 1.70, 0.01, 0.08), 18.55, -16, -0.2)
place(cut("pencil", 2.0, 2.35, 0.01, 0.08), 18.95, -17, -0.2)

# Clip 5 (20-25s): digital studio typing, checklist ticks, mouse click
place(cut("type1", 2.05, 3.4, 0.01, 0.15), 20.7, -14, 0.35)
place(cut("pencil", 0.30, 0.62, 0.01, 0.06), 22.0, -16, -0.3)
place(cut("pencil", 1.30, 1.62, 0.01, 0.06), 22.35, -17, -0.3)
place(cut("pencil", 2.0, 2.32, 0.01, 0.06), 22.7, -17, -0.3)
place(cut("mouse", 0.10, 0.45, 0.002, 0.05), 23.25, -12, 0.2)

# End card (25-30s): room settles as studio fades; one soft book/desk touch as the logo lands
place(cut("page", 0.0, 0.7, 0.01, 0.2), 25.0, -22, 0.0)
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
