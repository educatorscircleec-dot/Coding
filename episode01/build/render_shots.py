# Renders each keyframe into a 5.5s 1080x1920 shot with a slow camera move.
import subprocess, sys
KF = "/home/user/Coding/episode01/keyframes/kf{:02d}.png"
OUT = "/home/user/Coding/episode01/build/shot{:02d}.mp4"
FPS, DUR = 30, 5.5
N = int(FPS * DUR)
# (zoom_start, zoom_end, cx_start, cy_start, cx_end, cy_end) — centre of view, normalised
MOVES = {
 1: (1.00, 1.14, .50, .55, .48, .50),  # push toward doorway
 2: (1.10, 1.22, .45, .65, .52, .66),  # drift onto hands & chapati
 3: (1.18, 1.08, .52, .58, .48, .55),  # gentle pull-back, father & daughter
 4: (1.25, 1.18, .42, .66, .44, .58),  # tilt up along plaits (keeps mother's face out)
 5: (1.05, 1.18, .55, .45, .50, .42),  # push onto tiffin
 6: (1.15, 1.03, .50, .55, .50, .50),  # pull-out reveal of lane
 7: (1.00, 1.12, .40, .55, .35, .52),  # push toward mother in doorway
 8: (1.12, 1.20, .40, .60, .50, .62),  # drift onto marbles
 9: (1.08, 1.20, .50, .48, .50, .50),  # top-down push on meal
 10:(1.30, 1.40, .48, .62, .50, .68),  # push to candles (crops edges)
 11:(1.18, 1.04, .40, .62, .45, .55),  # slow pull-back, rooftop sunset
 12:(1.00, 1.12, .50, .50, .52, .40),  # push past girl toward the lane
}
def run(i):
    z0,z1,x0,y0,x1,y1 = MOVES[i]
    t = f"(on/{N-1})"
    e = f"(0.5-0.5*cos(PI*{t}))"          # ease in-out
    z = f"{z0}+({z1}-{z0})*{e}"
    cx = f"({x0}+({x1}-{x0})*{e})"
    cy = f"({y0}+({y1}-{y0})*{e})"
    x = f"max(0,min(iw-iw/zoom,{cx}*iw-iw/zoom/2))"
    y = f"max(0,min(ih-ih/zoom,{cy}*ih-ih/zoom/2))"
    vf = (f"scale=2160:-1:flags=lanczos,crop=2160:3840,"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={N}:s=1080x1920:fps={FPS},"
          f"eq=saturation=1.06:contrast=1.03,noise=alls=5:allf=t,vignette=PI/6,format=yuv420p")
    cmd = ["ffmpeg","-y","-loglevel","error","-loop","1","-i",KF.format(i),"-vf",vf,
           "-frames:v",str(N),"-c:v","libx264","-preset","medium","-crf","16",OUT.format(i)]
    subprocess.run(cmd, check=True); print("shot", i, "done", flush=True)
if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(4) as ex: list(ex.map(run, range(1,13)))
