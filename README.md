# AI Animated Series Studio

A project layout and pipeline for making an animated series with AI tools. You write the show as plain
text and YAML, and the pipeline turns each shot into a keyframe image, animates it into a short clip,
and joins the clips into an episode with subtitles.

```
 script.md ──► shots.yaml ──► prompts ──► keyframes (image) ──► clips (image→video) ──► episode.mp4 + .srt
                  ▲               ▲
   characters/*.yaml   locations/*.yaml   series/style.yaml
```

## Layout

| Path | What lives there |
|------|------------------|
| `series/bible.md` | Logline, format, tone, world rules, episode ideas (for writers) |
| `series/style.yaml` | The show's look: style prompt, negative prompt, resolution, fps, which AI providers to use |
| `characters/*.yaml` | One file per character. Its `visual` text goes into every prompt, which keeps the character looking the same from shot to shot |
| `locations/*.yaml` | Reusable sets, described the same way |
| `episodes/epNNN/script.md` | The screenplay |
| `episodes/epNNN/shots.yaml` | The shot list (storyboard as data): framing, action, motion, dialogue, duration |
| `studio/` | The Python pipeline |
| `output/` | Generated media (git-ignored; you can always regenerate it) |

## Quick start

```bash
pip install -e ".[ai,dev]"       # needs ffmpeg on PATH as well

python -m studio validate        # checks every shot refers to real characters/locations
python -m studio prompts ep001   # shows the exact prompts each shot will send
python -m studio render ep001    # keyframes → clips → output/ep001/ep001.mp4
```

Out of the box, both steps use the **placeholder** provider: title cards with a slow zoom. It costs
nothing, so use it to block out timing and pacing before you generate anything.

## Switching on real AI generation

Edit `series/style.yaml`, or override a provider for a single run:

```bash
# Keyframes: text-to-image via Hugging Face Inference (FLUX.1-schnell by default)
python -m studio keyframes ep001 --provider huggingface --only s020

# Clips: image-to-video via the Wan 2.2 Space (zerogpu-aoti/wan2-2-fp8da-aoti-faster)
python -m studio animate ep001 --provider wan --only s020 --force

python -m studio assemble ep001
```

- Both need a Hugging Face token in `HF_TOKEN`. ZeroGPU Spaces have a daily GPU quota, so iterate on one
  shot with `--only` before you render a whole episode.
- Files that already exist are skipped. To redo a shot, pass `--force` (with `--only` to limit it to that shot).
- Each step reads its keyframe or clip from disk, so you can drop in your own image (for example a
  hand-fixed keyframe) at `output/ep001/keyframes/s020.png` and only re-animate that shot.

## Branded scenes and motion (no AI video needed)

For shorts hosted by your own character (see `brand/`):

```bash
python -m studio compose short001   # AI background + your sticker + logo -> scenes/*.png
python -m studio motion short001    # camera moves, living stickers, map card -> clips/*.mp4
python -m studio voice short001
python -m studio assemble short001
```

Each shot in `shots.yaml` can set:
- `camera`: `move` (push_in, pull_out, pan_left, pan_right, tilt_up, tilt_down, still), `amount`,
  `focus_x`, and `dim` (lights going down during the shot).
- `map`: a label, `pins` as `[lat, lon]`, and an optional `region` to fly in to. The map card slides
  in, flies from the whole world down to the region, and drops pins that pulse.
  The world outlines come from Natural Earth (public domain), stored in `studio/data/world.json`.

Layout: the whole picture sits in the middle of the vertical frame and is never covered. The band
above it holds the logo and the map card (or the title), and the band below holds the spoken line
as a burned-in caption. Camera moves are kept gentle (at most 8% zoom), so the animal stays whole.
Use the host sticker only when she speaks to the viewer. Animated GIF stickers keep playing their
frames.

## Voices

`python -m studio voice <episode>` reads every shot's dialogue aloud with
[Kokoro](https://huggingface.co/hexgrad/Kokoro-82M), an open text-to-speech model that runs on the CPU
for free. It writes one WAV file per shot, plus `voiceover.wav`, a read-through of the whole script.
It also warns you when a line runs longer than its shot. `assemble` then lays each shot's audio
under that shot.

One-time setup:

```bash
pip install -e ".[voice]"
HF_HUB_DISABLE_XET=1 python -c "from huggingface_hub import hf_hub_download as d; \
  [d('fastrtc/kokoro-onnx', f, local_dir='models/kokoro') for f in ('kokoro-v1.0.onnx','voices-v1.0.bin')]"
```

Cast each voice in the character file with `tts_voice` and `tts_speed`. Voice ids starting `af_`/`am_`
are American and `bf_`/`bm_` are British; there are 54 voices in all.

### Adding another provider

Subclass `KeyframeProvider` or `AnimateProvider` in `studio/providers/`, then register the new
provider by name in `studio/providers/__init__.py`. Runway, Kling, Luma, local ComfyUI or Stable
Diffusion would all go in this way.

## Making an episode

1. Write the next episode idea into `series/bible.md`.
2. `python -m studio new-episode ep002 "Too Many Ramps"`
3. Write `script.md`, then break it into shots in `shots.yaml`. Each AI clip runs 1–5 s, so plan for
   lots of short shots.
4. `validate` → `prompts` → `render` with placeholders, and check the pacing.
5. Switch on real providers, generate shot by shot, and replace any weak keyframes.
6. `assemble`, then finish in an editor (music, voices, sound effects, colour).

## Tips for consistent characters

- Keep each character's `visual` short and specific, and never paraphrase it per shot.
- Put the action in `action` and the movement in `motion`. Don't re-describe the character there.
- Use a fixed `seed` in `style.yaml` while you iterate.
- When a keyframe nails the look, save it as the character's `reference_image` for later
  image-to-image or character-reference tools.

## Not yet covered (next steps)

- Lip-sync
- Music and sound-effect layers in `assemble`
- Character-reference or LoRA keyframes for stronger consistency

## Tests

```bash
python -m pytest
```

## Narrated shorts (voice-timed, one-pass render)

`python -m studio short <episode>` renders a whole short in one pass from `shots.yaml`:
- **Voice first.** Each narration line is its own audio file (`output/<ep>/lines/<id>.mp3`). The
  renderer measures every line, then times shot cuts, pauses, captions and map pins from the voice,
  so nothing drifts out of sync. Pauses are spread to land exactly on `target_seconds`.
- **Animated pictures.** `scripts/wan_batch.py episodes/<ep>/animation.yaml` makes one Wan 2.2 clip
  per scene. It skips clips that already exist, so you can re-run it after the free GPU allowance resets.
- **Captions** highlight each word as it's spoken. **Map pins** drop when the "where it lives" line
  starts. A soft music-box bed dips under the voice, with a whoosh on cuts and a pop on pins. The
  final mix is normalised to -14 LUFS.
- `timing.json` and the `.srt` file record exactly when every line plays.
