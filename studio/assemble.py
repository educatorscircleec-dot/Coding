"""Join shot clips into an episode and write subtitles from the dialogue."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def clip_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def write_srt(entries: list[tuple[float, float, str, str]], out_path: Path) -> Path:
    """entries: (start, end, speaker, line)"""
    blocks = [
        f"{i}\n{_ts(a)} --> {_ts(b)}\n{speaker}: {line}\n"
        for i, (a, b, speaker, line) in enumerate(entries, 1)
    ]
    out_path.write_text("\n".join(blocks), encoding="utf-8")
    return out_path


def concat(clips: list[Path], out_path: Path, fps: int, size: tuple[int, int]) -> Path:
    """Re-encode while joining so clips from different providers/sizes still line up."""
    w, h = size
    inputs: list[str] = []
    filters = []
    for i, c in enumerate(clips):
        inputs += ["-i", str(c)]
        filters.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={fps},setsar=1,format=yuv420p[v{i}]"
        )
    graph = ";".join(filters) + ";" + "".join(f"[v{i}]" for i in range(len(clips)))
    graph += f"concat=n={len(clips)}:v=1:a=0[out]"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph,
         "-map", "[out]", "-c:v", "libx264", "-crf", "18", str(out_path)],
        check=True,
    )
    return out_path
