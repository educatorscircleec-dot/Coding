"""Layered live motion: the animal is cut out and moved as a solid piece (no rubbery
warping), while the background (water, grass, sky) gets its own motion underneath.

Cut-outs come from BiRefNet-lite (MIT licence, runs on the CPU), downloaded once to
models/birefnet/onnx/model.onnx from the Hugging Face repo onnx-community/BiRefNet_lite-ONNX.

Animal moves (all rigid; positions are fractions of the picture):
  bob      up/down float          tilt     rock back and forth around a pivot
  breathe  whole-body gentle grow/shrink around a pivot (e.g. the feet)
  swim     slide by (x, y) across a line's window      settle  slowly sink/relax
  pop      enlarge a small part (an eye) briefly, as a solid disc
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .livemotion import Scene, _draw_zzz, _env

MODEL = Path(__file__).resolve().parent.parent / "models" / "birefnet" / "onnx" / "model.onnx"


def animal_mask(image: Path, cache: Path, keep: dict | None = None) -> np.ndarray:
    """Return a 0..1 mask of the main subject, cached as a PNG."""
    if not cache.exists():
        import onnxruntime as ort
        sess = ort.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])
        im = Image.open(image).convert("RGB")
        x = np.asarray(im.resize((1024, 1024)), np.float32) / 255
        x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None]
        y = sess.run(None, {sess.get_inputs()[0].name: x.astype(np.float32)})[-1][0, 0]
        m = 1 / (1 + np.exp(-y)) if y.min() < 0 else y
        cache.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).resize(im.size).save(cache)
    m = np.asarray(Image.open(cache).convert("L"), np.float32) / 255
    if keep:   # limit to an ellipse around the animal (drops stray sky/cloud bits)
        h, w = m.shape
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = ((xx / w - keep["cx"]) / keep["rx"]) ** 2 + ((yy / h - keep["cy"]) / keep["ry"]) ** 2
        m = m * (d <= 1)
    return m


class LayeredScene:
    def __init__(self, image: Path, mask: np.ndarray, bg_recipe: list, moves: list,
                 overlays: list, size: int = 1024):
        img = np.asarray(Image.open(image).convert("RGB").resize((size, size), Image.LANCZOS))
        m = cv2.resize(mask, (size, size))
        m = cv2.GaussianBlur(m, (0, 0), 1.2)
        hard = (m > 0.35).astype(np.uint8)
        hole = cv2.dilate(hard, np.ones((13, 13), np.uint8))
        bg = cv2.inpaint(img, hole * 255, 9, cv2.INPAINT_TELEA)
        self.size = size
        self.fg = img.astype(np.float32)
        self.alpha = np.clip(m * 1.15, 0, 1).astype(np.float32)
        self.bg_scene = Scene.__new__(Scene)
        Scene.__init__(self.bg_scene, image, bg_recipe, size)
        self.bg_scene.img = bg.astype(np.float32)
        self.moves, self.overlays = moves, overlays

    def _affine(self, t, windows):
        S = self.size
        A = np.eye(3, dtype=np.float32)
        def about(px, py, M):
            T1 = np.array([[1, 0, -px], [0, 1, -py], [0, 0, 1]], np.float32)
            T2 = np.array([[1, 0, px], [0, 1, py], [0, 0, 1]], np.float32)
            return T2 @ M @ T1
        for mv in self.moves:
            k = 1.0
            if mv.get("lines") is not None and mv["type"] not in ("swim", "settle"):
                k = max(_env(t, *windows[i]) for i in mv["lines"])
                if k <= 0:
                    continue
            amp, spd, ph = mv.get("amp", 1.0) * k, mv.get("speed", 1.0), mv.get("ph", 0.0)
            px, py = mv.get("px", 0.5) * S, mv.get("py", 0.5) * S
            kind = mv["type"]
            if kind == "bob":
                M = np.array([[1, 0, amp * S * 0.004 * math.sin(t * 1.3 * spd + ph)],
                              [0, 1, amp * S * 0.010 * math.sin(t * 2.4 * spd + ph)],
                              [0, 0, 1]], np.float32)
            elif kind == "tilt":
                a = math.radians(amp * 2.5 * math.sin(t * 1.6 * spd + ph))
                M = about(px, py, np.array([[math.cos(a), -math.sin(a), 0],
                                            [math.sin(a), math.cos(a), 0], [0, 0, 1]], np.float32))
            elif kind == "breathe":
                s = 1 + amp * 0.012 * math.sin(t * 2.0 * spd + ph)
                M = about(px, py, np.diag([s, s * 1.006, 1]).astype(np.float32))
            elif kind in ("swim", "settle"):
                a, b = windows[mv["lines"][0]] if mv.get("lines") else (0, 1)
                p = min(max((t - a) / max(b - a, 1e-3), 0), 1)
                p = p * p * (3 - 2 * p)
                if kind == "swim":
                    M = np.array([[1, 0, mv.get("x", 0) * S * p], [0, 1, mv.get("y", 0) * S * p],
                                  [0, 0, 1]], np.float32)
                else:
                    sy = 1 - mv.get("amount", 0.02) * p
                    M = about(px, py, np.diag([1 + (1 - sy) * 0.4, sy, 1]).astype(np.float32))
            else:
                continue
            A = M @ A
        return A

    def frame(self, t: float, windows) -> np.ndarray:
        S = self.size
        bg = self.bg_scene.frame(t, windows).astype(np.float32)
        A = self._affine(t, windows)[:2]
        fg = cv2.warpAffine(self.fg, A, (S, S), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_REPLICATE)
        al = cv2.warpAffine(self.alpha, A, (S, S), flags=cv2.INTER_LINEAR)[..., None]
        # solid "pop" of a small detail (e.g. an eye), moved with the animal
        for ov in self.overlays:
            if ov["type"] != "pop":
                continue
            a, b = windows[ov["lines"][0]]
            p = (t - a) / 0.7
            if not 0 <= p <= 1.6:
                continue
            s = 1 + 0.45 * math.sin(min(p, 1) * math.pi) * ov.get("amp", 1.0)
            cx, cy = A @ np.array([ov["cx"] * S, ov["cy"] * S, 1], np.float32)
            r = int(ov["r"] * S)
            x0, y0 = int(cx) - r, int(cy) - r
            patch = fg[y0:y0 + 2 * r, x0:x0 + 2 * r].copy()
            if patch.shape[:2] != (2 * r, 2 * r):
                continue
            big = cv2.resize(patch, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
            R = big.shape[0] // 2
            yy, xx = np.mgrid[-R:R, -R:R]
            disc = np.clip((R - np.sqrt(xx ** 2 + yy ** 2)) / (R * 0.25), 0, 1)[..., None]
            bx, by = int(cx) - R, int(cy) - R
            region = fg[by:by + 2 * R, bx:bx + 2 * R]
            if region.shape[:2] == big[:2 * R, :2 * R].shape[:2]:
                fg[by:by + 2 * R, bx:bx + 2 * R] = region * (1 - disc) + big[:2 * R, :2 * R] * disc
        out = bg * (1 - al) + fg * al
        for ov in self.overlays:
            if ov["type"] == "zzz":
                k = 1.0 if ov.get("lines") is None else max(_env(t, *windows[i]) for i in ov["lines"])
                if k > 0:
                    cx, cy = A @ np.array([ov["cx"] * S, ov["cy"] * S, 1], np.float32)
                    out = _draw_zzz(out, t, {**ov, "cx": cx / S, "cy": cy / S}, k, S, S)
        return np.clip(out, 0, 255).astype(np.uint8)


def render_layered(image: Path, mask: np.ndarray, sc: dict, windows, out_prefix: Path,
                   fps: int = 24, size: int = 1024) -> list[Path]:
    scene = LayeredScene(image, mask, sc.get("background", []), sc.get("animal", []),
                         sc.get("overlays", []), size)
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
