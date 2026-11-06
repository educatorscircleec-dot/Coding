// EduCrew "Miniature World" reel — 15s, 1080x1920.
// Uses the four illustrated scene plates from the reference reel, rebuilt with
// smooth camera glides, themed glyph swirls, animated caption cards, story-style
// progress, light-flash transitions and an animated end card synced to the music.
// Everything is a pure function of time t, so preview and MP4 render match.

const W = 1080, H = 1920, DUR = 15;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const FONT = 'Inter, "DejaVu Sans", sans-serif';

const C = {
  navy: '#13304d', navy2: '#0b1f33', gold: '#f2b632', cream: '#fff8ec',
  teal: '#1fa3a8', purple: '#8a4fd1', green: '#5fb33a', orange: '#f08a24', red: '#e25545',
};

function load(src) { const i = new Image(); i.src = src; return i; }
const logo = load('assets/educrew-logo.png');
const SCENES = [
  {
    img: load('assets/plates/math.jpg'), t0: 0, t1: 3, color: C.teal, icon: '±',
    title: 'MATHEMATICS', sub: ['Curriculum', 'Workbooks', 'Problem-solving'],
    cam: [{ z: 1.38, cx: 420, cy: 862 }, { z: 1.54, cx: 600, cy: 830 }],
    src: [440, 560], glyphs: ['1', '2', '3', '7', '+', '−', '×', '÷', '=', 'π', '√', '%', 'tri', 'sq', 'hex'],
  },
  {
    img: load('assets/plates/ela.jpg'), t0: 3, t1: 6, color: C.purple, icon: 'Aa',
    title: 'ENGLISH LANGUAGE ARTS', sub: ['Reading', 'Vocabulary', 'Learning resources'],
    cam: [{ z: 1.40, cx: 640, cy: 862 }, { z: 1.56, cx: 520, cy: 840 }],
    src: [600, 900], glyphs: ['A', 'a', 'B', 'b', 'C', 'Aa', 'E', 'g', 'Q', 'r', '?', '!', '“ ”', 'abc', 'star'],
  },
  {
    img: load('assets/plates/science.jpg'), t0: 6, t1: 9, color: C.green, icon: 'atom',
    title: 'SCIENCE', sub: ['Experiments', 'Models', 'Inquiry-based learning'],
    cam: [{ z: 1.38, cx: 690, cy: 862 }, { z: 1.52, cx: 520, cy: 860 }],
    src: [720, 560], glyphs: ['atom', 'atom', 'bubble', 'bubble', 'hex', 'H₂O', 'CO₂', 'DNA', 'star', 'bubble', 'circ'],
  },
  {
    img: load('assets/plates/studio.jpg'), t0: 9, t1: 12, color: C.orange, icon: 'play',
    title: 'ACADEMIC CONTENT STUDIO', sub: ['Assessments', 'Teacher guides', 'LMS-ready lessons'],
    cam: [{ z: 1.40, cx: 430, cy: 862 }, { z: 1.52, cx: 660, cy: 835 }],
    src: [560, 330], glyphs: ['check', 'check', 'play', 'sq', 'A+', '✓', 'doc', 'star', '100'],
  },
];
const XF = 0.32;      // half-length of the scene crossfade (s)
const END = 12.0;     // end card starts on the music hit

