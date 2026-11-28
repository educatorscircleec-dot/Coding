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


def mix_dialogue(wavs: list[tuple[Path, float]], total: float, out_path: Path) -> Path:
    """Place each shot's dialogue WAV at that shot's start time on one track."""
    import numpy as np
    import soundfile as sf

    sr = sf.info(str(wavs[0][0])).samplerate
    track = np.zeros(int(total * sr) + sr, dtype=np.float32)
    for path, start in wavs:
        data, _ = sf.read(str(path), dtype="float32")
        i = int((start + 0.15) * sr)  # small lead-in so lines don't start on the cut
        data = data[: max(0, len(track) - i)]
        track[i : i + len(data)] += data
    sf.write(str(out_path), np.clip(track[: int(total * sr)], -1, 1), sr)
    return out_path


def add_audio(video: Path, audio: Path) -> Path:
    tmp = video.with_suffix(".tmp.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
         "-shortest", str(tmp)],
        check=True,
    )
    tmp.replace(video)
    return video
