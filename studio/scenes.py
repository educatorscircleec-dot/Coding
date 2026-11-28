"""Animated explainer scenes drawn locally (free), used by the Math Hacks renderer.

doors: the three-doors probability puzzle. Per narration line, a state like
  {show: [1, 2, 3], picked: 1, open: {3: goat}, ask: [1, 2], labels: {1: "1/3"},
   group: {doors: [2, 3], text: "2/3"}, move_group_to: 2, stamp: "50 / 50 ?", banner: "..."}
Everything animates in on the line's own clock, so it lands as the words are spoken.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

from .compose import _font
from .motion import INK, ease, ease_out_back

DOOR = (167, 110, 220)
DOOR_DARK = (120, 70, 175)
GREEN = (34, 170, 110)
YELLOW = (255, 196, 0)
RED = (230, 60, 80)


def draw_car(d: ImageDraw.ImageDraw, cx, cy, s):
    d.rounded_rectangle((cx - s, cy - s * 0.15, cx + s, cy + s * 0.35), s * 0.18, fill=RED, outline=INK, width=5)
    d.rounded_rectangle((cx - s * 0.55, cy - s * 0.55, cx + s * 0.45, cy - s * 0.1), s * 0.2,
                        fill=RED, outline=INK, width=5)
    d.rectangle((cx - s * 0.42, cy - s * 0.45, cx + s * 0.32, cy - s * 0.18), fill=(190, 230, 255))
    for wx in (-0.55, 0.55):
        d.ellipse((cx + wx * s - s * 0.22, cy + s * 0.18, cx + wx * s + s * 0.22, cy + s * 0.62),
                  fill=INK)
        d.ellipse((cx + wx * s - s * 0.09, cy + s * 0.31, cx + wx * s + s * 0.09, cy + s * 0.49),
                  fill=(220, 220, 220))


def draw_goat(d: ImageDraw.ImageDraw, cx, cy, s):
    fur, horn = (245, 240, 230), (170, 140, 100)
    d.polygon([(cx - s * 0.35, cy - s * 0.35), (cx - s * 0.6, cy - s * 0.95), (cx - s * 0.15, cy - s * 0.45)],
              fill=horn, outline=INK)
    d.polygon([(cx + s * 0.35, cy - s * 0.35), (cx + s * 0.6, cy - s * 0.95), (cx + s * 0.15, cy - s * 0.45)],
              fill=horn, outline=INK)
    d.ellipse((cx - s * 0.95, cy - s * 0.4, cx - s * 0.35, cy - s * 0.1), fill=fur, outline=INK, width=4)
    d.ellipse((cx + s * 0.35, cy - s * 0.4, cx + s * 0.95, cy - s * 0.1), fill=fur, outline=INK, width=4)
    d.ellipse((cx - s * 0.48, cy - s * 0.5, cx + s * 0.48, cy + s * 0.55), fill=fur, outline=INK, width=5)
    for ex in (-0.2, 0.2):
        d.ellipse((cx + ex * s - s * 0.07, cy - s * 0.15, cx + ex * s + s * 0.07, cy - s * 0.01), fill=INK)
    d.ellipse((cx - s * 0.2, cy + s * 0.18, cx + s * 0.2, cy + s * 0.42), fill=(240, 180, 190), outline=INK, width=3)
    d.polygon([(cx - s * 0.1, cy + s * 0.5), (cx + s * 0.1, cy + s * 0.5), (cx, cy + s * 0.85)], fill=fur, outline=INK)


def _label(img, text, cx, y, size, color, p=1.0):
    if p <= 0:
        return
    d = ImageDraw.Draw(img)
    while size > 24 and d.textlength(text, font=_font(size)) > img.width * 0.86:
        size -= 4
    font = _font(max(8, int(size * p)))
    tw = d.textlength(text, font=font)
    d.text((cx - tw / 2, y), text, font=font, fill=color, stroke_width=max(2, int(size * p) // 9),
           stroke_fill="white")


def doors_scene(card: Image.Image, state: dict, lt: float, dur: float) -> None:
    """Draw the doors state onto `card` (an RGBA image the size of the board)."""
    W, H = card.size
    d = ImageDraw.Draw(card)
    dw, dh = int(W * 0.24), int(H * 0.5)
    gap = (W - 3 * dw) // 4
    top = int(H * 0.30)
    xs = {i: gap + (i - 1) * (dw + gap) for i in (1, 2, 3)}
    if state.get("hundred"):
        hundred_doors(card, state, lt, dur)
        return
    prizes = state.get("prizes", {1: "goat", 2: "car", 3: "goat"})
    shown = state.get("show", [1, 2, 3])
    for i in (1, 2, 3):
        if i not in shown:
            continue
        p = ease_out_back((lt - 0.15 * (i - 1)) / 0.4) if state.get("intro") else 1.0
        if p <= 0:
            continue
        x, y = xs[i], top + int((1 - min(p, 1)) * 60)
        # what's behind (visible when open)
        d.rounded_rectangle((x, y, x + dw, y + dh), 18, fill=(255, 246, 214), outline=INK, width=6)
        opening = state.get("open", {})
        k = 0.0
        if i in opening:
            k = ease((lt - float(state.get("open_at", 0.4)) * dur) / 0.6) if state.get("animate_open", True) else 1.0
        if i in opening and k > 0.15:
            what = opening[i] or prizes.get(i)
            (draw_car if what == "car" else draw_goat)(d, x + dw / 2, y + dh * 0.5, dw * 0.38)
        # the door panel swings (shrinks to the left)
        pw = int(dw * (1 - 0.82 * k))
        if pw > 6:
            d.rounded_rectangle((x, y, x + pw, y + dh), 18, fill=DOOR, outline=INK, width=6)
            if pw > dw * 0.4:
                d.rounded_rectangle((x + pw * 0.15, y + dh * 0.1, x + pw * 0.85, y + dh * 0.42), 12,
                                    outline=DOOR_DARK, width=5)
                d.rounded_rectangle((x + pw * 0.15, y + dh * 0.52, x + pw * 0.85, y + dh * 0.88), 12,
                                    outline=DOOR_DARK, width=5)
                d.ellipse((x + pw * 0.78, y + dh * 0.5, x + pw * 0.9, y + dh * 0.56), fill=YELLOW, outline=INK)
                font = _font(int(dw * 0.32))
                d.text((x + pw / 2 - d.textlength(str(i), font=font) / 2, y + dh * 0.13), str(i),
                       font=font, fill="white", stroke_width=4, stroke_fill=INK)
    # your pick: bouncing arrow + "YOU"
    if state.get("picked"):
        i = state["picked"]
        bob = math.sin(lt * 5) * 10
        cx = xs[i] + dw / 2
        ay = top - 70 + bob
        d.polygon([(cx - 30, ay), (cx + 30, ay), (cx, ay + 45)], fill=YELLOW, outline=INK)
        _label(card, "YOU", cx, ay - 70, 56, INK)
    # "switch?" curved arrow from one door to another
    if state.get("ask"):
        a, b = state["ask"]
        p = ease((lt - 0.2) / 0.6)
        x1, x2 = xs[a] + dw / 2, xs[b] + dw / 2
        yb = top + dh + 50
        pts = [(x1 + (x2 - x1) * t, yb + math.sin(t * math.pi) * 45) for t in [j / 20 for j in range(int(20 * p) + 1)]]
        if len(pts) > 1:
            d.line(pts, fill=GREEN, width=10)
        if p >= 1:
            d.polygon([(x2 - 25, yb - 10), (x2 + 15, yb - 25), (x2 + 5, yb + 20)], fill=GREEN)
            _label(card, state.get("ask_text", "SWITCH?"), (x1 + x2) / 2, yb + 60, 60, GREEN)
    # odds labels under doors
    for i, text in (state.get("labels") or {}).items():
        p = ease_out_back((lt - float(state.get("labels_at", 0.3)) * dur) / 0.4)
        _label(card, text, xs[int(i)] + dw / 2, top + dh + 25, 84, YELLOW if text.startswith("1") else GREEN, min(p, 1.2))
    # bracket over a group of doors, optionally sliding onto one door
    if state.get("group"):
        g = state["group"]
        ds = g["doors"]
        p = ease_out_back((lt - 0.2) / 0.4)
        gx1, gx2 = xs[min(ds)], xs[max(ds)] + dw
        tgt = state.get("move_group_to")
        if tgt:
            mk = ease((lt - float(state.get("move_at", 0.55)) * dur) / 0.8)
            gx1 = gx1 + (xs[tgt] - gx1) * mk
            gx2 = gx2 + (xs[tgt] + dw - gx2) * mk
        if p > 0:
            by = top + dh + 40
            d.line((gx1, by, gx1, by + 30, gx2, by + 30, gx2, by), fill=GREEN, width=10)
            _label(card, g["text"], (gx1 + gx2) / 2, by + 45, 88, GREEN, min(p, 1.2))
    if state.get("stamp"):
        p = ease_out_back((lt - 0.25) / 0.35)
        if p > 0:
            _label(card, state["stamp"], W / 2, H * 0.05, 150, RED, min(p, 1.2))
            if state.get("cross") and lt > dur * 0.55:
                d.line((W * 0.25, H * 0.08, W * 0.75, H * 0.22), fill=RED, width=16)
    if state.get("banner"):
        p = ease_out_back((lt - float(state.get("banner_at", 0.15)) * dur) / 0.4)
        _label(card, state["banner"], W / 2, H * 0.06, 96, state.get("banner_color") == "yellow" and YELLOW or GREEN, min(p, 1.2))


def hundred_doors(card: Image.Image, state: dict, lt: float, dur: float) -> None:
    """10x10 grid of little doors: you pick #1, the host opens 98 goat doors one by one,
    leaving only yours and one other closed."""
    W, H = card.size
    d = ImageDraw.Draw(card)
    gx, gy = int(W * 0.1), int(H * 0.2)
    cell = int(min((W - 2 * gx) / 10, (H * 0.72) / 10))
    keep = state.get("keep", 57)          # the other door left closed
    open_start, open_len = float(state.get("open_at", 0.25)) * dur, float(state.get("open_len", 0.5)) * dur
    order = [i for i in range(2, 101) if i != keep]
    for n in range(1, 101):
        r, c = divmod(n - 1, 10)
        x, y = gx + c * cell, gy + r * cell
        idx = order.index(n) if n in order else None
        opened = idx is not None and lt > open_start + open_len * idx / len(order)
        pad = cell * 0.12
        box = (x + pad, y + pad, x + cell - pad, y + cell - pad)
        if opened:
            d.rounded_rectangle(box, 6, fill=(255, 246, 214), outline=INK, width=2)
            d.ellipse((x + cell * 0.35, y + cell * 0.35, x + cell * 0.65, y + cell * 0.65), fill=(245, 240, 230), outline=INK)
        else:
            col = YELLOW if n == 1 else (GREEN if n == keep and lt > open_start + open_len else DOOR)
            d.rounded_rectangle(box, 6, fill=col, outline=INK, width=3)
    if lt > open_start + open_len + 0.2:
        _label(card, state.get("after", "SWITCH NOW?"), W / 2, H * 0.03, 110, GREEN)
    else:
        _label(card, state.get("banner", "IMAGINE 100 DOORS"), W / 2, H * 0.03, 110, YELLOW)
