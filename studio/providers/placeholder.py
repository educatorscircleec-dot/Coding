"""Offline stand-ins: title cards and slow-zoom clips.

Use these to block out an episode's timing and test the pipeline without spending
any generation credits or GPU time.
"""

from __future__ import annotations

import hashlib
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .base import AnimateProvider, KeyframeProvider


class PlaceholderKeyframes(KeyframeProvider):
    def generate(self, prompt, negative, out_path: Path, label=""):
        # Stable colour per shot so placeholder clips are easy to tell apart.
        h = hashlib.md5(label.encode()).digest()
        bg = (40 + h[0] % 80, 40 + h[1] % 80, 60 + h[2] % 80)
        img = Image.new("RGB", (self.width, self.height), bg)
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((24, 20), label.upper(), fill=(255, 220, 140), font=font)
        y = 50
        for line in textwrap.wrap(prompt, 100)[:20]:
            draw.text((24, y), line, fill=(235, 235, 235), font=font)
            y += 16
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path)
        return out_path


class PlaceholderAnimate(AnimateProvider):
    def animate(self, image: Path, prompt, negative, duration, out_path: Path, label=""):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        frames = max(1, int(duration * self.fps))
        # Slow Ken Burns zoom so the timing feels like motion.
        vf = (f"zoompan=z='min(zoom+0.0015,1.15)':d={frames}:"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={self.fps},format=yuv420p")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(image),
             "-vf", vf, "-frames:v", str(frames), "-c:v", "libx264", str(out_path)],
            check=True,
        )
        return out_path
