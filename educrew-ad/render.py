"""Render the 30s 9:16 EduCrew miniature-world ad.

Frames: AI-generated photoreal miniature dioramas in frames/scene1-5.png.
Logo: the supplied original logo (logo.png), only uniformly scaled, never redrawn or recoloured.
Text: exact supplied wording, composited during editing (not generated in the images).

Usage: python3 render.py [out.mp4]
"""
import math
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).parent
W, H, FPS = 1080, 1920, 30
SCENE = 5.0
TOTAL = 30.0
XFADE = 0.6  # seconds of crossfade centred on each cut

NAVY = (16, 42, 76)
TEAL = (0, 128, 138)
GOLD = (240, 176, 40)
WHITE = (255, 255, 255)

F = lambda w, s: ImageFont.truetype(str(ROOT / f"fonts/Montserrat-{w}.ttf"), s)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ---------- source images ----------
scenes = []
for i in range(1, 6):
    im = cv2.imread(str(ROOT / f"frames/scene{i}.png"), cv2.IMREAD_COLOR)
    # upscale once to cover 1080x1920 with headroom for camera moves
    scale = max(W / im.shape[1], H / im.shape[0])
    im = cv2.resize(im, None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4)
    scenes.append(cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32))

logo = Image.open(ROOT / "logo.png").convert("RGBA")


def logo_at(size):
    r = size / max(logo.size)
    return logo.resize((round(logo.size[0] * r), round(logo.size[1] * r)), Image.LANCZOS)


wm = logo_at(190)


# ---------- camera moves: (zoom, pan_x, pan_y) as function of local t in [0,1]
# pan values in [-1,1] = fraction of available slack
def cam(scene, t):
    e = ease(t)
    if scene == 0:  # zoom in, then glide left->right
        z = 1.0 + 0.16 * ease(t / 0.55)
        x = -0.7 + 1.4 * ease((t - 0.35) / 0.65)
        return z, x, 0.1
    if scene == 1:  # track left->right while pushing toward the workbook
        return 1.12 + 0.12 * e, -0.8 + 1.6 * e, 0.15 * e
    if scene == 2:  # pan left->right with gentle zoom-out reveal
        return 1.28 - 0.26 * e, -0.7 + 1.4 * e, -0.2 + 0.2 * e
    if scene == 3:  # zoom in on documents, then pull back
        z = 1.0 + 0.24 * math.sin(math.pi * e)
        return z, 0.35 * math.sin(math.pi * e), 0.45 * math.sin(math.pi * e)
    if scene == 4:  # right->left, then zoom out to full studio
        x = 0.8 - 1.6 * ease(t / 0.6)
        z = 1.25 - 0.23 * ease((t - 0.4) / 0.6)
        return z, x * (1 - 0.6 * ease((t - 0.5) / 0.5)), 0.0
    raise ValueError


def shot(idx, t):
    src = scenes[idx]
    z, px, py = cam(idx, t)
    sh, sw = src.shape[:2]
    cw, ch = W / z, H / z
    # crop window centre with slack
    cx = sw / 2 + px * (sw - cw) / 2
    cy = sh / 2 + py * (sh - ch) / 2
    s = W / cw
    M = np.float32([[s, 0, W / 2 - s * cx], [0, s, H / 2 - s * cy]])
    return cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


# ---------- text overlays ----------
CAPTIONS = [
    ["Big ideas begin with", "great academic design."],
    ["Mathematics | Curriculum |", "Concept-based Learning"],
    ["English Language Arts |", "Science | Learning Resources"],
    ["Standards Alignment |", "Assessment Design |", "Instructional Design"],
    ["Curriculum Development to", "LMS-ready Content"],
]


def caption_layer(lines):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    font = F(700, 58)
    lh = 76
    widths = [d.textlength(l, font=font) for l in lines]
    bw = max(widths) + 110
    bh = lh * len(lines) + 70
    x0 = (W - bw) / 2
    y0 = H - 330 - bh
    # soft shadow
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0, y0 + 10, x0 + bw, y0 + bh + 10], 34, fill=(0, 0, 0, 110))
    layer = Image.alpha_composite(layer, sh.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 34, fill=NAVY + (215,))
    d.rounded_rectangle([x0 + bw / 2 - 70, y0 + bh - 14, x0 + bw / 2 + 70, y0 + bh - 6], 4, fill=GOLD + (255,))
    for i, (l, w) in enumerate(zip(lines, widths)):
        d.text(((W - w) / 2, y0 + 30 + i * lh), l, font=font, fill=WHITE)
    return np.asarray(layer).astype(np.float32) / 255.0


cap_layers = [caption_layer(c) for c in CAPTIONS]


def overlay(base, layer, alpha, dy=0):
    if alpha <= 0:
        return base
    if dy:
        layer = np.roll(layer, int(dy), axis=0)
    a = layer[..., 3:4] * alpha
    return base * (1 - a) + layer[..., :3] * 255 * a


def wm_layer():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(wm, (W - wm.size[0] - 40, 60))
    return np.asarray(layer).astype(np.float32) / 255.0


