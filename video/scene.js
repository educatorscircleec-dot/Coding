// EduCrew Academic Solutions — 30s cinematic miniature-world ad (1080x1920).
// Six 5-second scenes built from photoreal miniature-diorama plates, with
// camera moves, the original logo as a constant watermark, the supplied
// on-screen text added as clean typography, and a brand end card.
// Everything is a pure function of time t, so preview and MP4 render match.

const W = 1080, H = 1920, DUR = 30;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const FONT = 'Inter, "DejaVu Sans", sans-serif';
const C = { navy: '#0f2a45', navy2: '#081a2e', gold: '#f2b632', teal: '#1fa3a8', cream: '#fff8ec' };

function load(src) { const i = new Image(); i.src = src; return i; }
const logo = load('assets/educrew-logo.png');
const IMG = {
  s1: load('assets/mini/s1-workspace.jpg'), s2: load('assets/mini/s2-math.jpg'),
  s3a: load('assets/mini/s3a-library.jpg'), s3b: load('assets/mini/s3b-science.jpg'),
  s4: load('assets/mini/s4-office.jpg'), s5: load('assets/mini/s5-studio.jpg'),
};
const PW = 1296, PH = 2304;          // plate size
const SEAM = 360;                    // overlap of the library -> science strip
const S3B_X = PW - SEAM;

// Camera keys are in local scene time (s) and plate coordinates.
// z = screen pixels per plate pixel (0.834 shows the full plate width).
const SCENES = [
  {
    t0: 0, draw: 's1',
    keys: [[0, 0.86, 648, 1152], [2.4, 1.08, 560, 1250], [5.6, 1.08, 780, 1265]],
    text: 'Big ideas begin with great academic design.',
  },
  {
    t0: 5, draw: 's2',
    keys: [[-0.6, 1.0, 545, 1000], [2.6, 1.0, 750, 1000], [5.6, 1.27, 500, 1270]],
    text: 'Mathematics | Curriculum | Concept-based Learning',
  },
  {
    t0: 10, draw: 'strip',
    keys: [[-0.6, 1.06, 560, 1150], [1.2, 1.06, 740, 1150], [3.6, 1.0, S3B_X + 700, 1150], [5.6, 0.9, S3B_X + 640, 1152]],
    text: 'English Language Arts | Science | Learning Resources',
  },
  {
    t0: 15, draw: 's4',
    keys: [[-0.6, 0.9, 648, 1150], [2.4, 1.25, 800, 1530], [5.6, 0.9, 640, 1190]],
    text: 'Standards Alignment | Assessment Design | Instructional Design',
  },
  {
    t0: 20, draw: 's5',
    keys: [[-0.6, 1.15, 826, 1000], [2.6, 1.15, 472, 1050], [5.6, 0.86, 648, 1152]],
    text: 'Curriculum Development to LMS-ready Content',
  },
];
const XF = 0.6;     // crossfade length between scenes
const END = 25;     // brand reveal
const FINAL = [
  "Let's Build Better Learning Experiences.",
  'Call / WhatsApp: +91 9967421713',
  'Email: aaishayusuf.l@gmail.com',
  'Website: www.educrew.in',
  '@educrew.academicsolution',
];

// ---------- helpers ----------
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, p) => a + (b - a) * p;
const esine = p => 0.5 - 0.5 * Math.cos(Math.PI * p);
const eout = p => 1 - Math.pow(1 - p, 3);
function rr(x, y, w, h, r, fill, stroke, lw = 2) {
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
}
function setFont(size, weight) { ctx.font = `${weight} ${size}px ${FONT}`; }
function text(s, x, y, size, color, weight = 700, align = 'center') {
  setFont(size, weight); ctx.fillStyle = color; ctx.textAlign = align; ctx.textBaseline = 'middle';
  ctx.fillText(s, x, y);
}

// ---------- camera ----------
function camAt(keys, lt) {
  if (lt <= keys[0][0]) return keys[0].slice(1);
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    if (lt <= b[0]) {
      const p = esine((lt - a[0]) / (b[0] - a[0]));
      return [lerp(a[1], b[1], p), lerp(a[2], b[2], p), lerp(a[3], b[3], p)];
    }
  }
  return keys[keys.length - 1].slice(1);
}
function plateLayer(kind) {
  if (kind !== 'strip') { ctx.drawImage(IMG[kind], 0, 0, PW, PH); return; }
  ctx.drawImage(IMG.s3a, 0, 0, PW, PH);
  ctx.drawImage(stripB, S3B_X, 0, PW, PH); // science plate with feathered left edge
}

