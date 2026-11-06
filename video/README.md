# EduCrew Miniature World reel — 15s (9:16) with music

`educrew-promo-15s.mp4`: 1080×1920, 30 fps, 15 s, H.264 + AAC stereo soundtrack.

| Time | Scene | On screen |
|---|---|---|
| 0–3s | Mathematics | Camera glides from the abacus/math book to the kids; numbers & operators swirl up from the book |
| 3–6s | English Language Arts | Glide across the reading corner; letters rise from the storybook |
| 6–9s | Science | Glide to the young scientist; atoms, bubbles, H₂O swirl from the flask |
| 9–12s | Academic Content Studio | Glide across the laptop & LMS storyboards; checkmarks and play icons rise |
| 12–15s | End card | Logo pops on the music hit, tagline, subjects, services, contact, "Let's build better learning" |

Each scene has an animated caption card (title, subject chips, icon), story-style progress bar,
brand pill, light flash on cuts, and twinkles.

## Files
- `scene.js`: all animation (scene list, camera moves, captions, end card text).
- `assets/plates/*.jpg`: scene artwork taken from the reference reel.
- `music.py`: synthesises the original, royalty-free soundtrack (`assets/music.wav`), 120 BPM,
  one chord per scene, whooshes into each cut, hit at 12s.
- `render.cjs`: renders frames in headless Chromium and muxes the music with ffmpeg.

## Edit and re-render
```
python3 music.py assets/music.wav   # only if you change the music
node render.cjs                     # writes educrew-promo-15s.mp4
node render.cjs --stills 1.5,7,13   # PNG frames for checking
```
Preview live: `python3 -m http.server` in this folder, open `index.html`.
