"""Math Hacks shorts: animated maths board + free Kokoro voice, all rendered locally.

Same sync rule as studio/short.py: the voice is the master clock. Each line has its own audio
file; cuts, board animations and captions follow the measured speech.

Per line in shots.yaml:
  board: ["{y:8%} of {p:25}", ...]   rows that pop in one after another while the line plays
  swap:  {template: "{a}% of {b}", a: "8", b: "25"}   the two numbers fly to each other's place
Colour markup: {y:..} yellow, {p:..} pink, {g:..} green, {b:..} blue.
"""

from __future__ import annotations

import math
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .compose import _font, _round_logo
from .motion import INK, _with_shadow, ease, ease_out_back, load_sticker_frames
from .short import (SR, Line, Shot, _words_with_weights, build_timeline, caption_image,
                    load_audio, music_bed, sfx_pop, sfx_whoosh, trim_silence)

COLORS = {"y": (255, 196, 0), "p": (236, 72, 153), "g": (34, 170, 110), "b": (59, 130, 246)}
BOARD_BG = (255, 253, 246)
GRID = (226, 232, 244)
BG_TOP, BG_BOTTOM = (88, 60, 150), (40, 28, 84)


def parse(markup: str) -> list[tuple[str, tuple]]:
    parts, pos = [], 0
    for m in re.finditer(r"\{([ypgb]):([^}]*)\}", markup):
        if m.start() > pos:
            parts.append((markup[pos:m.start()], INK))
        parts.append((m.group(2), COLORS[m.group(1)]))
        pos = m.end()
    if pos < len(markup):
        parts.append((markup[pos:], INK))
    return parts


