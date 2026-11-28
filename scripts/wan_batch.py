"""Animate scene backgrounds with Wan 2.2 (image -> video), chaining clips for long shots.

Usage: python scripts/wan_batch.py episodes/short001/animation.yaml
Each job: background image, one prompt per segment. Segment N+1 starts from the last
frame of segment N, so the motion is continuous.
"""
import concurrent.futures as cf
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from gradio_client import Client, handle_file

SPACE = "zerogpu-aoti/wan2-2-fp8da-aoti-faster"
STYLE = ", cute 2D cartoon animation, bold clean outlines, pastel colors, smooth natural motion, static camera, same art style"
NEG = "morphing, melting, distortion, extra limbs, extra heads, text, watermark, camera shake, zoom, realistic, 3d, flicker, blurry"


def last_frame(video: Path, out: Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.1", "-i", str(video),
                    "-frames:v", "1", "-q:v", "2", str(out)], check=True)
    return out


def run_job(name, job, outdir):
    client = Client(SPACE, verbose=False)
    image = Path(job["image"])
    parts = []
    for i, seg in enumerate(job["segments"]):
        out = outdir / f"{name}_{i}.mp4"
        if not out.exists():
            for attempt in range(3):
                try:
                    v, _ = client.predict(
                        input_image=handle_file(str(image)), prompt=seg["prompt"] + STYLE,
                        steps=6, negative_prompt=NEG, duration_seconds=seg.get("seconds", 4.2),
                        guidance_scale=1, guidance_scale_2=1, seed=job.get("seed", 42),
                        randomize_seed=False, api_name="/generate_video")
                    shutil.copy(v["video"] if isinstance(v, dict) else v, out)
                    break
                except Exception as e:  # queue hiccups: retry
                    print(f"{name}_{i} attempt {attempt + 1} failed: {e}", flush=True)
            else:
                raise RuntimeError(f"{name}_{i} failed")
        print(f"done {out.name}", flush=True)
        parts.append(out)
        image = last_frame(out, outdir / f"{name}_{i}_last.png")
    # join segments (drop the duplicated first frame of each continuation)
    lst = outdir / f"{name}.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p",
                    str(outdir / f"{name}.mp4")], check=True)
    return name


if __name__ == "__main__":
    spec = yaml.safe_load(Path(sys.argv[1]).read_text())
    outdir = Path(spec["output"])
    outdir.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(max_workers=int(spec.get("parallel", 3))) as ex:
        futs = {ex.submit(run_job, n, j, outdir): n for n, j in spec["jobs"].items()}
        for f in cf.as_completed(futs):
            try:
                print(f"FINISHED {f.result()}", flush=True)
            except Exception as e:
                print(f"ERROR {futs[f]}: {e}", flush=True)
