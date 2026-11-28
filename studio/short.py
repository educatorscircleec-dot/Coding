"""Render a narrated short in one pass, so picture, voice, captions and map stay in sync.

Timeline rule: the voice drives everything.
  * each line's real speech length (silence trimmed) is measured from its audio file
  * pauses between lines / shots are spread so the whole short lands on `target_seconds`
  * each shot lasts exactly as long as its lines (+ pauses); its animated clip is gently
    time-stretched to fit
  * captions appear when their line starts, with the current word highlighted
  * map pins drop when the line marked `map_line: true` starts

Audio: narration + soft procedural music-box bed (ducked under the voice) + light SFX
(whoosh on cuts, pop on pins). Nothing is fetched from outside.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from .compose import _font, _round_logo
from .motion import (INK, _with_shadow, ease, ease_out_back, load_sticker_frames, map_card)

SR = 44100
HIGHLIGHT = (255, 214, 64)


# ---------------------------------------------------------------- audio helpers
def load_audio(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def trim_silence(a: np.ndarray, thr: float = 0.02, pad: float = 0.04) -> np.ndarray:
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx):
        return a
    p = int(pad * SR)
    return a[max(0, idx[0] - p): idx[-1] + p]


def music_bed(seconds: float, bpm: int = 84) -> np.ndarray:
    """Gentle music-box lullaby (pentatonic), soft enough to sit under a voice."""
    n = int(seconds * SR)
    out = np.zeros(n, np.float32)
    beat = 60 / bpm
    # C major pentatonic melody + root notes, 16-beat loop
    mel = [72, 76, 79, 76, 74, 72, 74, 76, 79, 81, 79, 76, 74, 76, 72, -1]
    bass = [48, 48, 55, 55, 53, 53, 55, 55]
    def note(midi, dur, amp):
        f = 440 * 2 ** ((midi - 69) / 12)
        t = np.arange(int(dur * SR)) / SR
        env = np.exp(-t * 3.2) * (1 - np.exp(-t * 400))
        tone = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) \
            + 0.12 * np.sin(6 * np.pi * f * t)
        return (tone * env * amp).astype(np.float32)
    i = 0
    t = 0.0
    while t < seconds:
        m = mel[i % len(mel)]
        if m > 0:
            s = note(m, beat * 2.5, 0.16)
            k = int(t * SR)
            out[k:k + len(s)] += s[: max(0, n - k)]
        if i % 2 == 0:
            b = note(bass[(i // 2) % len(bass)], beat * 3, 0.12)
            k = int(t * SR)
            out[k:k + len(b)] += b[: max(0, n - k)]
        t += beat
        i += 1
    fade = int(1.5 * SR)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out


def sfx_whoosh(dur: float = 0.35) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    noise = np.random.default_rng(1).standard_normal(len(t)).astype(np.float32)
    # simple moving-average low-pass whose width sweeps = rising whoosh
    out = np.zeros_like(noise)
    for k in range(len(t)):
        w = int(40 - 34 * (k / len(t)))
        out[k] = noise[max(0, k - w):k + 1].mean()
    env = np.sin(np.pi * t / dur) ** 2
    return out * env * 0.5


def sfx_pop(dur: float = 0.12) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    f = 900 + 900 * np.exp(-t * 40)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35) * 0.25).astype(np.float32)


# ---------------------------------------------------------------- timeline
@dataclass
class Line:
    id: str
    text: str
    audio: np.ndarray
    start: float = 0.0          # absolute seconds
    map_line: bool = False

    @property
    def dur(self) -> float:
        return len(self.audio) / SR


@dataclass
class Shot:
    id: str
    spec: dict
    lines: list[Line]
    start: float = 0.0
    end: float = 0.0
    frames: list = field(default_factory=list)


def build_timeline(shots: list[Shot], target: float, lead: float = 0.3,
                   tail: float = 0.9) -> None:
    speech = sum(l.dur for s in shots for l in s.lines)
    n_inner = sum(len(s.lines) - 1 for s in shots)
    n_cuts = len(shots) - 1
    free = target - speech - lead - tail
    # inner pauses are a bit shorter than the beat between shots
    unit = free / (n_inner * 1.0 + n_cuts * 1.6) if (n_inner + n_cuts) else 0
    inner, cut = max(0.15, unit), max(0.25, unit * 1.6)
    t = 0.0
    for i, s in enumerate(shots):
        s.start = t
        t += lead if i == 0 else cut / 2
        for j, l in enumerate(s.lines):
            l.start = t
            t += l.dur + (inner if j < len(s.lines) - 1 else 0)
        t += tail if i == len(shots) - 1 else cut / 2
        s.end = t


# ---------------------------------------------------------------- captions
def _words_with_weights(text: str):
    words = text.split()
    w = [max(1, len(re.findall(r"[aeiouy]+", x.lower()))) + len(x) * 0.15 for x in words]
    return words, w


def caption_image(text: str, active: int, width: int, size: int) -> Image.Image:
    font = _font(size)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    words = text.split()
    lines, cur = [], []
    for i, wd in enumerate(words):
        test = " ".join(words[j] for j in cur + [i])
        if cur and probe.textlength(test, font=font) > width:
            lines.append(cur)
            cur = [i]
        else:
            cur.append(i)
    lines.append(cur)
    lh = int(size * 1.2)
    img = Image.new("RGBA", (width, lh * len(lines) + size // 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    space = probe.textlength(" ", font=font)
    for li, idxs in enumerate(lines):
        total = probe.textlength(" ".join(words[i] for i in idxs), font=font)
        x = (width - total) / 2
        for i in idxs:
            fill = HIGHLIGHT if i == active else "white"
            d.text((x, li * lh), words[i], font=font, fill=fill,
                   stroke_width=max(3, size // 8), stroke_fill=INK)
            x += probe.textlength(words[i], font=font) + space
    return img


# ---------------------------------------------------------------- video helpers
def load_clip(path: Path, size: int) -> tuple[list[Image.Image], float]:
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height,r_frame_rate", "-of", "json", str(path)],
                           capture_output=True, text=True, check=True)
    st = json.loads(probe.stdout)["streams"][0]
    w, h = st["width"], st["height"]
    num, den = map(int, st["r_frame_rate"].split("/"))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    n = len(raw) // (w * h * 3)
    frames = []
    for k in range(n):
        im = Image.frombuffer("RGB", (w, h), raw[k * w * h * 3:(k + 1) * w * h * 3])
        side = min(w, h)
        im = im.crop(((w - side) // 2, (h - side) // 2, (w - side) // 2 + side,
                      (h - side) // 2 + side)).resize((size, size), Image.LANCZOS)
        frames.append(im)
    return frames, num / den


def band_background(first: Image.Image, W: int, H: int) -> Image.Image:
    scale = max(W / first.width, H / first.height)
    b = first.resize((int(first.width * scale) + 1, int(first.height * scale) + 1))
    b = b.crop(((b.width - W) // 2, (b.height - H) // 2, (b.width - W) // 2 + W,
                (b.height - H) // 2 + H))
    return ImageEnhance.Brightness(b.filter(ImageFilter.GaussianBlur(40))).enhance(0.5)


def _fit_text(text: str, max_w: int, size: int) -> Image.Image:
    while size > 20 and ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(
            text, font=_font(size)) > max_w:
        size -= 2
    return caption_image(text, -1, max_w, size)


# ---------------------------------------------------------------- render
def render_short(project, ep_id: str, spec: dict) -> Path:
    root = project.root
    base = project.output_dir / ep_id
    W, H = project.resolution(ep_id)
    fps = project.fps(ep_id)
    target = float(spec.get("target_seconds", 45))
    lines_dir = base / spec.get("lines_dir", "lines")
    clips_dir = base / spec.get("clips_dir", "wan")
    brand = project.style.get("brand", {})
    logo_path = root / brand["logo"] if brand.get("logo") else None

    P = W
    top = int((H - P) * 0.47)
    bottom_y = top + P
    band_h = H - bottom_y
    m = int(W * 0.03)

    shots: list[Shot] = []
    for s in spec["shots"]:
        lines = [Line(l["id"], l["line"], trim_silence(load_audio(lines_dir / f"{l['id']}.mp3")),
                      map_line=bool(l.get("map_line"))) for l in s["lines"]]
        shots.append(Shot(s["id"], s, lines))
    build_timeline(shots, target)

    logo_size = min(int(W * 0.2), top - 2 * m)
    logo = _round_logo(logo_path, logo_size) if logo_path else None
    right_x = m * 2 + logo_size if logo else m
    right_w = W - right_x - m

    # per-shot assets
    for s in shots:
        clip = clips_dir / f"{s.spec['clip']}.mp4"
        if not clip.exists() and spec.get("fallback_clips_dir"):
            clip = base / spec["fallback_clips_dir"] / f"{s.spec['clip']}.mp4"
            print(f"[{s.id}] animated clip not ready yet, using {clip.relative_to(root)}")
        s.frames, s.clip_fps = load_clip(clip, P)
        s.band = band_background(s.frames[0], W, H).convert("RGBA")
        s.sticker = []
        if s.spec.get("sticker"):
            raw, durs = load_sticker_frames(root / "brand" / "stickers" /
                                            f"{s.spec['sticker']}.png")
            sw = int(W * float(s.spec.get("sticker_scale", 0.33)))
            s.sticker = [_with_shadow(f.resize((sw, round(f.height * sw / f.width)),
                                               Image.LANCZOS)) for f in raw]
            s.sticker_durs = durs
        s.title = _fit_text(s.spec["title"], right_w, int(top * 0.2)) if s.spec.get("title") else None
        map_line = next((l for l in s.lines if l.map_line), None)
        s.pin_t = (map_line.start - s.start) if map_line else 1.0

    total = shots[-1].end
    n_frames = int(round(total * fps))
    out_path = base / f"{ep_id}.mp4"
    silent = base / f"{ep_id}_video.mp4"
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium",
         "-crf", "18", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)

    xfade = 0.22
    prev_last = None
    cap_cache: dict = {}
    for fi in range(n_frames):
        ts = fi / fps
        si = next(i for i, s in enumerate(shots) if ts < s.end or i == len(shots) - 1)
        s = shots[si]
        lt = ts - s.start                       # time inside the shot
        dur = s.end - s.start
        frame = s.band.copy()

        # animated picture, time-stretched to the shot length
        k = min(len(s.frames) - 1, int(lt / dur * len(s.frames)))
        frame.paste(s.frames[k], (0, top))

        if logo:
            frame.alpha_composite(logo, (m, (top - logo_size) // 2))

        # map card: slides in at the start, pins drop when the location line starts
        if s.spec.get("map"):
            slide = ease_out_back((lt - 0.15) / 0.45)
            if slide > 0:
                mspec = dict(s.spec["map"])
                card = map_card(lt, mspec, (right_w, top - 2 * m), dur,
                                fly_start=max(0.3, s.pin_t - 1.6), pin_start=s.pin_t)
                mx = int(right_x + (1 - slide) * (W - right_x + m))
                frame.alpha_composite(_with_shadow(card), (mx - 40, m - 40))
        elif s.title is not None:
            p = ease_out_back((lt - 0.1) / 0.5)
            if p > 0:
                tl = s.title.resize((max(1, int(s.title.width * p)),
                                     max(1, int(s.title.height * p))))
                frame.alpha_composite(tl, (right_x + (right_w - tl.width) // 2,
                                           (top - tl.height) // 2))

        # host sticker (only where she talks to the viewer)
        cap_x, cap_w = m, W - 2 * m
        if s.sticker:
            tot = sum(s.sticker_durs)
            j, acc = 0, lt % tot
            while j < len(s.sticker_durs) - 1 and acc >= s.sticker_durs[j]:
                acc -= s.sticker_durs[j]
                j += 1
            st = s.sticker[j]
            pop = max(0.05, ease_out_back(lt / 0.4))
            sc = (0.6 + 0.4 * pop)
            st2 = st.resize((max(1, int(st.width * sc)), max(1, int(st.height * sc))))
            y = int(H - st2.height + 30 + math.sin(lt * 2.6) * 5)
            frame.alpha_composite(st2, (m - 40 + (st.width - st2.width) // 2, max(0, y)))
            cap_x = m + st.width - 70
            cap_w = W - cap_x - m

        # caption for the line being spoken, active word highlighted
        cur = next((l for l in s.lines if l.start - 0.05 <= ts < l.start + l.dur + 0.25), None)
        if cur is not None:
            words, wts = _words_with_weights(cur.text)
            prog = (ts - cur.start) / max(cur.dur, 0.01)
            acc, active = 0.0, len(words) - 1
            for wi, wv in enumerate(wts):
                acc += wv / sum(wts)
                if prog < acc:
                    active = wi
                    break
            key = (cur.id, active, cap_w)
            if key not in cap_cache:
                cap_cache[key] = caption_image(cur.text, active, cap_w, int(band_h * 0.15))
            cap = cap_cache[key]
            p = min(1.0, ease_out_back((ts - cur.start + 0.05) / 0.25))
            if p > 0:
                c2 = cap if p == 1 else cap.resize((max(1, int(cap.width * p)),
                                                    max(1, int(cap.height * p))))
                frame.alpha_composite(c2, (cap_x + (cap_w - c2.width) // 2,
                                           bottom_y + (band_h - c2.height) // 2))

        rgb = frame.convert("RGB")
        # quick cross-fade into each new shot
        if si > 0 and lt < xfade and prev_last is not None:
            rgb = Image.blend(prev_last, rgb, ease(lt / xfade))
        if si + 1 < len(shots) and s.end - ts <= 1.0 / fps + 1e-6:
            prev_last = rgb
        proc.stdin.write(rgb.tobytes())
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError("ffmpeg failed")

    # ---- audio: voice + ducked music bed + sfx
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    for s in shots:
        for l in s.lines:
            k = int(l.start * SR)
            voice[k:k + len(l.audio)] += l.audio
    peak = np.abs(voice).max() or 1
    voice *= 0.89 / peak
    env = np.convolve(np.abs(voice), np.ones(int(0.25 * SR)) / int(0.25 * SR), "same")
    duck = 1 - 0.6 * np.clip(env / (env.max() or 1) * 4, 0, 1)
    bed = music_bed(total + 1)[:n] * duck * float(spec.get("music_level", 0.55))
    fx = np.zeros(n, np.float32)
    wh, pop = sfx_whoosh(), sfx_pop()
    for s in shots[1:]:
        k = max(0, int((s.start - 0.15) * SR))
        fx[k:k + len(wh)] += wh[: n - k] * 0.5
    for s in shots:
        if s.spec.get("map"):
            for i in range(len(s.spec["map"].get("pins", []))):
                k = int((s.start + s.pin_t + i * 0.18 + 0.15) * SR)
                fx[k:k + len(pop)] += pop[: max(0, n - k)]
    mix = np.clip(voice + bed + fx, -1, 1)[: int(total * SR)]
    wav = base / f"{ep_id}_mix.wav"
    import soundfile as sf
    sf.write(str(wav), mix, SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest", str(out_path)], check=True)
    silent.unlink()

    # subtitles + timing report
    srt = []
    for i, l in enumerate([l for s in shots for l in s.lines], 1):
        from .assemble import _ts
        srt.append(f"{i}\n{_ts(l.start)} --> {_ts(l.start + l.dur)}\n{l.text}\n")
    (base / f"{ep_id}.srt").write_text("\n".join(srt), encoding="utf-8")
    report = [{"shot": s.id, "start": round(s.start, 2), "end": round(s.end, 2),
               "lines": [{"id": l.id, "start": round(l.start, 2), "end": round(l.start + l.dur, 2),
                          "text": l.text} for l in s.lines]} for s in shots]
    (base / "timing.json").write_text(json.dumps(report, indent=2))
    return out_path
