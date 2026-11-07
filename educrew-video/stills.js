// Render stills at given times for review: node stills.js out_dir 1 3 6 ...
const { chromium } = require('playwright');
const path = require('path'); const fs = require('fs'); const serve = require('./serve');
(async () => {
  const srv = await serve();
  const [out, ...times] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.error('PAGEERR', e.message));
  await p.goto(srv.url);
  await p.waitForFunction(() => window.logoReady); await p.evaluate(() => window.logoReady());
  for (const t of times) {
    const data = await p.evaluate(tt => { window.renderFrame(tt); return document.getElementById('out').toDataURL('image/jpeg', .85); }, parseFloat(t));
    fs.writeFileSync(path.join(out, `t${t}.jpg`), Buffer.from(data.split(',')[1], 'base64'));
  }
  await b.close(); srv.close();
})();