// precomputed layers
let stripB = null, blurEnd = null;
function buildLayers() {
  stripB = document.createElement('canvas'); stripB.width = PW; stripB.height = PH;
  const b = stripB.getContext('2d');
  b.drawImage(IMG.s3b, 0, 0, PW, PH);
  b.globalCompositeOperation = 'destination-in';
  const g = b.createLinearGradient(0, 0, SEAM, 0);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,1)');
  b.fillStyle = g; b.fillRect(0, 0, PW, PH);
  blurEnd = document.createElement('canvas'); blurEnd.width = PW; blurEnd.height = PH;
  const e = blurEnd.getContext('2d');
  e.filter = 'blur(26px) saturate(1.1)'; e.drawImage(IMG.s5, 0, 0, PW, PH);
}

function drawPlate(s, t) {
  const [z, cx, cy] = camAt(s.keys, t - s.t0);
  ctx.save();
  ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-cx, -cy);
  ctx.imageSmoothingQuality = 'high';
  plateLayer(s.draw);
  if (s.draw === 's1') drawSignLogo(t);
  ctx.restore();
}

// The original logo, uniformly scaled onto the blank sign the hand places (scene 1).
function drawSignLogo(t) {
  const a = eout(seg(t, 1.2, 2.0));
  if (a <= 0 || !logo.naturalWidth) return;
  const d = 128, cx = 902, cy = 1398;
  const h = d * logo.naturalHeight / logo.naturalWidth;
  ctx.save(); ctx.globalAlpha = a;
  ctx.drawImage(logo, cx - d / 2, cy - h / 2, d, h);
  ctx.restore();
}

// ---------- on-screen text ----------
function layoutTokens(str, size, maxW) {
  // "A | B | C" -> items kept whole, gold separators; sentences wrap by word.
  const piped = str.includes(' | ');
  const toks = piped ? str.split(' | ').flatMap((p, i) => (i ? [{ sep: true, s: '|' }, { s: p }] : [{ s: p }]))
    : str.split(' ').map(s => ({ s }));
  setFont(size, 700);
  const space = piped ? 26 : ctx.measureText(' ').width;
  const lines = [[]]; let w = 0;
  toks.forEach(tk => {
    tk.w = ctx.measureText(tk.s).width;
    const add = (lines[lines.length - 1].length ? space : 0) + tk.w;
    if (w + add > maxW && lines[lines.length - 1].length && !tk.sep) { lines.push([]); w = 0; }
    if (tk.sep && w + add > maxW) return; // drop separator at a line break
    lines[lines.length - 1].push(tk); w += (lines[lines.length - 1].length > 1 ? space : 0) + tk.w;
  });
  // strip trailing separators
  lines.forEach(l => { while (l.length && l[l.length - 1].sep) l.pop(); while (l.length && l[0].sep) l.shift(); });
  return { lines: lines.filter(l => l.length), space };
}
function drawCaption(s, t) {
  const lt = t - s.t0;
  const inP = eout(seg(lt, 0.45, 1.05));
  const outP = seg(lt, 4.55, 5.0);
  if (inP <= 0 || outP >= 1) return;
  const size = 52, lh = 70, maxW = 880;
  const { lines, space } = layoutTokens(s.text, size, maxW);
  const boxH = lines.length * lh + 96, y0 = 1720 - boxH;
  ctx.save();
  ctx.globalAlpha = inP * (1 - outP);
  ctx.translate(0, (1 - inP) * 40);
  ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 40; ctx.shadowOffsetY = 14;
  rr(60, y0, W - 120, boxH, 30, 'rgba(8,26,46,.80)');
  ctx.shadowColor = 'transparent';
  rr(60, y0, W - 120, boxH, 30, null, 'rgba(242,182,50,.75)', 2);
  const gw = 140 * eout(seg(lt, 0.7, 1.3));
  rr(W / 2 - gw / 2, y0 + 26, gw, 6, 3, C.gold);
  lines.forEach((line, i) => {
    const la = eout(seg(lt, 0.7 + i * 0.15, 1.2 + i * 0.15));
    const lw = line.reduce((a, tk, k) => a + tk.w + (k ? space : 0), 0);
    let x = W / 2 - lw / 2;
    const y = y0 + 70 + lh / 2 + i * lh;
    ctx.save(); ctx.globalAlpha *= la; ctx.translate(0, (1 - la) * 16);
    line.forEach((tk, k) => {
      if (k) x += space;
      text(tk.s, x, y, size, tk.sep ? C.gold : '#ffffff', tk.sep ? 500 : 700, 'left');
      x += tk.w;
    });
    ctx.restore();
  });
  ctx.restore();
}

// ---------- watermark (original logo, never altered) ----------
function drawWatermark(t) {
  const a = seg(t, 0.2, 0.8) * (1 - seg(t, END + 0.3, END + 0.8));
  if (a <= 0 || !logo.naturalWidth) return;
  const d = 132, h = d * logo.naturalHeight / logo.naturalWidth;
  ctx.save(); ctx.globalAlpha = a;
  ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 18; ctx.shadowOffsetY = 4;
  ctx.drawImage(logo, W - 44 - d, 48, d, h);
  ctx.restore();
}