def row_image(markup: str, size: int, max_w: int) -> Image.Image:
    parts = parse(markup)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    while True:
        font = _font(size)
        w = sum(probe.textlength(t, font=font) for t, _ in parts)
        if w <= max_w or size < 30:
            break
        size -= 4
    img = Image.new("RGBA", (int(w) + 20, int(size * 1.35)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 10
    for t, col in parts:
        d.text((x, 0), t, font=font, fill=col)
        x += probe.textlength(t, font=font)
    return img


def background(W: int, H: int) -> Image.Image:
    g = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array(BG_TOP), np.array(BG_BOTTOM)
    arr = (top * (1 - g) + bot * g).repeat(W, axis=1)
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")


class Floaters:
    """Faint maths symbols drifting upward behind everything (keeps the frame alive)."""
    SYMBOLS = ["%", "+", "×", "÷", "=", "½", "¼", "π", "√", "7", "3", "9"]

    def __init__(self, W, H, n=22):
        rng = np.random.default_rng(11)
        self.items = []
        for i in range(n):
            size = int(rng.uniform(50, 120))
            img = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
            ImageDraw.Draw(img).text((size * 0.3, size * 0.2), self.SYMBOLS[i % len(self.SYMBOLS)],
                                     font=_font(size), fill=(255, 255, 255, int(rng.uniform(25, 55))))
            self.items.append((img, rng.uniform(0, W), rng.uniform(0, H), rng.uniform(25, 60),
                               rng.uniform(0, 6.28)))
        self.W, self.H = W, H

    def draw(self, frame, t):
        for img, x, y, spd, ph in self.items:
            yy = (y - t * spd) % (self.H + 200) - 100
            xx = x + math.sin(t * 0.6 + ph) * 18
            frame.alpha_composite(img, (int(xx), int(yy)))


def board_card(w, h) -> Image.Image:
    card = Image.new("RGBA", (w, h), BOARD_BG + (255,))
    d = ImageDraw.Draw(card)
    step = w // 14
    for x in range(0, w, step):
        d.line((x, 0, x, h), fill=GRID, width=2)
    for y in range(0, h, step):
        d.line((0, y, w, y), fill=GRID, width=2)
    d.line((step * 1.5, 0, step * 1.5, h), fill=(250, 170, 170), width=4)   # notebook margin
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), w // 18, fill=255)
    card.putalpha(mask)
    border = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle((3, 3, w - 4, h - 4), w // 18, outline=INK, width=8)
    card.alpha_composite(border)
    return card


# ---------------------------------------------------------------- lively extras
def stage_card(w: int, h: int, t: float) -> Image.Image:
    """Game-show stage: dark backdrop, sweeping spotlights, curtains, glowing floor."""
    yy = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array([48, 22, 92]) * (1 - yy) + np.array([22, 10, 48]) * yy).repeat(w, axis=1)
    img = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    light = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(light)
    for k, (base_x, col) in enumerate([(0.2, (255, 220, 120)), (0.8, (160, 220, 255)), (0.5, (255, 160, 220))]):
        ang = math.sin(t * 0.9 + k * 2.1) * 0.35
        bx, by = w * base_x, -40
        tx = w * 0.5 + math.sin(ang) * w * 0.8
        ld.polygon([(bx, by), (tx - w * 0.18, h), (tx + w * 0.18, h)], fill=col + (38,))
    img.alpha_composite(light.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(img)
    d.ellipse((-w * 0.2, h * 0.82, w * 1.2, h * 1.25), fill=(90, 50, 150))
    for side in (0, 1):   # curtains with a gentle sway
        sway = math.sin(t * 1.3 + side) * 6
        x0 = 0 if side == 0 else w - w * 0.09
        for j in range(4):
            xx = x0 + j * w * 0.022 + sway
            d.rounded_rectangle((xx, -20, xx + w * 0.03, h + 20), 12,
                                fill=(200, 40, 70) if j % 2 == 0 else (170, 30, 60))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), w // 18, fill=255)
    img.putalpha(mask)
    ImageDraw.Draw(img).rounded_rectangle((3, 3, w - 4, h - 4), w // 18, outline=INK, width=8)
    return img


class Confetti:
    def __init__(self, W, n=140, seed=5):
        rng = np.random.default_rng(seed)
        self.p = [(rng.uniform(0, W), rng.uniform(-300, -20), rng.uniform(-120, 120), rng.uniform(380, 720),
                   rng.uniform(0, 6.28), tuple(int(c) for c in rng.choice(
                       [[255, 196, 0], [236, 72, 153], [34, 170, 110], [59, 130, 246], [255, 255, 255]])),
                   rng.uniform(10, 22)) for _ in range(n)]

    def draw(self, frame, t):
        if t < 0 or t > 3.0:
            return
        d = ImageDraw.Draw(frame)
        for x, y, vx, vy, ph, col, sz in self.p:
            xx = x + vx * t + math.sin(t * 6 + ph) * 25
            yy = y + vy * t
            w = sz * abs(math.cos(t * 8 + ph)) + 3
            d.rectangle((xx, yy, xx + w, yy + sz * 0.6), fill=col)


def promo_frame(frame, t, dur, assets, W, H):
    """EduCrew brand end card (added to every video)."""
    logo, sticker, texts = assets["logo"], assets["sticker"], assets["texts"]
    p = ease_out_back(t / 0.6)
    if p > 0:
        size = max(1, int(logo.width * min(p, 1.1)))
        lg = logo.resize((size, size)).rotate(math.sin(t * 2) * 3, resample=Image.BICUBIC)
        frame.alpha_composite(lg, ((W - lg.width) // 2, int(H * 0.07) + (logo.height - size) // 2))
    y = int(H * 0.07) + logo.height + 30
    for i, img in enumerate(texts):
        q = ease_out_back((t - 0.5 - i * 0.35) / 0.4)
        if q > 0:
            im = img if q == 1 else img.resize((max(1, int(img.width * q)), max(1, int(img.height * q))))
            frame.alpha_composite(im, ((W - im.width) // 2, y + (img.height - im.height) // 2))
        y += img.height + 18
    if sticker is not None:
        q = ease_out_back((t - 0.8) / 0.5)
        if q > 0:
            st = sticker.resize((max(1, int(sticker.width * q)), max(1, int(sticker.height * q))))
            frame.alpha_composite(st, ((W - st.width) // 2, int(H - st.height - H * 0.03 + math.sin(t * 2.6) * 6)))


def render_mathshort(project, ep_id: str, spec: dict) -> Path:
    root = project.root
    base = project.output_dir / ep_id
    W, H = project.resolution(ep_id)
    fps = project.fps(ep_id)
    lines_dir = base / "lines"
    brand = project.style.get("brand", {})

    shots = []
    for s in spec["shots"]:
        ls = []
        for l in s["lines"]:
            f = next(p for p in (lines_dir / f"{l['id']}.wav", lines_dir / f"{l['id']}.mp3")
                     if p.exists())
            ln = Line(l["id"], l["line"], trim_silence(load_audio(f)))
            ln.spec = l
            ls.append(ln)
        shots.append(Shot(s["id"], s, ls))
    build_timeline(shots, float(spec.get("target_seconds", 45)))
    total = shots[-1].end

    m = int(W * 0.04)
    top_h = int(H * 0.16)
    card_y, card_h = top_h + m, int(H * 0.52)
    card_w = W - 2 * m
    cap_y = card_y + card_h + m
    bg = background(W, H)
    floaters = Floaters(W, H)
    card = _with_shadow(board_card(card_w, card_h))
    logo = _round_logo(root / brand["logo"], int(top_h * 0.8)) if brand.get("logo") else None
    title_img = row_image("{y:" + spec.get("series_title", "") + "}", int(top_h * 0.36), W - 3 * m - top_h)
    ep_img = row_image(spec.get("title", ""), int(top_h * 0.22), W - 3 * m - top_h)
    ep_chip = Image.new("RGBA", (ep_img.width + 30, ep_img.height + 10), (255, 255, 255, 235))
    ep_chip.alpha_composite(ep_img, (15, 5))

    row_size = int(card_h * 0.15)
    max_row_w = card_w - 2 * int(card_w * 0.12)
    for s in shots:
        s.sticker = []
        if s.spec.get("sticker"):
            raw, durs = load_sticker_frames(root / "brand" / "stickers" / f"{s.spec['sticker']}.png")
            sw = int(W * 0.30)
            s.sticker = [_with_shadow(f.resize((sw, round(f.height * sw / f.width)), Image.LANCZOS))
                         for f in raw]
            s.sticker_durs = durs
        for l in s.lines:
            l.rows = [row_image(r, row_size, max_row_w) for r in l.spec.get("board", [])]
            if l.spec.get("swap"):
                sw_ = l.spec["swap"]
                a, b = sw_["a"], sw_["b"]
                tmpl = sw_["template"]
                l.swap_parts = (tmpl, a, b)

        for l in s.lines:
            l.sticker = []
            if l.spec.get("sticker"):
                raw, durs = load_sticker_frames(root / "brand" / "stickers" / f"{l.spec['sticker']}.png")
                sw = int(W * 0.30)
                l.sticker = [_with_shadow(f.resize((sw, round(f.height * sw / f.width)), Image.LANCZOS))
                             for f in raw]
                l.sticker_durs = durs
    promo_assets = None
    if any(s.spec.get("promo") for s in shots):
        pc = brand.get("promo", {})
        texts = [row_image("{y:" + pc.get("name", "EduCrew Academic Solutions") + "}", 78, W - 2 * m)]
        for t_ in pc.get("lines", []):
            texts.append(row_image(t_, 54, W - 2 * m))
        if pc.get("cta"):
            texts.append(row_image("{g:" + pc["cta"] + "}", 72, W - 2 * m))
        chip_bg = []
        for img in texts:
            chip = Image.new("RGBA", (img.width + 40, img.height + 16), (255, 255, 255, 235))
            mask = Image.new("L", chip.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, chip.width - 1, chip.height - 1), 24, fill=255)
            chip.putalpha(mask)
            chip.alpha_composite(img, (20, 8))
            chip_bg.append(chip)
        st = None
        if pc.get("sticker"):
            raw, _ = load_sticker_frames(root / "brand" / "stickers" / f"{pc['sticker']}.png")
            sw = int(W * 0.42)
            st = _with_shadow(raw[0].resize((sw, round(raw[0].height * sw / raw[0].width)), Image.LANCZOS))
        promo_assets = {"logo": _round_logo(root / brand["logo"], int(W * 0.42)), "sticker": st,
                        "texts": chip_bg}
    confetti = Confetti(W)
    from .scenes import doors_scene

    all_lines = [l for s in shots for l in s.lines]
    silent = base / f"{ep_id}_video.mp4"
    out = base / f"{ep_id}.mp4"
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium",
         "-crf", "18", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    cap_cache = {}
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    pops = []          # times for pop sfx
    for fi in range(int(round(total * fps))):
        ts = fi / fps
        frame = bg.copy()
        floaters.draw(frame, ts)
        # header
        if logo:
            frame.alpha_composite(logo, (m, (top_h - logo.height) // 2 + m // 2))
        hx = m * 2 + (logo.width if logo else 0)
        frame.alpha_composite(title_img, (hx, int(top_h * 0.22)))
        frame.alpha_composite(ep_chip, (hx + 6, int(top_h * 0.22) + title_img.height + 4))
        si = next(i for i, s_ in enumerate(shots) if ts < s_.end or i == len(shots) - 1)
        if shots[si].spec.get("promo"):
            frame = bg.copy()
            floaters.draw(frame, ts)
            promo_frame(frame, ts - shots[si].start, shots[si].end - shots[si].start, promo_assets, W, H)
            spoken = next((l for l in shots[si].lines if l.start - 0.05 <= ts < l.start + l.dur + 0.25), None)
            proc.stdin.write(frame.convert("RGB").tobytes())
            continue
        cur = None
        for l in all_lines:
            if ts >= l.start - 0.12:
                cur = l
        if cur is not None and cur.spec.get("doors") is not None:
            lt0 = ts - cur.start
            stage = stage_card(card_w, card_h, ts)
            doors_scene(stage, cur.spec["doors"], lt0, cur.dur)
            # camera punch-in on key moments
            if cur.spec.get("punch"):
                k = math.exp(-max(lt0 - 0.1, 0) * 3) * (lt0 > 0.1)
                sc = 1 + 0.07 * k
                stage = stage.resize((int(card_w * sc), int(card_h * sc)))
            sh = _with_shadow(stage)
            frame.alpha_composite(sh, (m - 40 - (stage.width - card_w) // 2,
                                       card_y - 40 - (stage.height - card_h) // 2))
            if cur.spec.get("confetti"):
                confetti.draw(frame, lt0 - float(cur.spec.get("confetti_at", 0.5)) * cur.dur)
        else:
            frame.alpha_composite(card, (m - 40, card_y - 40))

        # which line's board is showing (hold the last one until the next line starts)
        cur = None
        for l in all_lines:
            if ts >= l.start - 0.12:
                cur = l
        if cur is not None:
            lt = ts - cur.start
            dur = cur.dur
            if getattr(cur, "swap_parts", None):
                tmpl, a, b = cur.swap_parts
                font = _font(int(row_size * 1.25))
                pre, mid, post = re.split(r"\{a\}|\{b\}", tmpl)
                # positions of a and b in "a<mid>b"
                wa, wb, wm = (probe.textlength(a, font=font), probe.textlength(b, font=font),
                              probe.textlength(pre + mid.split("{")[0], font=font))
                text_a, text_b = a + pre.strip() if False else a, b
                line1 = f"{a}{mid}{b}"
                total_w = probe.textlength(f"{a}{mid}{b}", font=font)
                x0 = (W - total_w) / 2
                y0 = card_y + card_h * 0.32
                k = ease((lt - dur * 0.35) / 0.9)      # swap happens mid-line
                pos_a0, pos_b0 = x0, x0 + probe.textlength(a + mid, font=font)
                pos_b1, pos_a1 = x0, x0 + probe.textlength(b + mid, font=font)
                layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                d = ImageDraw.Draw(layer)
                # the middle text ("% of ") fades between its two positions
                mid_x0 = pos_a0 + probe.textlength(a, font=font)
                mid_x1 = pos_b1 + probe.textlength(b, font=font)
                d.text((mid_x0 + (mid_x1 - mid_x0) * k, y0), mid, font=font, fill=INK)
                arc = math.sin(k * math.pi) * row_size * 0.9
                d.text((pos_a0 + (pos_a1 - pos_a0) * k, y0 - arc), a, font=font, fill=COLORS["y"])
                d.text((pos_b0 + (pos_b1 - pos_b0) * k, y0 + arc), b, font=font, fill=COLORS["p"])
                if k >= 1:
                    eq = row_image("{g:same answer!}", int(row_size * 0.8), max_row_w)
                    p = ease_out_back((lt - dur * 0.35 - 1.0) / 0.4)
                    if p > 0:
                        e2 = eq.resize((max(1, int(eq.width * p)), max(1, int(eq.height * p))))
                        layer.alpha_composite(e2, ((W - e2.width) // 2, int(y0 + row_size * 1.9)))
                frame.alpha_composite(layer)
            elif cur.rows:
                n = len(cur.rows)
                gap = int(row_size * 0.35)
                total_h = sum(r.height for r in cur.rows) + gap * (n - 1)
                y = card_y + (card_h - total_h) // 2
                for i, r in enumerate(cur.rows):
                    appear = (dur * 0.85) * i / max(n, 1)
                    p = ease_out_back((lt - appear) / 0.35)
                    if p > 0:
                        r2 = r if p == 1 else r.resize((max(1, int(r.width * p)), max(1, int(r.height * p))))
                        frame.alpha_composite(r2, ((W - r2.width) // 2, y + (r.height - r2.height) // 2))
                    y += r.height + gap

        # host sticker (opening and sign-off only)
        si = next(i for i, s in enumerate(shots) if ts < s.end or i == len(shots) - 1)
        s = shots[si]
        cap_x, cap_w = m, W - 2 * m
        line_now = next((l for l in s.lines if l.start - 0.12 <= ts), None)
        for l in s.lines:
            if ts >= l.start - 0.12:
                line_now = l
        if line_now is not None and getattr(line_now, "sticker", None):
            s = type("S", (), {"sticker": line_now.sticker, "sticker_durs": line_now.sticker_durs,
                               "start": line_now.start, "end": s.end})()
        if s.sticker:
            lt = ts - s.start
            tot = sum(s.sticker_durs)
            j, acc = 0, lt % tot
            while j < len(s.sticker_durs) - 1 and acc >= s.sticker_durs[j]:
                acc -= s.sticker_durs[j]
                j += 1
            st = s.sticker[j]
            sc = 0.6 + 0.4 * max(0.05, ease_out_back(lt / 0.4))
            st2 = st.resize((max(1, int(st.width * sc)), max(1, int(st.height * sc))))
            frame.alpha_composite(st2, (m - 40, int(H - st2.height + 30 + math.sin(lt * 2.6) * 5)))
            cap_x = m + st.width - 70
            cap_w = W - cap_x - m

        # caption with active-word highlight
        spoken = next((l for l in all_lines if l.start - 0.05 <= ts < l.start + l.dur + 0.25), None)
        if spoken is not None:
            words, wts = _words_with_weights(spoken.text)
            prog = (ts - spoken.start) / max(spoken.dur, 0.01)
            acc, active = 0.0, len(words) - 1
            for wi, wv in enumerate(wts):
                acc += wv / sum(wts)
                if prog < acc:
                    active = wi
                    break
            key = (spoken.id, active, cap_w)
            if key not in cap_cache:
                cap_cache[key] = caption_image(spoken.text, active, cap_w,
                                               int((H - cap_y) * (0.11 if s.sticker else 0.15)))
            c = cap_cache[key]
            frame.alpha_composite(c, (cap_x + (cap_w - c.width) // 2,
                                      cap_y + (H - cap_y - c.height) // 2 - int(H * 0.02)))
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError("ffmpeg failed")

    # audio: voice + soft bed + sfx (pop on each board row, whoosh on shot changes)
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    for l in all_lines:
        k = int(l.start * SR)
        voice[k:k + len(l.audio)] += l.audio
    voice *= 0.89 / (np.abs(voice).max() or 1)
    env = np.convolve(np.abs(voice), np.ones(int(0.25 * SR)) / int(0.25 * SR), "same")
    duck = 1 - 0.6 * np.clip(env / (env.max() or 1) * 4, 0, 1)
    bed = music_bed(total + 1, bpm=96)[:n] * duck * float(spec.get("music_level", 0.35))
    fx = np.zeros(n, np.float32)
    pop, wh = sfx_pop(), sfx_whoosh()
    for l in all_lines:
        rows = len(l.spec.get("board", [])) or 1
        for i in range(rows):
            k = int((l.start + (l.dur * 0.85) * i / rows + 0.05) * SR)
            fx[k:k + len(pop)] += pop[: max(0, n - k)]
    for s in shots[1:]:
        k = max(0, int((s.start - 0.15) * SR))
        fx[k:k + len(wh)] += wh[: n - k] * 0.4
    import soundfile as sf
    wav = base / f"{ep_id}_mix.wav"
    sf.write(str(wav), np.clip(voice + bed + fx, -1, 1)[: int(total * SR)], SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)], check=True)
    silent.unlink()
    return out
