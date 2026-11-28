"""Bring a still picture to life without an AI video model (free, runs on the CPU).

Each scene is animated by bending parts of the picture over time (displacement maps):
  bob      move a region up/down (an animal floating on water)
  breathe  gently grow/shrink a region (an animal breathing)
  rock     tilt a region back and forth (otters rocking on waves)
  shift    slide a region (a dolphin swimming forward)
  pop      quickly enlarge a small region then settle (draw the eye to a detail)
  ripple   wavy water
  sway     tree tops / curtains moving in the breeze
  twinkle  stars and lights sparkling
  glow     a soft light pulsing (lamp, moon)
  zzz      little "z" letters floating up from a sleeping animal

Every effect can be limited to one narration line (`lines: [1]`, counting from 0), so each
action happens while that line is spoken. Output: one clip per line, <clip>_<i>.mp4, with
each clip lasting exactly as long as its line's window in timing.json.
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .compose import _font


def _mask(h, w, cx, cy, rx, ry, soft=0.55):
    """Soft elliptical mask (1 inside, fading to 0 at the edge)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = ((xx / w - cx) / rx) ** 2 + ((yy / h - cy) / ry) ** 2
    m = np.clip((1 - d) / soft, 0, 1)
    return m * m * (3 - 2 * m)


def _env(t, a, b, ramp=0.35):
    """1 inside [a, b] with soft ramps, 0 outside."""
    if t < a - ramp or t > b + ramp:
        return 0.0
    up = min(1.0, (t - (a - ramp)) / ramp)
    down = min(1.0, ((b + ramp) - t) / ramp)
    return max(0.0, min(up, down))