// ---------- end card ----------
function drawEnd(t) {
  const lt = t - END;
  if (lt < -0.1) return;
  // studio softens into the brand background while the camera keeps pulling back
  const bp = seg(lt, 0, 0.9);
  const z = lerp(0.86, 0.84, seg(lt, 0, 5)) * lerp(1, 1.0, 0);
  ctx.save(); ctx.globalAlpha = bp;
  ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-648, -1152);
  ctx.drawImage(blurEnd, 0, 0);
  ctx.restore();
  const np = eout(seg(lt, 0.3, 1.4));
  const g = ctx.createRadialGradient(W / 2, 760, 80, W / 2, 900, 1300);
  g.addColorStop(0, `rgba(22,58,92,${0.9 * np})`); g.addColorStop(1, `rgba(6,18,33,${0.97 * np})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // gold hairlines
  const hl = eout(seg(lt, 1.0, 1.8));
  if (hl > 0) {
    rr(W / 2 - 300 * hl, 1110, 600 * hl, 2, 1, 'rgba(242,182,50,.8)');
    rr(W / 2 - 160 * hl, 1660, 320 * hl, 2, 1, 'rgba(242,182,50,.6)');
  }
  // large centred original logo
  const la = eout(seg(lt, 0.5, 1.4));
  if (la > 0 && logo.naturalWidth) {
    const halo = ctx.createRadialGradient(W / 2, 640, 180, W / 2, 640, 480);
    halo.addColorStop(0, `rgba(242,182,50,${0.28 * la})`); halo.addColorStop(1, 'rgba(242,182,50,0)');
    ctx.fillStyle = halo; ctx.fillRect(0, 100, W, 1100);
    const d = 600 * lerp(0.94, 1, la), h = d * logo.naturalHeight / logo.naturalWidth;
    ctx.save(); ctx.globalAlpha = la;
    ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = 50; ctx.shadowOffsetY = 18;
    ctx.drawImage(logo, W / 2 - d / 2, 640 - h / 2, d, h);
    ctx.restore();
  }
  // final card text (exact wording)
  const rows = [
    [FINAL[0], 1205, 48, '#ffffff', 800, 1.5],
    [FINAL[1], 1330, 38, '#ffffff', 600, 2.1],
    [FINAL[2], 1400, 38, '#ffffff', 600, 2.3],
    [FINAL[3], 1470, 38, '#ffffff', 600, 2.5],
    [FINAL[4], 1580, 42, C.gold, 800, 2.8],
  ];
  rows.forEach(([s, y, size, col, wt, at]) => {
    const a = eout(seg(lt, at, at + 0.6));
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = a; ctx.translate(0, (1 - a) * 18);
    let sz = size; setFont(sz, wt); while (ctx.measureText(s).width > W - 120) { sz -= 2; setFont(sz, wt); }
    text(s, W / 2, y, sz, col, wt);
    ctx.restore();
  });
}

// ---------- frame ----------
function renderAt(t) {
  t = clamp(t, 0, DUR - 1e-4);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  SCENES.forEach((s, i) => {
    const next = SCENES[i + 1];
    const tEnd = next ? next.t0 : END + 1;
    if (t < s.t0 - XF || t > tEnd + 0.05) return;
    const a = i === 0 ? 1 : seg(t, s.t0 - XF, s.t0);
    ctx.save(); ctx.globalAlpha = esine(a); drawPlate(s, t); ctx.restore();
  });
  // warm light + gentle vignette for a premium macro look
  ctx.save(); ctx.globalCompositeOperation = 'soft-light';
  const lg = ctx.createRadialGradient(W * 0.8, H * 0.15, 0, W * 0.8, H * 0.15, 1300);
  lg.addColorStop(0, 'rgba(255,200,130,.35)'); lg.addColorStop(1, 'rgba(255,200,130,0)');
  ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H); ctx.restore();
  const vg = ctx.createRadialGradient(W / 2, H * 0.48, H * 0.32, W / 2, H * 0.5, H * 0.8);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(15,8,0,.42)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  const bg = ctx.createLinearGradient(0, 1300, 0, H);
  bg.addColorStop(0, 'rgba(0,0,0,0)'); bg.addColorStop(1, 'rgba(0,0,0,.4)');
  ctx.fillStyle = bg; ctx.fillRect(0, 1300, W, H - 1300);
  SCENES.forEach(s => drawCaption(s, t));
  drawEnd(t);
  drawWatermark(t);
  const fi = 1 - seg(t, 0, 0.5);
  if (fi > 0) { ctx.fillStyle = `rgba(0,0,0,${fi})`; ctx.fillRect(0, 0, W, H); }
}

window.DUR = DUR;
window.renderAt = renderAt;
window.ready = Promise.all([
  logo.decode().catch(() => {}),
  ...Object.values(IMG).map(i => i.decode().catch(() => {})),
  document.fonts.load(`800 40px Inter`), document.fonts.load(`700 40px Inter`),
  document.fonts.load(`600 40px Inter`), document.fonts.load(`500 40px Inter`),
]).then(() => { buildLayers(); renderAt(0); });
