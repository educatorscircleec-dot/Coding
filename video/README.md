# EduCrew Academic Studio — 15s promo (9:16)

`educrew-promo-15s.mp4` — 1080×1920, 30 fps, 15 s, no audio.

| Time | Shot |
|---|---|
| 0–2.5s | A hand lowers the miniature EduCrew Academic Studio onto an oak desk (tea steaming beside it) |
| 2.5–4.5s | The hand places a tiny desk, a laptop with an LMS storyboard, and a curriculum-map whiteboard; the logo lights up the sign |
| 4.5–7s | Camera glides across the Math, English and Science shelves |
| 7–10.5s | A fingertip taps the workbook; it opens and numbers, letters, shapes and atoms swirl up like steam |
| 10.5–12.5s | A hand slides in a tray: teacher guide, student workbook, marked assessment, LMS tablet |
| 12.5–15s | Scene dims; logo, subjects and @educrew.academicsolution fade in |

## Edit and re-render
- Preview: serve this folder (`python3 -m http.server`) and open `index.html` (play/pause + scrubber).
- Timing, camera moves and art are all in `scene.js` (`CAM`, `ITEMS`, `HK2`, `HK3`, `trayY`).
- Render: `node render.cjs` (needs Playwright + ffmpeg). `node render.cjs --stills 4,9,14` saves PNG frames.
