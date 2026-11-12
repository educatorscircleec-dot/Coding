# Episode 1 — A Little World of Happiness (60 s, 9:16, 1080×1920, 30 fps)

## Shot list & timing
| # | Time | Shot | Sound |
|---|------|------|-------|
| 1 | 0–5 s | Girl runs across sunlit courtyard toward doorway (rear) | birds, crow, footsteps — **N1** |
| 2 | 5–10 | Mother's bangled hands rolling chapati, child's hand reaches in | water pouring, birds |
| 3 | 10–15 | Over father's shoulder: newspaper, girl hugs him from behind | clock tick — **N2** |
| 4 | 15–20 | Mother braids plaits, girl in school uniform (rear) | clock tick, birds |
| 5 | 20–25 | Girl's hands pack steel tiffin into red school bag | water drops — **N3** |
| 6 | 25–30 | Hopscotch in the lane, golden hour (rear) | children laughing |
| 7 | 30–35 | Mother in doorway calls out (rear) | door creak, crickets — **Mother line** |
| 8 | 35–40 | Girl playing marbles in the courtyard (rear) | crickets — **Child line** |
| 9 | 40–45 | Top-down family meal, hands only | water jug, crickets |
| 10 | 45–50 | Small birthday cake, parents' hands clapping | clapping, laughter |
| 11 | 50–55 | Family silhouettes on rooftop at sunset | breeze, crow — **N4** |
| 12 | 55–60 | Girl at the green gate looking out at schoolchildren in the lane | morning birds, rooster — **N5** → fade |

Narration (exact script): N1 "My childhood was simple, but it was full of happiness." · N2 "We didn't have everything, but somehow, we had everything that mattered." · N3 "A loving family, little moments of joy, and a home filled with warmth." · N4 "I didn't know much about the world back then." · N5 "I was just a little girl, enjoying her little world."

## How it was made
- Character reference: `character_reference.png` (rear view: girl, mother, father) — see `series_bible.md`. Every keyframe was generated with this image as a reference; reuse it for Episodes 2–10.
- Keyframes: `keyframes/kf01–kf12.png` (photoreal stills).
- Motion: slow eased push-ins/pull-outs/pans per shot (`build/render_shots.py`), 0.5 s crossfades.
- Voice: on-device neural TTS (Kokoro-82M, Indian female voices); child line pitch-raised. Verified by speech-to-text against the script.
- Sound: real field recordings from the ESC-50 dataset (CC BY-NC 3.0 — fine for non-commercial use; swap for licensed SFX if the reel is monetised/commercial). No music.
- Mix: `build/mix_audio.py` → `build/soundtrack.wav` (−16.8 LUFS).

## Pending
- **Logo**: run `./add_logo.sh /path/to/EduCrew_logo.png` once the original logo file is supplied.
- **Live-action motion**: keyframes are ready to be used as start frames for image-to-video once a video model is available (Runway paid plan, or Hugging Face GPU quota).
