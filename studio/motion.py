"""Animate a scene without an AI video model: camera moves, a living sticker, and a map.

Each shot is built from layers, so every part moves on its own:
  background  -> camera move (push in, pull out, pan, tilt) with smooth easing
  sticker     -> pops in, gently bobs; animated GIF stickers play their frames
  map card    -> slides in, the map flies from the whole world to where the animal lives,
                 pins drop in and pulse
  logo, title -> logo stays put; the title pops in

shots.yaml fields used (all optional):
  camera: {move: push_in|pull_out|pan_left|pan_right|tilt_up|tilt_down|still,
           amount: 0.15, focus_x: 0.5, dim: 0.0}
  map:    {label: "African savannas", pins: [[lat, lon], ...],
           region: [lon_min, lon_max, lat_min, lat_max]}   # omit region = whole world
"""

from __future__ import annotations

import json
import math
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from .compose import _font, _round_logo, _shadow, _title

WORLD = Path(__file__).parent / "data" / "world.json"
INK = (58, 36, 84)          # outline colour, matches the sticker outlines
OCEAN = (186, 225, 242)
LAND = (206, 234, 176)
PIN = (235, 76, 96)


# ---------- easing ----------
def ease(t: float) -> float:            # smooth in-out
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ease_out_back(t: float) -> float:   # overshoot, for pop-ins
    t = min(max(t, 0.0), 1.0)
    c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


# ---------- camera ----------
def camera_box(t: float, move: str, amount: float, focus_x: float,
               src: tuple[int, int], out: tuple[int, int]) -> tuple[float, float, float, float]:
    """Return the source rectangle to show at time t (0..1)."""
    sw, sh = src
    ow, oh = out
    base = min(sw / ow, sh / oh)          # source pixels per output pixel at zoom 1
    e = ease(t)
    zoom, fx, fy = 1.0, focus_x, 0.5
    if move == "push_in":
        zoom = 1 + amount * e
    elif move == "pull_out":
        zoom = 1 + amount * (1 - e)
    elif move in ("pan_left", "pan_right"):
        zoom = 1 + amount * 0.3
        span = amount * 2
        fx = focus_x + (span / 2) * (2 * e - 1) * (1 if move == "pan_right" else -1)
    elif move in ("tilt_up", "tilt_down"):
        zoom = 1 + max(amount, 0.2)
        fy = 0.5 + 0.5 * (2 * e - 1) * (1 if move == "tilt_down" else -1)
        fy = 0.5 + (fy - 0.5) * 0.9
    w, h = ow * base / zoom, oh * base / zoom
    x = (sw - w) * min(max(fx, 0), 1)
    y = (sh - h) * min(max(fy, 0), 1)
    return (x, y, x + w, y + h)