WM = wm_layer()


# ---------- end card ----------
def end_card_static():
    # clean brand background: soft white with teal/navy wave at bottom, gold hairline
    bg = Image.new("RGB", (W, H), (248, 250, 252))
    g = np.asarray(bg).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.38) / H) ** 2)
    g -= (np.clip(r, 0, 1) * 22)[..., None]
    bg = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    wave = [(x, H - 150 + 40 * math.sin(x / W * math.pi * 1.4 + 0.6)) for x in range(0, W + 1, 6)]
    d.polygon(wave + [(W, H), (0, H)], fill=NAVY)
    wave2 = [(x, H - 175 + 40 * math.sin(x / W * math.pi * 1.4 + 0.6)) for x in range(0, W + 1, 6)]
    d.line(wave2, fill=GOLD, width=8)
    wave3 = [(x, H - 215 + 34 * math.sin(x / W * math.pi * 1.2 + 1.4)) for x in range(0, W + 1, 6)]
    d.line(wave3, fill=TEAL, width=5)
    return np.asarray(bg.convert("RGB")).astype(np.float32)


END_BG = end_card_static()
BIG = logo_at(720)


def text_block():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = 1180
    head = "Let's Build Better Learning Experiences."
    f1 = F(700, 46)
    d.text(((W - d.textlength(head, font=f1)) / 2, y), head, font=f1, fill=NAVY)
    y += 82
    d.rounded_rectangle([W / 2 - 80, y, W / 2 + 80, y + 6], 3, fill=GOLD)
    y += 40
    f2 = F(600, 40)
    for l in [
        "Call / WhatsApp: +91 9967421713",
        "Email: aaishayusuf.l@gmail.com",
        "Website: www.educrew.in",
        "@educrew.academicsolution",
    ]:
        col = TEAL if l.startswith("@") else NAVY
        d.text(((W - d.textlength(l, font=f2)) / 2, y), l, font=f2, fill=col)
        y += 66
    return np.asarray(layer).astype(np.float32) / 255.0


END_TEXT = text_block()


def logo_layer(scale):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lg = BIG if scale >= 0.999 else BIG.resize((round(BIG.size[0] * scale), round(BIG.size[1] * scale)), Image.LANCZOS)
    cy = 120 + BIG.size[1] / 2
    layer.alpha_composite(lg, (round((W - lg.size[0]) / 2), round(cy - lg.size[1] / 2)))
    return np.asarray(layer).astype(np.float32) / 255.0


def end_frame(t, prev):
    """t in [0,5]: miniature studio pulls back & fades into brand background, logo, then contact details."""
    # 0-1.4s: last studio pulls back, blurs, and dissolves into the clean background
    a = ease(t / 1.4)
    if a < 1:
        sm = cv2.GaussianBlur(prev, (0, 0), 1 + 18 * a)
        z = 1 - 0.08 * a
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
        sm = cv2.warpAffine(sm, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        frame = sm * (1 - a) + END_BG * a
    else:
        frame = END_BG.copy()
    la = ease((t - 0.9) / 0.9)
    if la > 0:
        frame = overlay(frame, logo_layer(0.9 + 0.1 * ease((t - 0.9) / 1.4)), la)
    ta = ease((t - 2.0) / 0.8)
    frame = overlay(frame, END_TEXT, ta, dy=(1 - ta) * 30)
    return frame, la


def main(out):
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE,
    )
    n = int(TOTAL * FPS)
    last_scene5 = None
    for f in range(n):
        T = f / FPS
        idx = min(int(T // SCENE), 5)
        lt = T - idx * SCENE
        if idx < 5:
            # extend each shot slightly beyond its 5s so crossfades have material
            frame = shot(idx, (lt + XFADE / 2) / (SCENE + XFADE))
            if idx < 4 and lt > SCENE - XFADE / 2:
                k = ease((lt - (SCENE - XFADE / 2)) / XFADE)
                nxt = shot(idx + 1, (lt - SCENE + XFADE / 2) / (SCENE + XFADE))
                frame = frame * (1 - k) + nxt * k
            if idx > 0 and lt < XFADE / 2:
                k = ease((lt + XFADE / 2) / XFADE)
                prv = shot(idx - 1, (lt + SCENE + XFADE / 2) / (SCENE + XFADE))
                frame = prv * (1 - k) + frame * k
            if idx == 4:
                last_scene5 = frame
            # caption: fade in 0.5-1.0s, out 4.3-4.8s
            ca = ease((lt - 0.45) / 0.5) * (1 - ease((lt - 4.25) / 0.45))
            frame = overlay(frame, cap_layers[idx], ca, dy=(1 - ca) * 24)
            frame = overlay(frame, WM, 0.95)
        else:
            frame, la = end_frame(lt, last_scene5)
            # small watermark stays until the large logo has taken over
            frame = overlay(frame, WM, 0.95 * (1 - la))
        ff.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "EduCrew_Miniature_Ad_30s_9x16.mp4")
