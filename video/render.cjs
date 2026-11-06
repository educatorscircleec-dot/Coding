// Renders scene.js frame-by-frame in headless Chromium and encodes an MP4.
// Muxes assets/music.wav (from music.py) as the soundtrack when present.
// Usage: node render.cjs [--fps 30] [--out educrew-promo-15s.mp4] [--stills 0,3,6,9,12,14.5]
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? a.concat([[v.slice(2), arr[i + 1]]]) : a), []));
const FPS = +(args.fps || 30);
const OUT = path.resolve(__dirname, args.out || 'educrew-miniature-ad-30s.mp4');
const MUSIC = path.join(__dirname, 'assets', 'music.wav');
const STILLS = args.stills ? args.stills.split(',').map(Number) : null;

const types = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const p = path.join(__dirname, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(__dirname) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, r));
  const port = server.address().port;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto(`http://127.0.0.1:${port}/index.html?render`);
  await page.evaluate(() => window.ready);
  const grab = (t, type) => page.evaluate(([t, type]) => { renderAt(t); return document.getElementById('c').toDataURL(type, 0.95).split(',')[1]; }, [t, type]);

  if (STILLS) {
    const dir = path.join(__dirname, 'stills'); fs.mkdirSync(dir, { recursive: true });
    for (const t of STILLS) fs.writeFileSync(path.join(dir, `t${t.toFixed(1)}.png`), Buffer.from(await grab(t, 'image/png'), 'base64'));
    console.log('stills written to', dir);
  } else {
    const dur = await page.evaluate(() => window.DUR);
    const n = Math.round(dur * FPS);
    const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      ...(fs.existsSync(MUSIC) ? ['-i', MUSIC, '-c:a', 'aac', '-b:a', '192k', '-map', '0:v', '-map', '1:a', '-shortest'] : []),
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = 0; i < n; i++) {
      const buf = Buffer.from(await grab(i / FPS, 'image/jpeg'), 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 30 === 0) process.stdout.write(`frame ${i}/${n}\n`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    console.log('wrote', OUT);
  }
  await browser.close(); server.close();
})();
