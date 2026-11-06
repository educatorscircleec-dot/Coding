// Render all 900 frames (30 fps × 30 s) in parallel pages: node render.js frames_dir
const { chromium } = require('playwright');
const path = require('path'); const fs = require('fs');
(async () => {
  const out = process.argv[2] || 'frames'; fs.mkdirSync(out, { recursive: true });
  const FPS = 30, N = 900, P = 4;
  const b = await chromium.launch();
  await Promise.all([...Array(P)].map(async (_, w) => {
    const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
    p.on('pageerror', e => console.error('PAGEERR', e.message));
    await p.goto('file://' + path.resolve(__dirname, 'scene.html') + '?render=1');
    await p.evaluate(() => document.fonts.ready); await p.evaluate(() => window.logoReady());
    for (let f = w; f < N; f += P) {
      const d = await p.evaluate(t => { window.renderFrame(t); return document.getElementById('c').toDataURL('image/jpeg', .94); }, f / FPS);
      fs.writeFileSync(path.join(out, `f${String(f).padStart(4, '0')}.jpg`), Buffer.from(d.split(',')[1], 'base64'));
    }
  }));
  await b.close();
})();