# ---------- map ----------
@lru_cache(maxsize=1)
def world_map(width: int = 3000) -> Image.Image:
    """Equirectangular cartoon world map, -180..180 lon, 90..-90 lat."""
    h = width // 2
    img = Image.new("RGB", (width, h), OCEAN)
    d = ImageDraw.Draw(img)
    rings = json.loads(WORLD.read_text())["rings"]
    for ring in rings:
        pts = [((lon + 180) / 360 * width, (90 - lat) / 180 * h) for lon, lat in ring]
        if len(pts) > 2:
            d.polygon(pts, fill=LAND, outline=INK, width=max(2, width // 900))
    return img


def _lonlat_to_px(lon: float, lat: float, w: int) -> tuple[float, float]:
    return (lon + 180) / 360 * w, (90 - lat) / 180 * (w // 2)


def _fit_aspect(box, aspect, w):
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    if bw / bh < aspect:
        nw = bh * aspect
        x0 -= (nw - bw) / 2
        x1 = x0 + nw
    else:
        nh = bw / aspect
        y0 -= (nh - bh) / 2
        y1 = y0 + nh
    return (x0, y0, x1, y1)


def map_card(t_sec: float, spec: dict, size: tuple[int, int], duration: float,
             fly_start: float = 0.9, pin_start: float = 2.0) -> Image.Image:
    cw, ch = size
    band = int(ch * 0.24)
    mh = ch - band
    world = world_map()
    W = world.width
    aspect = cw / mh
    full = _fit_aspect((0, _lonlat_to_px(0, 80, W)[1], W, _lonlat_to_px(0, -58, W)[1]), aspect, W)
    if spec.get("region"):
        lo0, lo1, la0, la1 = spec["region"]
        x0, y0 = _lonlat_to_px(lo0, la1, W)
        x1, y1 = _lonlat_to_px(lo1, la0, W)
        target = _fit_aspect((x0, y0, x1, y1), aspect, W)
    else:
        target = _fit_aspect((full[0] + W * 0.04, full[1] + W * 0.02,
                              full[2] - W * 0.04, full[3] - W * 0.02), aspect, W)
    # fly from the whole world to the region between 0.9 s and 2.4 s
    k = ease((t_sec - fly_start) / 1.5)
    box = tuple(a + (b - a) * k for a, b in zip(full, target))
    card = world.transform((cw, mh), Image.EXTENT, box, Image.BILINEAR,
                           fillcolor=OCEAN).convert("RGBA")
    d = ImageDraw.Draw(card)
    sx, sy = cw / (box[2] - box[0]), mh / (box[3] - box[1])
    r = max(8, cw // 34)
    for i, (lat, lon) in enumerate(spec.get("pins", [])):
        px, py = _lonlat_to_px(lon, lat, W)
        px, py = (px - box[0]) * sx, (py - box[1]) * sy
        start = pin_start + i * 0.18                # pins drop one after another
        p = (t_sec - start) / 0.45
        if p <= 0:
            continue
        drop = (1 - ease_out_back(p)) * r * 4
        cy = py - r * 1.6 - drop
        pulse = ((t_sec - start) % 1.4) / 1.4        # expanding ring
        if p >= 1:
            rr = r * (0.8 + 1.6 * pulse)
            a = int(160 * (1 - pulse))
            ring = Image.new("RGBA", card.size, (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse((px - rr, py - rr * 0.5, px + rr, py + rr * 0.5),
                                         outline=PIN + (a,), width=max(2, r // 3))
            card.alpha_composite(ring)
        d.polygon([(px, py), (px - r * 0.75, cy + r * 0.4), (px + r * 0.75, cy + r * 0.4)],
                  fill=PIN, outline=INK)
        d.ellipse((px - r, cy - r, px + r, cy + r), fill=PIN, outline=INK, width=max(2, r // 4))
        d.ellipse((px - r * 0.4, cy - r * 0.4, px + r * 0.4, cy + r * 0.4), fill="white")
    out = Image.new("RGBA", (cw, ch), (255, 255, 255, 255))
    out.paste(card, (0, 0))
    od = ImageDraw.Draw(out)
    label = spec.get("label", "")
    fs = int(band * 0.55)
    while fs > 14 and od.textlength(label, font=_font(fs)) > cw * 0.92:
        fs -= 1
    font = _font(fs)
    tw = od.textlength(label, font=font)
    od.text(((cw - tw) / 2, mh + (band - fs) * 0.42), label, font=font, fill=INK)
    od.line((0, mh, cw, mh), fill=INK, width=3)
    mask = Image.new("L", (cw, ch), 0)
    rad = cw // 14
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1), rad, fill=255)
    out.putalpha(mask)
    border = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle((2, 2, cw - 3, ch - 3), rad, outline=INK,
                                             width=max(4, cw // 90))
    out.alpha_composite(border)
    return out


# ---------- sticker ----------
def load_sticker_frames(path_png: Path, crop=None) -> tuple[list[Image.Image], list[float]]:
    gif = path_png.with_suffix(".gif")
    frames, durs = [], []
    if gif.exists():
        g = Image.open(gif)
        for i in range(getattr(g, "n_frames", 1)):
            g.seek(i)
            frames.append(g.convert("RGBA"))
            durs.append(max(g.info.get("duration", 120), 60) / 1000)
    else:
        frames, durs = [Image.open(path_png).convert("RGBA")], [1.0]
    if crop:
        l, t, r, b = crop
        frames = [f.crop((int(l * f.width), int(t * f.height), int(r * f.width),
                          int(b * f.height))) for f in frames]
    box = frames[0].split()[3].getbbox()
    for f in frames[1:]:
        b2 = f.split()[3].getbbox()
        if b2:
            box = (min(box[0], b2[0]), min(box[1], b2[1]), max(box[2], b2[2]), max(box[3], b2[3]))
    return [f.crop(box) for f in frames], durs


def _with_shadow(st: Image.Image) -> Image.Image:
    pad = 40
    layer = Image.new("RGBA", (st.width + pad * 2, st.height + pad * 2), (0, 0, 0, 0))
    layer.paste(st, (pad, pad), st)
    return Image.alpha_composite(_shadow(layer), layer)


# ---------- render one shot ----------
def _caption_layer(text: str, width: int, size: int) -> Image.Image:
    """Bold white caption with a purple outline, wrapped to `width`."""
    font = _font(size)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if probe.textlength(test, font=font) > width and line:
            lines.append(line)
            line = word
        else:
            line = test
    lines.append(line)
    lh = int(size * 1.18)
    img = Image.new("RGBA", (width, lh * len(lines) + size // 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=font)
        d.text(((width - tw) / 2, i * lh), ln, font=font, fill="white",
               stroke_width=max(3, size // 8), stroke_fill=INK)
    return img


def _scaled(layer: Image.Image, p: float) -> Image.Image:
    return layer.resize((max(1, int(layer.width * p)), max(1, int(layer.height * p))),
                        Image.BILINEAR)


def render_shot(bg_path: Path, out_path: Path, *, size: tuple[int, int], fps: int,
                duration: float, sticker: Path | None = None, side: str = "left",
                scale: float = 0.36, crop=None, logo: Path | None = None,
                logo_scale: float = 0.2, title: str | None = None,
                camera: dict | None = None, map_spec: dict | None = None,
                caption: str | None = None, still_path: Path | None = None) -> Path:
    """Vertical layout: the whole square picture sits in the middle (never cropped hard,
    never covered); the band above holds the logo + map card or title, the band below
    holds the caption and, when she speaks to camera, the host."""
    W, H = size
    camera = camera or {}
    move = camera.get("move", "push_in")
    amount = min(float(camera.get("amount", 0.05)), 0.08)   # gentle: keep the animal whole
    focus_x = float(camera.get("focus_x", 0.5))
    dim = float(camera.get("dim", 0.0))

    P = W                                   # picture panel: full width, square
    top = int((H - P) * 0.47)               # band above the picture
    bottom_y = top + P                      # band below starts here

    src = Image.open(bg_path).convert("RGB")
    head = int(P * (1 + amount) + 2)
    panel_src = src.resize((head, round(src.height * head / src.width)), Image.LANCZOS)

    # bands: blurred, darkened copy of the same picture
    cover = max(W / src.width, H / src.height)
    bands = src.resize((int(src.width * cover) + 1, int(src.height * cover) + 1), Image.LANCZOS)
    bands = bands.crop(((bands.width - W) // 2, (bands.height - H) // 2,
                        (bands.width - W) // 2 + W, (bands.height - H) // 2 + H))
    bands = ImageEnhance.Brightness(bands.filter(ImageFilter.GaussianBlur(40))).enhance(0.55)
    bands = bands.convert("RGBA")
    edge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edge)
    for k in range(18):                     # soft shadow above and below the picture
        a = int(70 * (1 - k / 18))
        ed.line((0, top - k, W, top - k), fill=(20, 8, 35, a))
        ed.line((0, bottom_y + k, W, bottom_y + k), fill=(20, 8, 35, a))
    bands.alpha_composite(edge)

    frames, durs = [], []
    if sticker:
        raw, durs = load_sticker_frames(sticker, crop)
        sw = int(W * scale)
        frames = [_with_shadow(f.resize((sw, round(f.height * sw / f.width)), Image.LANCZOS))
                  for f in raw]
    m = int(W * 0.03)
    logo_size = min(int(W * logo_scale), top - 2 * m)
    logo_img = _round_logo(logo, logo_size) if logo else None
    right_x = m * 2 + logo_size if logo_img else m        # area right of the logo
    right_w = W - right_x - m

    title_layer = _caption_layer(title, right_w, int(top * 0.24)) if title else None
    card_size = (right_w, top - 2 * m)

    host_w = frames[0].width - 80 if frames else 0
    cap_x = (m + host_w) if frames and side == "left" else m
    cap_w = W - cap_x - m - (host_w if frames and side == "right" else 0)
    band_h = H - bottom_y
    caption_layer = _caption_layer(caption, cap_w, int(band_h * 0.17)) if caption else None

    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = int(round(duration * fps))
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium",
         "-crf", "19", "-pix_fmt", "yuv420p", str(out_path)],
        stdin=subprocess.PIPE)
    total_gif = sum(durs) if durs else 1
    for i in range(n):
        ts = i / fps
        t = i / max(n - 1, 1)
        frame = bands.copy()
        box = camera_box(t, move, amount, focus_x, panel_src.size, (P, P))
        frame.paste(panel_src.transform((P, P), Image.EXTENT, box, Image.BILINEAR), (0, top))
        if dim:
            frame = ImageEnhance.Brightness(frame).enhance(1 - dim * ease(t))

        if logo_img:
            frame.alpha_composite(logo_img, (m, (top - logo_size) // 2))

        if map_spec:
            slide = ease_out_back((ts - 0.3) / 0.5)
            if slide > 0:
                card = map_card(ts, map_spec, card_size, duration)
                mx = int(right_x + (1 - slide) * (W - right_x + m))
                frame.alpha_composite(_with_shadow(card), (mx - 40, m - 40))

        if title_layer is not None:
            p = ease_out_back((ts - 0.15) / 0.5)
            if p > 0:
                tl = _scaled(title_layer, p)
                frame.alpha_composite(tl, (right_x + (right_w - tl.width) // 2,
                                           (top - tl.height) // 2))

        if caption_layer is not None:
            p = ease_out_back((ts - 0.15) / 0.35)
            if p > 0:
                cl = _scaled(caption_layer, min(p, 1.08))
                frame.alpha_composite(cl, (cap_x + (cap_w - cl.width) // 2,
                                           bottom_y + (band_h - cl.height) // 2))

        if frames:
            k, acc = 0, ts % total_gif
            while k < len(durs) - 1 and acc >= durs[k]:
                acc -= durs[k]
                k += 1
            st = frames[k]
            pop = ease_out_back(ts / 0.45)
            s = max(0.05, 0.6 + 0.4 * pop) * (1 + 0.01 * math.sin(ts * 2.6))
            st_s = _scaled(st, s)
            base_x = m - 40 if side == "left" else W - st.width - m + 40
            x = base_x + (st.width - st_s.width) // 2
            y = int(H - st_s.height + 40 - m + math.sin(ts * 2.6) * H * 0.003)
            frame.alpha_composite(st_s, (x, max(y, 0)))

        if still_path is not None and i == int(n * 0.7):
            still_path.parent.mkdir(parents=True, exist_ok=True)
            frame.convert("RGB").save(still_path)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError(f"ffmpeg failed for {out_path}")
    return out_path
