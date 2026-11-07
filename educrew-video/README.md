# EduCrew Academic Solutions — 30 s miniature-world spot

Vertical 1080×1920, 30 fps, 30 s, with original instrumental music (no vocals).

The miniature world is a real 3D scene rendered in code with Three.js: modelled figurines, furniture and props,
physically based materials, soft shadows, depth-of-field blur, bloom and a colour grade.
The palette comes from the EduCrew logo (teal, gold, navy, purple, green).
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
The original EduCrew logo (`assets/logo.png`, transparent PNG) appears in three places: a fixed
watermark in the upper right for the whole video, the plaque above the door, and large in the
centre of the final screen. It is drawn at its own proportions and is never stretched or redrawn.

## Rebuild
```bash
npm install                           # three.js
node render.js frames                 # 900 JPEG frames (Playwright + Chromium WebGL, served over local HTTP)
python3 music.py music.wav            # instrumental bed + ambience + swooshes
ffmpeg -y -framerate 30 -i frames/f%04d.jpg -i music.wav \
  -c:v libx264 -b:v 9M -maxrate 12M -bufsize 18M -pix_fmt yuv420p -movflags +faststart \
  -c:a aac -b:a 192k -shortest EduCrew_Miniature_30s.mp4
```
Preview: `node stills.js out 3 12.5 29` writes stills at those times.
