"""Build finished scene images: AI background + your own character sticker + your logo.

Using the real sticker art (rather than asking a model to redraw the character) keeps the
host looking exactly like the brand artwork in every scene.

Inputs per shot (shots.yaml):
    sticker:        file name in brand/stickers/ (without .png)
    sticker_side:   left | right | center           (default: left)
    sticker_scale:  fraction of frame width          (default: 0.62)
    sticker_crop:   [left, top, right, bottom] as fractions, to trim a sticker's caption
    focus_x:        0..1, which part of the square background to keep in a vertical frame
    title:          optional big on-screen text at the top (e.g. the hook)
Background image: output/<ep>/backgrounds/<shot>.jpg|png
Logo: series/style.yaml -> brand.logo
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for f in FONT_CANDIDATES:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def _cover(bg: Image.Image, w: int, h: int, focus_x: float) -> Image.Image:
    scale = max(w / bg.width, h / bg.height)
    bg = bg.resize((round(bg.width * scale), round(bg.height * scale)), Image.LANCZOS)
    x = round((bg.width - w) * min(max(focus_x, 0), 1))
    y = (bg.height - h) // 2
    return bg.crop((x, y, x + w, y + h))


def _round_logo(path: Path, size: int) -> Image.Image:
    logo = Image.open(path).convert("RGBA")
    if logo.getpixel((0, 0))[3] == 255:  # opaque square: cut it to a circle
        mask = Image.new("L", logo.size, 0)
        ImageDraw.Draw(mask).ellipse((2, 2, logo.width - 3, logo.height - 3), fill=255)
        logo.putalpha(mask)
    return logo.resize((size, size), Image.LANCZOS)


def _shadow(layer: Image.Image, radius: int = 18, opacity: int = 90) -> Image.Image:
    alpha = layer.split()[3].point(lambda a: opacity if a > 0 else 0)
    sh = Image.new("RGBA", layer.size, (30, 10, 50, 0))
    sh.putalpha(alpha.filter(ImageFilter.GaussianBlur(radius)))
    return sh


def _title(img: Image.Image, text: str) -> None:
    d = ImageDraw.Draw(img)
    size = img.width // 11
    font = _font(size)
    lines, line = [], ""
    for word in text.split():  # wrap to ~88% of width
        test = f"{line} {word}".strip()
        if d.textlength(test, font=font) > img.width * 0.88 and line:
            lines.append(line)
            line = word
        else:
            line = test
    lines.append(line)
    y = int(img.height * 0.16)
    for ln in lines:
        tw = d.textlength(ln, font=font)
        d.text(((img.width - tw) / 2, y), ln, font=font, fill="white",
               stroke_width=size // 7, stroke_fill=(74, 30, 110))
        y += int(size * 1.15)


def compose_scene(bg_path: Path, out_path: Path, size: tuple[int, int], *,
                  sticker: Path | None = None, side: str = "left", scale: float = 0.62,
                  crop: list[float] | None = None, focus_x: float = 0.5,
                  logo: Path | None = None, logo_scale: float = 0.2,
                  title: str | None = None) -> Path:
    w, h = size
    canvas = _cover(Image.open(bg_path).convert("RGB"), w, h, focus_x).convert("RGBA")

    if sticker:
        st = Image.open(sticker).convert("RGBA")
        if crop:
            l, t, r, b = crop
            st = st.crop((int(l * st.width), int(t * st.height),
                          int(r * st.width), int(b * st.height)))
        st = st.crop(st.split()[3].getbbox())
        sw = int(w * scale)
        st = st.resize((sw, round(st.height * sw / st.width)), Image.LANCZOS)
        margin = int(w * 0.03)
        x = {"left": margin, "right": w - sw - margin}.get(side, (w - sw) // 2)
        y = h - st.height - int(h * 0.06)
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        layer.paste(st, (x, y), st)
        canvas = Image.alpha_composite(canvas, _shadow(layer))
        canvas = Image.alpha_composite(canvas, layer)

    if logo:
        ls = int(w * logo_scale)
        lg = _round_logo(logo, ls)
        m = int(w * 0.035)
        canvas.alpha_composite(lg, (m, m))

    if title:
        _title(canvas, title)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path)
    return out_path