// ---------- helpers ----------
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, p) => a + (b - a) * p;
const eio = p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
const esine = p => 0.5 - 0.5 * Math.cos(Math.PI * p);
const eout = p => 1 - Math.pow(1 - p, 3);
const eback = p => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
function rng(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function rr(x, y, w, h, r, fill, stroke, lw = 2) {
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
}
function circ(x, y, r, fill, stroke, lw = 2) {
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
}
function poly(pts, fill, stroke, lw = 2) {
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
  ctx.closePath();
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
}
function text(s, x, y, size, color, weight = 700, align = 'center', spacing = 0) {
  ctx.font = `${weight} ${size}px ${FONT}`;
  ctx.fillStyle = color; ctx.textAlign = align; ctx.textBaseline = 'middle';
  ctx.letterSpacing = spacing + 'px';
  ctx.fillText(s, x, y);
  ctx.letterSpacing = '0px';
}
function textW(s, size, weight = 700, spacing = 0) {
  ctx.font = `${weight} ${size}px ${FONT}`; ctx.letterSpacing = spacing + 'px';
  const w = ctx.measureText(s).width; ctx.letterSpacing = '0px'; return w;
}

// ---------- glyphs ----------
function drawGlyph(g, s, col) {
  ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = Math.max(2, s * 0.12);
  ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  switch (g) {
    case 'tri': poly([[0, -s * 0.55], [s * 0.55, s * 0.42], [-s * 0.55, s * 0.42]], null, col, ctx.lineWidth); break;
    case 'sq': ctx.strokeRect(-s * 0.42, -s * 0.42, s * 0.84, s * 0.84); break;
    case 'hex': poly([...Array(6)].map((_, k) => [Math.cos(k * 1.047) * s * 0.52, Math.sin(k * 1.047) * s * 0.52]), null, col, ctx.lineWidth); break;
    case 'circ': circ(0, 0, s * 0.42, null, col, ctx.lineWidth); break;
    case 'bubble':
      circ(0, 0, s * 0.42, 'rgba(255,255,255,.25)', col, ctx.lineWidth * 0.7);
      circ(-s * 0.14, -s * 0.14, s * 0.1, 'rgba(255,255,255,.9)'); break;
    case 'star':
      poly([...Array(10)].map((_, k) => { const r = k % 2 ? s * 0.24 : s * 0.58, a = k * 0.628 - 1.571; return [Math.cos(a) * r, Math.sin(a) * r]; }), col); break;
    case 'atom':
      ctx.lineWidth = Math.max(1.6, s * 0.07);
      for (let k = 0; k < 3; k++) { ctx.beginPath(); ctx.ellipse(0, 0, s * 0.62, s * 0.22, k * 1.047, 0, 7); ctx.stroke(); }
      circ(0, 0, s * 0.13, col); break;
    case 'check':
      rr(-s * 0.48, -s * 0.48, s * 0.96, s * 0.96, s * 0.2, 'rgba(255,255,255,.85)', col, ctx.lineWidth * 0.6);
      ctx.beginPath(); ctx.moveTo(-s * 0.24, 0); ctx.lineTo(-s * 0.05, s * 0.2); ctx.lineTo(s * 0.28, -s * 0.22); ctx.stroke(); break;
    case 'play':
      rr(-s * 0.55, -s * 0.4, s * 1.1, s * 0.8, s * 0.14, col);
      poly([[-s * 0.12, -s * 0.2], [s * 0.22, 0], [-s * 0.12, s * 0.2]], '#fff'); break;
    case 'doc':
      rr(-s * 0.36, -s * 0.48, s * 0.72, s * 0.96, s * 0.08, '#fff', col, ctx.lineWidth * 0.6);
      for (let k = 0; k < 3; k++) { ctx.beginPath(); ctx.moveTo(-s * 0.2, -s * 0.2 + k * s * 0.2); ctx.lineTo(s * 0.2, -s * 0.2 + k * s * 0.2); ctx.stroke(); }
      break;
    default: {
      const sz = g.length > 2 ? s * 0.8 : s * 1.15;
      ctx.lineWidth = sz * 0.16; ctx.strokeStyle = 'rgba(255,255,255,.9)';
      ctx.font = `800 ${sz}px ${FONT}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.strokeText(g, 0, 0);
      ctx.fillStyle = col; ctx.fillText(g, 0, 0);
    }
  }
}

// themed "steam" swirl, generated once per scene with a fixed seed
const PAL = [C.teal, C.purple, C.green, C.gold, C.orange, C.red, '#2f6fd6'];
SCENES.forEach((s, si) => {
  const r = rng(11 + si * 97);
  s.parts = [];
  for (let i = 0; i < 46; i++) {
    s.parts.push({
      birth: s.t0 + 0.25 + (i / 46) * 2.3 + r() * 0.1, life: 1.6 + r() * 0.7,
      g: s.glyphs[Math.floor(r() * s.glyphs.length)],
      col: r() < 0.45 ? s.color : PAL[Math.floor(r() * PAL.length)],
      sp: 150 + r() * 110, f: 1.6 + r() * 2.2, ph: r() * 6.28, amp: 8 + r() * 14, drift: (r() - 0.5) * 90,
      size: 32 + r() * 28, rot: (r() - 0.5) * 2.2, ox: (r() - 0.5) * 120,
    });
  }
  s.sparks = [];
  for (let i = 0; i < 18; i++) s.sparks.push({ x: 200 + r() * 680, y: 300 + r() * 1200, ph: r(), sz: 6 + r() * 10 });
});

// ---------- precomputed layers ----------
let collage = null;
function buildCollage() {
  const off = document.createElement('canvas'); off.width = W; off.height = H;
  const o = off.getContext('2d');
  o.filter = 'blur(22px) saturate(1.15)';
  const cw = W / 2, ch = H / 2;
  SCENES.forEach((s, i) => {
    const x = (i % 2) * cw, y = Math.floor(i / 2) * ch;
    // clean band of the plate, cover-fit into the cell
    const sw = 1080, sh = 1405, sc = Math.max(cw / sw, ch / sh) * 1.1;
    o.drawImage(s.img, 0, 160, sw, sh, x + (cw - sw * sc) / 2, y + (ch - sh * sc) / 2, sw * sc, sh * sc);
  });
  o.filter = 'none';
  collage = off;
}

// ---------- scene rendering ----------
function camFor(s, t) {
  // camera glides through the scene and a bit beyond, so crossfades stay in motion
  const p = (t - (s.t0 - XF)) / (s.t1 - s.t0 + 2 * XF);
  const e = esine(clamp(p, -0.2, 1.2));
  const a = s.cam[0], b = s.cam[1];
  return { z: lerp(a.z, b.z, e), cx: lerp(a.cx, b.cx, e), cy: lerp(a.cy, b.cy, e) };
}
function withCam(cam, fn) {
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(cam.z, cam.z); ctx.translate(-cam.cx, -cam.cy); fn(); ctx.restore();
}
function drawParticles(s, t, cam) {
  const [bx, by] = s.src;
  // soft glow at the source
  const gp = seg(t, s.t0, s.t0 + 0.6) * (1 - seg(t, s.t1 - 0.3, s.t1 + 0.2));
  if (gp > 0) {
    const g = ctx.createRadialGradient(bx, by, 0, bx, by - 30, 220);
    g.addColorStop(0, `rgba(255,220,140,${0.45 * gp})`); g.addColorStop(1, 'rgba(255,220,140,0)');
    ctx.fillStyle = g; ctx.fillRect(bx - 240, by - 260, 480, 480);
  }
  s.parts.forEach(p => {
    const age = t - p.birth; if (age < 0 || age > p.life) return;
    const u = age / p.life;
    const y = by - p.sp * age - 30 * age * age;
    const x = bx + p.ox * Math.min(1, age * 1.8) + Math.sin(age * p.f + p.ph) * (p.amp + age * 38) + p.drift * age;
    const a = Math.min(1, u * 5) * (1 - u * u);
    ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y);
    ctx.rotate(p.rot * age + Math.sin(age * 2 + p.ph) * 0.25);
    const sz = p.size * (0.55 + 0.55 * Math.min(1, age * 1.6)) / cam.z;
    ctx.shadowColor = 'rgba(255,255,255,.9)'; ctx.shadowBlur = 12;
    drawGlyph(p.g, sz, p.col);
    ctx.restore();
  });
}
function drawScene(s, t) {
  const cam = camFor(s, t);
  ctx.imageSmoothingQuality = 'high';
  withCam(cam, () => {
    ctx.drawImage(s.img, 0, 0);
    drawParticles(s, t, cam);
  });
  // twinkles in screen space
  s.sparks.forEach(k => {
    const ph = ((t - s.t0) * 0.9 + k.ph) % 1;
    const a = Math.sin(ph * Math.PI) ** 3;
    if (a < 0.02) return;
    ctx.save(); ctx.globalAlpha = a * 0.9; ctx.translate(k.x, k.y); ctx.rotate(ph);
    ctx.shadowColor = '#fff3c4'; ctx.shadowBlur = 14;
    poly([[0, -k.sz], [k.sz * 0.22, -k.sz * 0.22], [k.sz, 0], [k.sz * 0.22, k.sz * 0.22], [0, k.sz], [-k.sz * 0.22, k.sz * 0.22], [-k.sz, 0], [-k.sz * 0.22, -k.sz * 0.22]], '#fffbe8');
    ctx.restore();
  });
}
function sceneAlpha(s, t, last) {
  const fin = s.t0 === 0 ? 1 : seg(t, s.t0 - XF, s.t0 + XF);
  // outgoing scene stays opaque underneath; the incoming one fades in on top
  return fin;
}

// ---------- overlays ----------
function drawTopBar(t) {
  const a = seg(t, 0.1, 0.6) * (1 - seg(t, END - 0.2, END + 0.2));
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a;
  // story progress segments
  const n = SCENES.length, gap = 10, x0 = 40, w = (W - 80 - gap * (n - 1)) / n;
  SCENES.forEach((s, i) => {
    const x = x0 + i * (w + gap);
    rr(x, 34, w, 7, 4, 'rgba(255,255,255,.35)');
    const p = seg(t, s.t0, s.t1);
    if (p > 0) rr(x, 34, Math.max(7, w * p), 7, 4, '#ffffff');
  });
  // brand pill
  const bw = textW('EduCrew Academic Solutions', 34, 800) + 140;
  ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 24; ctx.shadowOffsetY = 6;
  rr(40, 64, bw, 92, 46, 'rgba(11,31,51,.82)');
  ctx.shadowColor = 'transparent';
  rr(40, 64, bw, 92, 46, null, 'rgba(242,182,50,.85)', 2.5);
  circ(86, 110, 36, '#fff');
  ctx.save(); ctx.beginPath(); ctx.arc(86, 110, 35, 0, 7); ctx.clip();
  if (logo.naturalWidth) ctx.drawImage(logo, 50, 74, 72, 72 * logo.naturalHeight / logo.naturalWidth);
  ctx.restore();
  text('EduCrew Academic Solutions', 140, 111, 34, '#fff', 800, 'left');
  ctx.restore();
}
function drawIcon(kind, x, y, r, color) {
  circ(x, y, r, color);
  circ(x, y, r - 6, null, 'rgba(255,255,255,.55)', 2);
  ctx.save(); ctx.translate(x, y);
  if (kind === 'atom') drawGlyph('atom', r * 1.25, '#fff');
  else if (kind === 'play') poly([[-r * 0.25, -r * 0.36], [r * 0.42, 0], [-r * 0.25, r * 0.36]], '#fff');
  else text(kind, 0, 2, r * (kind.length > 1 ? 0.78 : 1.1), '#fff', 800);
  ctx.restore();
}
function drawCard(s, t) {
  const inP = eout(seg(t, s.t0 + 0.12, s.t0 + 0.62));
  const outP = s.t1 >= END ? seg(t, s.t1 - 0.35, s.t1) : seg(t, s.t1 - 0.25, s.t1 + 0.05);
  if (inP <= 0 || outP >= 1) return;
  const y = 1540 + (1 - inP) * 120 + outP * 60;
  ctx.save(); ctx.globalAlpha = inP * (1 - outP);
  const x = 40, w = W - 80, h = 270;
  ctx.shadowColor = 'rgba(0,0,0,.4)'; ctx.shadowBlur = 40; ctx.shadowOffsetY = 12;
  rr(x, y, w, h, 34, 'rgba(11,31,51,.86)');
  ctx.shadowColor = 'transparent';
  rr(x, y, w, h, 34, null, 'rgba(242,182,50,.8)', 2.5);
  // subject accent stripe that wipes in
  const sw = eout(seg(t, s.t0 + 0.3, s.t0 + 0.8));
  rr(x + 44, y + 40, 120 * sw, 9, 5, s.color);
  // index
  const idx = SCENES.indexOf(s) + 1;
  text(`0${idx} / 0${SCENES.length}`, x + 180 + 120 * (sw - 1) * 0, y + 45, 24, 'rgba(255,255,255,.6)', 700, 'left', 3);
  // title (letter-by-letter rise)
  const tp = seg(t, s.t0 + 0.25, s.t0 + 0.85);
  let size = 66; while (textW(s.title, size, 800, 1) > w - 200 && size > 40) size -= 2;
  ctx.save(); ctx.beginPath(); ctx.rect(x, y + 70, w, 90); ctx.clip();
  text(s.title, x + 44, y + 117 + (1 - eout(tp)) * 80, size, '#fff', 800, 'left', 1);
  ctx.restore();
  // subtitle chips
  let cx = x + 44;
  s.sub.forEach((word, i) => {
    const a = eout(seg(t, s.t0 + 0.5 + i * 0.14, s.t0 + 0.85 + i * 0.14));
    const ww = textW(word, 30, 600) + 44;
    ctx.save(); ctx.globalAlpha *= a; ctx.translate(0, (1 - a) * 18);
    rr(cx, y + 172, ww, 56, 28, 'rgba(255,255,255,.08)', s.color, 2);
    text(word, cx + ww / 2, y + 201, 30, C.gold, 600);
    ctx.restore();
    cx += ww + 12;
  });
  const ip = eback(seg(t, s.t0 + 0.35, s.t0 + 0.8));
  ctx.save(); ctx.translate(x + w - 92, y + 105); ctx.scale(ip, ip);
  drawIcon(s.icon, 0, 0, 52, s.color);
  ctx.restore();
  ctx.restore();
}
function drawFlash(t) {
  // warm light flash on each cut, peaking where the music whooshes land
  [3, 6, 9, END].forEach(c => {
    const d = Math.abs(t - c);
    if (d > 0.28) return;
    const a = (1 - d / 0.28) ** 2 * (c === END ? 0.55 : 0.32);
    const g = ctx.createRadialGradient(W * 0.7, H * 0.3, 0, W * 0.7, H * 0.3, H);
    g.addColorStop(0, `rgba(255,240,205,${a})`); g.addColorStop(1, `rgba(255,214,150,${a * 0.4})`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  });
}
function drawLightLeak(t) {
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  const x = W * (0.85 + 0.15 * Math.sin(t * 0.6)), y = H * (0.12 + 0.05 * Math.cos(t * 0.5));
  const g = ctx.createRadialGradient(x, y, 0, x, y, 700);
  g.addColorStop(0, 'rgba(255,190,110,.22)'); g.addColorStop(1, 'rgba(255,190,110,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

// ---------- end card ----------
function drawEnd(t) {
  const p = seg(t, END - 0.25, END + 0.15);
  if (p <= 0) return;
  ctx.save(); ctx.globalAlpha = p;
  if (!collage) buildCollage();
  const z = 1.05 + 0.06 * seg(t, END, DUR);
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.drawImage(collage, -W / 2, -H / 2); ctx.restore();
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, 'rgba(11,31,51,.62)'); g.addColorStop(0.5, 'rgba(11,31,51,.72)'); g.addColorStop(1, 'rgba(11,31,51,.92)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.restore();

  // logo pops on the beat
  const lp = seg(t, END, END + 0.55);
  if (lp > 0) {
    const s = eback(lp);
    ctx.save(); ctx.translate(540, 560);
    const halo = ctx.createRadialGradient(0, 0, 150, 0, 0, 420);
    halo.addColorStop(0, `rgba(242,182,50,${0.5 * lp})`); halo.addColorStop(1, 'rgba(242,182,50,0)');
    ctx.fillStyle = halo; ctx.fillRect(-460, -460, 920, 920);
    // rotating rays
    ctx.save(); ctx.rotate(t * 0.25); ctx.globalAlpha = 0.12 * lp;
    for (let k = 0; k < 12; k++) { ctx.rotate(Math.PI / 6); poly([[0, 0], [-40, -460], [40, -460]], '#ffe7a8'); }
    ctx.restore();
    ctx.scale(s, s);
    ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = 40; ctx.shadowOffsetY = 14;
    const lw = 560, lh = lw * logo.naturalHeight / logo.naturalWidth;
    if (logo.naturalWidth) ctx.drawImage(logo, -lw / 2, -lh / 2, lw, lh);
    ctx.restore();
  }
  const fade = (a, b) => eout(seg(t, a, b));
  const rise = (a, fn) => { ctx.save(); ctx.globalAlpha = a; ctx.translate(0, (1 - a) * 30); fn(); ctx.restore(); };
  rise(fade(12.35, 12.8), () => text('END-TO-END ACADEMIC', 540, 935, 54, '#fff', 800, 'center', 1));
  rise(fade(12.5, 12.95), () => text('PROJECT DELIVERY', 540, 1002, 60, C.gold, 800, 'center', 1));
  rise(fade(12.65, 13.1), () => text('FOR K–12 AND BEYOND', 540, 1066, 36, '#fff', 700, 'center', 3));
  rise(fade(12.85, 13.3), () => {
    rr(70, 1125, 940, 190, 30, 'rgba(11,31,51,.75)', 'rgba(242,182,50,.8)', 2.5);
    const subs = [['Mathematics', C.teal], ['English Language Arts', C.purple], ['Science', C.green]];
    const ws = subs.map(([s]) => textW(s, 30, 700) + 34);
    let x = 540 - (ws.reduce((a, b) => a + b, 0) + 24 * 2) / 2;
    subs.forEach(([s, c], i) => { circ(x + 9, 1185, 9, c); text(s, x + 28, 1186, 30, '#fff', 700, 'left'); x += ws[i] + 24; });
    text('Curriculum  |  Assessment  |  Instructional Design', 540, 1258, 30, C.gold, 600);
  });
  rise(fade(13.15, 13.6), () => {
    text('aaishayusuf.l@gmail.com', 540, 1395, 36, '#fff', 700);
    text('+91 9967421713   •   www.educrew.in', 540, 1450, 30, 'rgba(255,255,255,.8)', 500);
    text('@educrew.academicsolution', 540, 1505, 32, C.gold, 700);
  });
  const cta = fade(13.5, 14.0);
  if (cta > 0) {
    const pulse = 1 + 0.03 * Math.sin((t - 13.5) * 7) * cta;
    ctx.save(); ctx.globalAlpha = cta; ctx.translate(540, 1630); ctx.scale(pulse * lerp(0.8, 1, cta), pulse * lerp(0.8, 1, cta));
    ctx.shadowColor = 'rgba(242,182,50,.6)'; ctx.shadowBlur = 30;
    rr(-330, -50, 660, 100, 50, C.gold);
    ctx.shadowColor = 'transparent';
    text("LET'S BUILD BETTER LEARNING", 0, 2, 34, C.navy2, 800, 'center', 1);
    // shine sweep across the button
    const sh = seg(t, 14.0, 14.6);
    if (sh > 0 && sh < 1) {
      ctx.save(); ctx.beginPath(); ctx.roundRect(-330, -50, 660, 100, 50); ctx.clip();
      const sx = lerp(-420, 420, sh);
      const sg = ctx.createLinearGradient(sx - 70, 0, sx + 70, 0);
      sg.addColorStop(0, 'rgba(255,255,255,0)'); sg.addColorStop(0.5, 'rgba(255,255,255,.7)'); sg.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = sg; ctx.fillRect(sx - 70, -50, 140, 100); ctx.restore();
    }
    ctx.restore();
  }
  // floating confetti glyphs from all four subjects
  const r = rng(5);
  for (let i = 0; i < 26; i++) {
    const g = SCENES[i % 4].glyphs[Math.floor(r() * 6)], col = SCENES[i % 4].color;
    const x0 = r() * W, sp = 40 + r() * 60, ph = r() * 6.28, sz = 20 + r() * 18;
    const age = t - END - r() * 0.6; if (age < 0) continue;
    const y = H + 40 - ((age * sp + r() * H) % (H + 80));
    ctx.save(); ctx.globalAlpha = Math.min(1, age * 2) * 0.55; ctx.translate(x0 + Math.sin(age + ph) * 20, y); ctx.rotate(age * 0.4 + ph);
    drawGlyph(g, sz, col); ctx.restore();
  }
}

// ---------- frame ----------
function renderAt(t) {
  t = clamp(t, 0, DUR - 1e-4);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  SCENES.forEach((s, i) => {
    const last = i === SCENES.length - 1;
    if (t < s.t0 - XF || t > s.t1 + XF + (last ? 0.3 : 0)) return;
    const a = sceneAlpha(s, t, last);
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = a; drawScene(s, t); ctx.restore();
  });
  drawLightLeak(t);
  // warm vignette
  const vg = ctx.createRadialGradient(W / 2, H * 0.45, H * 0.3, W / 2, H * 0.5, H * 0.78);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(25,12,0,.5)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  // legibility gradients behind the top bar and caption card
  const tg = ctx.createLinearGradient(0, 0, 0, 260);
  tg.addColorStop(0, 'rgba(0,0,0,.35)'); tg.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = tg; ctx.fillRect(0, 0, W, 260);
  const bg = ctx.createLinearGradient(0, 1380, 0, H);
  bg.addColorStop(0, 'rgba(0,0,0,0)'); bg.addColorStop(1, 'rgba(0,0,0,.45)');
  ctx.fillStyle = bg; ctx.fillRect(0, 1380, W, H - 1380);
  SCENES.forEach(s => drawCard(s, t));
  drawTopBar(t);
  drawEnd(t);
  drawFlash(t);
  const fi = 1 - seg(t, 0, 0.3);
  if (fi > 0) { ctx.fillStyle = `rgba(0,0,0,${fi})`; ctx.fillRect(0, 0, W, H); }
  const fo = seg(t, DUR - 0.35, DUR);
  if (fo > 0) { ctx.fillStyle = `rgba(0,0,0,${fo})`; ctx.fillRect(0, 0, W, H); }
}

window.DUR = DUR;
window.renderAt = renderAt;
window.ready = Promise.all([
  logo.decode().catch(() => {}),
  ...SCENES.map(s => s.img.decode().catch(() => {})),
  document.fonts.load(`800 40px Inter`), document.fonts.load(`700 40px Inter`),
  document.fonts.load(`600 40px Inter`), document.fonts.load(`500 40px Inter`),
]).then(() => { buildCollage(); renderAt(0); });
