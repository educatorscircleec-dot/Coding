# EduCrew Academic Solutions — 30 s miniature-world spot

Vertical 1080×1920, 30 fps, 30 s, with original instrumental music (no vocals).
Output: `EduCrew_Miniature_30s.mp4`.

| Time | Scene | On-screen text |
|---|---|---|
| 0–5 s | A hand opens the studio door; the camera moves forward through the doorway; the five women walk, carry workbooks and work | Welcome to EduCrew Academic Solutions |
| 5–10 s | Maths on the whiteboard, a maths lesson typed on a laptop, English resources, Science worksheets, a curriculum-map discussion; the camera moves left to right, zooms into the maths workbook and pulls back | Mathematics • English Language Arts • Science |
| 10–15 s | A storyboard is built on screen, a card moves across the Lesson Flow board, sequencing is checked; the camera zooms into the storyboard | Instructional Design & Storyboarding |
| 15–20 s | The LMS dashboard: a SCORM upload whose progress bar fills to 100 %, then the module opens; a learner preview is tested on a tablet that a team member carries across; a QA checklist ticks off | LMS Development • SCORM Packaging • Digital Learning |
| 20–25 s | Round assessment table, filmed in a semicircle orbit; the camera zooms into the assessment paper as its items are ticked | Assessment Design • Standards Alignment • Academic QA |
| 25–30 s | The team walks to the centre; the camera rises and pulls back; the lights dim; the logo and contact details appear | Your Academic Development Partner + contact details |

## The logo
There was no logo file to work from, so the video shows a plain **"EC" stand-in
badge** as the watermark (upper right) and on the final screen.
To use the original logo, save it as **`assets/logo.png`** (a transparent PNG is
best) and rebuild. It is drawn at its own proportions and is never stretched.

## Rebuild
```bash
node render.js frames                 # 900 JPEG frames (Playwright + Chromium)
python3 music.py music.wav            # instrumental bed + ambience + swooshes
ffmpeg -y -framerate 30 -i frames/f%04d.jpg -i music.wav \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow -movflags +faststart \
  -c:a aac -b:a 192k -shortest EduCrew_Miniature_30s.mp4
```
Preview in a browser: open `scene.html` (it loops), or `scene.html?t=12.5` for a single frame.