class Scene:
    def __init__(self, image: Path, recipe: list[dict], size: int = 1024):
        img = Image.open(image).convert("RGB").resize((size, size), Image.LANCZOS)
        self.img = np.asarray(img).astype(np.float32)
        self.h = self.w = size
        self.recipe = recipe
        yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
        self.xx, self.yy = xx, yy
        self.masks = {}
        lum = self.img.mean(axis=2)
        self.lum = lum
        rng = np.random.default_rng(3)
        # smooth random phase field for twinkling
        noise = cv2.resize(rng.random((24, 24)).astype(np.float32), (size, size),
                           interpolation=cv2.INTER_CUBIC)
        self.phase = noise * 2 * math.pi * 3

    def _m(self, e):
        key = (e.get("cx"), e.get("cy"), e.get("rx"), e.get("ry"))
        if key not in self.masks:
            self.masks[key] = _mask(self.h, self.w, e["cx"], e["cy"], e["rx"], e["ry"],
                                    e.get("soft", 0.55))
        return self.masks[key]

    def frame(self, t: float, windows: list[tuple[float, float]]) -> np.ndarray:
        H, W = self.h, self.w
        dx = np.zeros((H, W), np.float32)
        dy = np.zeros((H, W), np.float32)
        post = []
        for e in self.recipe:
            lines = e.get("lines")
            k = 1.0
            if lines is not None:
                k = max(_env(t, *windows[i]) for i in lines)
                if k <= 0:
                    continue
            kind = e["type"]
            amp = e.get("amp", 1.0) * k
            spd = e.get("speed", 1.0)
            if kind == "ripple":
                y0 = e.get("y0", 0.5) * H
                band = np.clip((self.yy - y0) / (H * 0.08), 0, 1)
                dx += band * amp * 3.0 * np.sin(self.yy / H * 60 + t * 2.2 * spd)
                dy += band * amp * 1.2 * np.sin(self.xx / W * 25 + t * 1.7 * spd)
                continue
            if kind in ("twinkle", "glow", "zzz"):
                post.append((e, k))
                continue
            m = self._m(e)
            cx, cy = e["cx"] * W, e["cy"] * H
            if kind == "bob":
                dy += m * amp * H * 0.012 * math.sin(t * 2.4 * spd + e.get("ph", 0))
                dx += m * amp * W * 0.004 * math.sin(t * 1.3 * spd + e.get("ph", 0))
            elif kind == "breathe":
                s = amp * 0.025 * math.sin(t * 2.0 * spd)
                dx += m * (self.xx - cx) * s
                dy += m * (self.yy - cy) * s * 1.2
            elif kind == "rock":
                ang = math.radians(amp * 4.0 * math.sin(t * 1.6 * spd))
                rx, ry = self.xx - cx, self.yy - cy
                dx += m * (rx * (math.cos(ang) - 1) - ry * math.sin(ang))
                dy += m * (rx * math.sin(ang) + ry * (math.cos(ang) - 1))
            elif kind == "shift":   # progressive slide across the line window
                a, b = windows[e["lines"][0]]
                p = min(max((t - a) / max(b - a, 1e-3), 0), 1)
                p = p * p * (3 - 2 * p)
                dx += m * e.get("x", 0) * W * p
                dy += m * e.get("y", 0) * H * p
            elif kind == "pop":
                a, b = windows[e["lines"][0]]
                p = (t - a) / 0.6
                s = 0.0 if p < 0 else (0.35 * math.sin(min(p, 1) * math.pi) +
                                       0.08 * (p >= 1)) * amp
                dx += m * (self.xx - cx) * s
                dy += m * (self.yy - cy) * s
            elif kind == "sway":
                ys = np.clip(1 - (self.yy / H - e.get("y_top", 0)) /
                             max(e.get("y_len", 0.4), 1e-3), 0, 1)
                dx += m * ys * amp * W * 0.008 * math.sin(t * 1.4 * spd + e.get("ph", 0))
        # remap: content inside a mask moves by (dx, dy)
        out = cv2.remap(self.img, self.xx - dx, self.yy - dy, cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REFLECT)
        for e, k in post:
            if e["type"] == "twinkle":
                region = (self.yy / H < e.get("y_max", 0.35)) & (self.lum > e.get("lum", 200))
                flick = 0.5 + 0.5 * np.sin(self.phase + t * 4.0)
                gain = 1 + region * flick * 0.45 * e.get("amp", 1.0) * k
                out = out * gain[..., None]
            elif e["type"] == "glow":
                m = self._m(e)
                pulse = (0.5 + 0.5 * math.sin(t * 2.2 * e.get("speed", 1.0))) * e.get("amp", 1.0) * k
                col = np.array(e.get("color", [255, 220, 150]), np.float32)
                out = out + m[..., None] * col * 0.18 * pulse
            elif e["type"] == "zzz":
                out = _draw_zzz(out, t, e, k, W, H)
        return np.clip(out, 0, 255).astype(np.uint8)


def _draw_zzz(arr, t, e, k, W, H):
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(3):
        p = ((t * 0.45 + i / 3) % 1.0)
        x = e["cx"] * W + p * W * 0.08 + math.sin(p * 6) * 6
        y = e["cy"] * H - p * H * 0.14
        size = int(H * (0.03 + 0.02 * p))
        a = int(255 * math.sin(p * math.pi) * k)
        d.text((x, y), "z", font=_font(size), fill=(255, 255, 255, a),
               stroke_width=max(2, size // 9), stroke_fill=(70, 40, 110, a))
    img.alpha_composite(layer)
    return np.asarray(img.convert("RGB")).astype(np.float32)


def render_segments(image: Path, recipe: list[dict], windows: list[tuple[float, float]],
                    out_prefix: Path, fps: int = 24, size: int = 1024) -> list[Path]:
    """Render one clip per line window (times are relative to the shot start)."""
    scene = Scene(image, recipe, size)
    outs = []
    for i, (a, b) in enumerate(windows):
        path = out_prefix.parent / f"{out_prefix.name}_{i}.mp4"
        path.parent.mkdir(parents=True, exist_ok=True)
        n = max(1, int(round((b - a) * fps)))
        proc = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{size}x{size}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "17",
             "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
        for f in range(n):
            proc.stdin.write(scene.frame(a + f / fps, windows).tobytes())
        proc.stdin.close()
        proc.wait()
        outs.append(path)
    return outs
