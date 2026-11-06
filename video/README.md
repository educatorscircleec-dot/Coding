# EduCrew Academic Solutions — 30s cinematic miniature-world ad (9:16)

`educrew-miniature-ad-30s.mp4`: 1080×1920, 30 fps, 30 s, H.264 + AAC stereo music.

| Time | Scene | Camera | On-screen text |
|---|---|---|---|
| 0–5s | EduCrew academic workspace (hand places the sign; original logo appears on it) | zoom in, glide left→right | Big ideas begin with great academic design. |
| 5–10s | Mathematics curriculum studio (teacher at whiteboard) | track left→right, push into workbook | Mathematics \| Curriculum \| Concept-based Learning |
| 10–15s | ELA library continuing into the science corner | pan left→right, zoom out | English Language Arts \| Science \| Learning Resources |
| 15–20s | Curriculum office: map, assessments, hand placing a sheet | zoom into documents, pull back | Standards Alignment \| Assessment Design \| Instructional Design |
| 20–25s | Digital learning studio, specialists collaborating | right→left, zoom out | Curriculum Development to LMS-ready Content |
| 25–30s | Studio softens into the brand background; large logo; contact details | settle | Final card (exact wording) |

Brand rules: the original `assets/educrew-logo.png` is only ever scaled uniformly (never redrawn or
recoloured). It sits as a watermark top-right until the large centred logo takes over at 25.3s.
All text is typeset in the edit; the scene images contain no generated text or fake logos.

## Files
- `assets/mini/*.jpg`: photoreal miniature-diorama scene images (generated with Figma AI, upscaled 1.5×).
- `scene.js`: camera keys, captions, watermark, end card. `music.py`: original 30s soundtrack.
- `render.cjs`: renders in headless Chromium and muxes `assets/music.wav`.

```
python3 music.py assets/music.wav
node render.cjs                      # -> educrew-miniature-ad-30s.mp4
node render.cjs --stills 2,12,27     # PNG frames
```
