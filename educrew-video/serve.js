// Tiny static server so the logo image doesn't taint the canvas (file:// does).
const http = require('http'), fs = require('fs'), path = require('path');
const TYPES = { '.html': 'text/html', '.png': 'image/png', '.js': 'text/javascript' };
module.exports = () => new Promise(res => {
  const srv = http.createServer((q, r) => {
    const f = path.join(__dirname, decodeURIComponent(q.url.split('?')[0]));
    if (!f.startsWith(__dirname) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
    r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r);
  }).listen(0, '127.0.0.1', () => res({ url: `http://127.0.0.1:${srv.address().port}/scene.html?render=1`, close: () => srv.close() }));
});
