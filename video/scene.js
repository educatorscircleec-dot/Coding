// EduCrew Academic Studio — 15s promo, drawn on a 1080x1920 canvas.
// Everything is a pure function of time t (seconds), so the same code
// drives the live preview and the frame-by-frame MP4 render.

const W = 1080, H = 1920, DUR = 15;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');

const logo = new Image();
logo.src = 'assets/educrew-logo.png';

const C = {
  navy: '#13304d', navy2: '#0d2238', teal: '#1f8a8f', teal2: '#2aa6a6',
  gold: '#e8b03a', purple: '#6b3fa0', green: '#5aa33c', cream: '#fbf6ec',
  skin: '#f0c4a2', skinD: '#c98d68', red: '#d64541', wood: '#c99a66',
  woodD: '#8a5a35', ink: '#20324a',
};
const FONT = 'Inter, "DejaVu Sans", sans-serif';

// ---------- helpers ----------
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, p) => a + (b - a) * p;
const eio = p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
const eout = p => 1 - Math.pow(1 - p, 3);
const eback = p => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
function rng(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function keyInterp(keys, t) {
  if (t <= keys[0].t) return { ...keys[0] };
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    if (t <= b.t) {
      const p = eio((t - a.t) / (b.t - a.t));
      const o = {};
      for (const k in a) o[k] = typeof a[k] === 'number' ? lerp(a[k], b[k], p) : (p < 0.5 ? a[k] : b[k]);
      return o;
    }
  }
  return { ...keys[keys.length - 1] };
}
function rr(x, y, w, h, r, fill, stroke, lw = 2) {
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r);
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
function circ(x, y, r, fill, stroke, lw = 2) {
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
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
function line(x0, y0, x1, y1, color, lw = 2) {
  ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1);
  ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.stroke();
}

// ---------- timeline ----------
const CAM = [
  { t: 0.0, cx: 540, cy: 900, z: 0.84 },
  { t: 2.5, cx: 540, cy: 990, z: 0.92 },
  { t: 4.6, cx: 540, cy: 940, z: 1.02 },
  { t: 5.15, cx: 310, cy: 770, z: 2.05 },
  { t: 6.7, cx: 780, cy: 770, z: 2.05 },
  { t: 7.4, cx: 815, cy: 1130, z: 2.6 },
  { t: 8.3, cx: 805, cy: 1110, z: 2.5 },
  { t: 10.3, cx: 740, cy: 960, z: 1.45 },
  { t: 11.2, cx: 540, cy: 1360, z: 1.12 },
  { t: 15.0, cx: 540, cy: 1330, z: 1.04 },
];
const dioDY = t => -(1 - eout(seg(t, 0.1, 1.65))) * 1050;

// item placement in phase 2 (desk, laptop, whiteboard)
const ITEMS = { desk: 2.55, laptop: 3.15, board: 3.7 };
const DROP = 0.45, LIFT = 260;
const itemOff = (t, s) => -(1 - eio(seg(t, s, s + DROP))) * LIFT;
const itemAlpha = (t, s) => seg(t, s - 0.05, s + 0.1);
const HK2 = [
  { t: 2.30, x: 860, y: -600 },
  { t: 2.55, x: 712, y: 1170 - LIFT },
  { t: 3.00, x: 712, y: 1170 },
  { t: 3.15, x: 685, y: 1035 - LIFT },
  { t: 3.60, x: 685, y: 1035 },
  { t: 3.70, x: 365, y: 950 - LIFT },
  { t: 4.15, x: 365, y: 950 },
  { t: 4.60, x: 150, y: -700 },
];
const HK3 = [
  { t: 7.10, x: 1050, y: 450 },
  { t: 7.85, x: 845, y: 1100 },
  { t: 8.00, x: 840, y: 1152 },
  { t: 8.20, x: 870, y: 1060 },
  { t: 9.00, x: 1150, y: 500 },
];
const TRAY0 = 1480;
const trayY = t => TRAY0 + (1 - eout(seg(t, 10.45, 11.6))) * 950;

function handAt(t) {
  if (t < 2.5) {
    const d = dioDY(t);
    if (t < 1.75) return { x: 540, y: 393 + d, rot: 0.05, pose: 'pinch' };
    const p = eio(seg(t, 1.75, 2.5));
    return { x: lerp(540, 720, p), y: lerp(393, -900, p), rot: 0.05, pose: 'pinch' };
  }
  if (t < 4.6) return { ...keyInterp(HK2, t), rot: 0.1, pose: 'pinch' };
  if (t >= 7.1 && t < 9.0) return { ...keyInterp(HK3, t), rot: -0.42, pose: 'point' };
  if (t >= 10.4 && t < 12.5) {
    const ty = trayY(t) + 290;
    const back = eio(seg(t, 11.7, 12.45)) * 1100;
    return { x: 540, y: ty + 4 + back, rot: Math.PI, pose: 'flat' };
  }
  return null;
}

// ---------- desk (background) ----------
const R = rng(7);
const PLANKS = [];
for (let i = 0; i < 16; i++) {
  const grains = [];
  for (let g = 0; g < 9; g++) grains.push({ off: R(), amp: 4 + R() * 10, f: 0.002 + R() * 0.004, ph: R() * 6.28, a: 0.06 + R() * 0.1 });
  PLANKS.push({ tone: R(), grains, knot: R() < 0.4 ? { x: -400 + R() * 2200, r: 10 + R() * 14 } : null });
}
function drawDesk() {
  const x0 = -900, x1 = 2000, y0 = -800, ph = 230;
  PLANKS.forEach((p, i) => {
    const y = y0 + i * ph;
    const g = ctx.createLinearGradient(0, y, 0, y + ph);
    const l = 52 + p.tone * 8;
    g.addColorStop(0, `hsl(30,48%,${l}%)`);
    g.addColorStop(1, `hsl(28,50%,${l - 6}%)`);
    ctx.fillStyle = g; ctx.fillRect(x0, y, x1 - x0, ph);
    p.grains.forEach(gr => {
      ctx.beginPath();
      const gy = y + 10 + gr.off * (ph - 20);
      for (let x = x0; x <= x1; x += 40) {
        const yy = gy + Math.sin(x * gr.f + gr.ph) * gr.amp;
        x === x0 ? ctx.moveTo(x, yy) : ctx.lineTo(x, yy);
      }
      ctx.strokeStyle = `rgba(90,50,20,${gr.a})`; ctx.lineWidth = 2; ctx.stroke();
    });
    if (p.knot) {
      ctx.beginPath(); ctx.ellipse(p.knot.x, y + ph / 2, p.knot.r * 2.4, p.knot.r, 0, 0, 7);
      ctx.strokeStyle = 'rgba(90,50,20,.25)'; ctx.lineWidth = 3; ctx.stroke();
    }
    line(x0, y, x1, y, 'rgba(60,30,10,.35)', 3);
  });
}
function drawTea(t) {
  const x = 40, y = 1640;
  ctx.save();
  ctx.shadowColor = 'rgba(40,20,5,.35)'; ctx.shadowBlur = 30; ctx.shadowOffsetX = 14; ctx.shadowOffsetY = 18;
  circ(x, y, 118, '#f4efe6');
  ctx.restore();
  circ(x, y, 118, null, '#d9d0c1', 4);
  circ(x, y, 78, '#ffffff', '#d9d0c1', 4);
  ctx.save(); ctx.translate(x + 92, y + 6);
  rr(-6, -18, 56, 36, 18, null, '#ffffff', 16); ctx.restore();
  circ(x, y, 66, '#a8662c');
  circ(x - 14, y - 16, 24, 'rgba(255,255,255,.18)');
  // rising steam wisps
  for (let k = 0; k < 3; k++) {
    ctx.beginPath();
    for (let s = 0; s <= 1; s += 0.05) {
      const yy = y - 30 - s * 340;
      const xx = x - 25 + k * 25 + Math.sin(s * 7 + t * 2.4 + k * 2) * (8 + s * 30);
      s === 0 ? ctx.moveTo(xx, yy) : ctx.lineTo(xx, yy);
    }
    const a = 0.22 + 0.08 * Math.sin(t * 2 + k);
    ctx.strokeStyle = `rgba(255,255,255,${a})`; ctx.lineWidth = 10; ctx.lineCap = 'round'; ctx.stroke();
  }
  ctx.lineCap = 'butt';
}
function drawDeskProps() {
  // pencil
  ctx.save(); ctx.translate(990, 1880); ctx.rotate(-0.5);
  rr(-150, -11, 260, 22, 3, C.gold); poly([[110, -11], [150, 0], [110, 11]], '#f2d7b0');
  poly([[138, -3], [150, 0], [138, 3]], '#333'); rr(-170, -11, 24, 22, 3, '#e98a8a'); ctx.restore();
  // sticky notes
  ctx.save(); ctx.translate(-20, 2020); ctx.rotate(0.12);
  ctx.shadowColor = 'rgba(0,0,0,.2)'; ctx.shadowBlur = 12; ctx.shadowOffsetY = 6;
  rr(0, 0, 170, 170, 4, '#ffe27a'); ctx.restore();
}

// ---------- hand ----------
const POSES = {
  point: {
    palm: [20, -215, 78, 70],
    caps: [[-62, -190, -36, -118, 34], [24, -150, 34, -118, 30], [50, -160, 56, -128, 30], [72, -172, 74, -146, 28], [8, -160, 0, -10, 30]],
    nail: [1, -18],
  },
  pinch: {
    palm: [26, -215, 78, 70],
    caps: [[48, -150, 50, -112, 30], [70, -160, 72, -126, 30], [90, -175, 88, -146, 28], [22, -160, 4, -8, 30], [-62, -178, -8, -10, 32]],
    nail: [5, -18],
  },
  flat: {
    palm: [0, -222, 84, 74],
    caps: [[-48, -160, -50, -18, 28], [-16, -165, -16, -4, 29], [16, -165, 17, -8, 29], [47, -158, 50, -30, 27], [-78, -205, -104, -120, 32]],
    nail: null,
  },
};
function handShapes(pose, color, grow) {
  const P = POSES[pose];
  ctx.fillStyle = color; ctx.strokeStyle = color; ctx.lineCap = 'round';
  // wrist
  ctx.lineWidth = 116 + grow; ctx.beginPath(); ctx.moveTo(P.palm[0], -260); ctx.lineTo(P.palm[0] * 0.5, -360); ctx.stroke();
  ctx.beginPath(); ctx.ellipse(P.palm[0], P.palm[1], P.palm[2] + grow / 2, P.palm[3] + grow / 2, 0, 0, 7); ctx.fill();
  P.caps.forEach(c => { ctx.lineWidth = c[4] + grow; ctx.beginPath(); ctx.moveTo(c[0], c[1]); ctx.lineTo(c[2], c[3]); ctx.stroke(); });
  ctx.lineCap = 'butt';
}
function drawHand(h) {
  if (!h) return;
  ctx.save(); ctx.translate(h.x, h.y); ctx.rotate(h.rot);
  // shadow
  ctx.save(); ctx.translate(30, 26); ctx.rotate(-h.rot); ctx.rotate(h.rot);
  ctx.globalAlpha = 0.18; handShapes(h.pose, '#000', 4);
  ctx.fillStyle = '#000'; ctx.fillRect(-70, -1500, 150, 1140);
  ctx.restore();
  // sleeve
  const sx = POSES[h.pose].palm[0] * 0.5;
  const sg = ctx.createLinearGradient(sx - 72, 0, sx + 72, 0);
  sg.addColorStop(0, '#1d3c5c'); sg.addColorStop(0.5, '#2b5580'); sg.addColorStop(1, '#1a3653');
  ctx.fillStyle = sg; ctx.fillRect(sx - 72, -1500, 144, 1140);
  rr(sx - 78, -380, 156, 40, 10, '#16304b');
  handShapes(h.pose, C.skinD, 6);
  handShapes(h.pose, C.skin, 0);
  // knuckle highlight + nail
  ctx.globalAlpha = 0.25;
  const P = POSES[h.pose];
  ctx.beginPath(); ctx.ellipse(P.palm[0] - 20, P.palm[1] - 10, 30, 22, 0, 0, 7); ctx.fillStyle = '#fff'; ctx.fill();
  ctx.globalAlpha = 1;
  if (P.nail) { ctx.beginPath(); ctx.ellipse(P.nail[0], P.nail[1], 9, 12, 0, 0, 7); ctx.fillStyle = '#f8dccb'; ctx.fill(); }
  ctx.restore();
}

// ---------- diorama ----------
function drawStoryboard(x, y, w, h, t, compact) {
  rr(x, y, w, h, 3, '#ffffff');
  ctx.fillStyle = C.teal; ctx.fillRect(x, y, w, h * 0.16);
  text(compact ? 'LMS' : 'LMS · STORYBOARD', x + w / 2, y + h * 0.08, Math.max(7, h * 0.09), '#fff', 800, 'center', 1);
  const cols = compact ? 2 : 3, rows = compact ? 3 : 2;
  const pad = w * 0.06, gw = (w - pad * (cols + 1)) / cols, gh = (h * 0.84 - pad * (rows + 1)) / rows;
  const tints = [C.gold, C.purple, C.green, C.teal2, C.red, C.navy];
  let n = 0;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const fx = x + pad + c * (gw + pad), fy = y + h * 0.16 + pad + r * (gh + pad);
    rr(fx, fy, gw, gh, 2, '#eef3f7', '#c8d3de', 1);
    ctx.globalAlpha = 0.85;
    rr(fx + gw * 0.12, fy + gh * 0.18, gw * 0.4, gh * 0.45, 2, tints[n % 6]);
    ctx.globalAlpha = 1;
    line(fx + gw * 0.6, fy + gh * 0.3, fx + gw * 0.88, fy + gh * 0.3, '#9fb0c2', Math.max(1, gh * 0.06));
    line(fx + gw * 0.6, fy + gh * 0.5, fx + gw * 0.8, fy + gh * 0.5, '#9fb0c2', Math.max(1, gh * 0.06));
    line(fx + gw * 0.12, fy + gh * 0.8, fx + gw * 0.88, fy + gh * 0.8, '#c8d3de', Math.max(1, gh * 0.05));
    n++;
  }
  // progress bar that ticks along
  const pb = (t * 0.15) % 1;
  rr(x + pad, y + h - pad * 0.9, (w - 2 * pad), 3, 1, '#dde5ec');
  rr(x + pad, y + h - pad * 0.9, (w - 2 * pad) * (0.3 + 0.7 * pb), 3, 1, C.gold);
}
function drawShelfFrame(x, label, color) {
  rr(x - 8, 622, 216, 288, 6, C.wood, '#a87a4b', 3);
  rr(x, 662, 200, 240, 2, '#f1e3c9');
  rr(x + 30, 628, 140, 30, 8, color);
  text(label, x + 100, 644, 17, '#fff', 800, 'center', 2);
  rr(x - 4, 768, 208, 12, 2, '#b07e4e');
  rr(x - 4, 893, 208, 12, 2, '#b07e4e');
}
function drawMath(x) {
  drawShelfFrame(x, 'MATH', C.teal);
  // stacked workbooks
  [[C.teal, 4], [C.gold, 0], [C.navy, 8]].forEach(([c, o], i) => {
    rr(x + 10 + o, 750 - i * 19, 84, 18, 3, c, 'rgba(0,0,0,.15)', 1);
    rr(x + 14 + o, 753 - i * 19, 6, 12, 1, 'rgba(255,255,255,.6)');
  });
  text('1+2', x + 60, 722, 10, '#fff', 800);
  // protractor
  ctx.beginPath(); ctx.arc(x + 150, 768, 44, Math.PI, 0); ctx.closePath();
  ctx.fillStyle = 'rgba(232,176,58,.55)'; ctx.fill(); ctx.strokeStyle = '#b5841f'; ctx.lineWidth = 2; ctx.stroke();
  for (let a = 0; a <= 18; a++) {
    const an = Math.PI + (a / 18) * Math.PI, r0 = a % 3 ? 38 : 32;
    line(x + 150 + Math.cos(an) * r0, 768 + Math.sin(an) * r0, x + 150 + Math.cos(an) * 44, 768 + Math.sin(an) * 44, '#8a6214', 1);
  }
  circ(x + 150, 768, 4, '#8a6214');
  // number tiles
  ['1', '2', '3', '4'].forEach((d, i) => {
    rr(x + 10 + i * 30, 865, 27, 27, 4, ['#fff7e3', '#e3f4f4', '#fff7e3', '#e3f4f4'][i], '#9a8c74', 1.5);
    text(d, x + 23.5 + i * 30, 879, 16, C.ink, 800);
  });
  rr(x + 40, 836, 27, 27, 4, '#fde7e7', '#9a8c74', 1.5); text('+', x + 53.5, 850, 18, C.red, 800);
  rr(x + 70, 836, 27, 27, 4, '#e6f3df', '#9a8c74', 1.5); text('=', x + 83.5, 850, 18, C.green, 800);
  // compass
  const cx = x + 165;
  line(cx, 812, cx - 20, 892, '#6c7a89', 4); line(cx, 812, cx + 20, 892, '#6c7a89', 4);
  line(cx + 20, 880, cx + 21, 893, '#333', 3); circ(cx, 810, 7, '#8a99a8', '#4d5966', 2);
  line(cx, 795, cx, 803, '#4d5966', 4);
}
function drawEnglish(x) {
  drawShelfFrame(x, 'ENGLISH', C.purple);
  const bk = [[18, 96, C.purple], [22, 110, '#c0392b'], [16, 88, C.gold], [20, 104, C.navy], [18, 92, C.teal], [24, 112, '#7d4e2d'], [17, 98, '#9b59b6']];
  let bx = x + 8;
  bk.forEach(([w, h, c], i) => {
    rr(bx, 768 - h, w, h, 2, c, 'rgba(0,0,0,.2)', 1);
    rr(bx, 768 - h + 12, w, 5, 0, 'rgba(255,255,255,.45)');
    rr(bx, 768 - 18, w, 4, 0, 'rgba(255,255,255,.3)');
    bx += w + 2;
  });
  // leaning reader
  ctx.save(); ctx.translate(bx + 6, 768); ctx.rotate(0.32);
  rr(0, -80, 16, 80, 2, C.green, 'rgba(0,0,0,.2)', 1); ctx.restore();
  // vocabulary cards
  [['Aa', C.purple, -0.08], ['verb', C.teal, 0.04], ['noun', C.red, -0.03]].forEach(([w, c, r], i) => {
    ctx.save(); ctx.translate(x + 32 + i * 46, 893); ctx.rotate(r);
    ctx.shadowColor = 'rgba(0,0,0,.18)'; ctx.shadowBlur = 4; ctx.shadowOffsetY = 2;
    rr(-20, -60, 40, 58, 4, '#fff'); ctx.shadowColor = 'transparent';
    rr(-20, -60, 40, 9, [4, 4, 0, 0], c);
    text(w, 0, -28, w === 'Aa' ? 17 : 11, C.ink, 800); ctx.restore();
  });
  // readers stack
  [[C.gold, 0], [C.purple, 3], ['#2e86c1', -2]].forEach(([c, o], i) => {
    rr(x + 148 + o, 875 - i * 16, 46, 15, 2, c, 'rgba(0,0,0,.18)', 1);
  });
  text('READ', x + 171, 851, 8, '#fff', 800);
}
function drawScience(x) {
  drawShelfFrame(x, 'SCIENCE', C.green);
  // beaker
  rr(x + 12, 702, 46, 64, [2, 2, 8, 8], 'rgba(220,240,250,.55)', '#7aa6bd', 2);
  rr(x + 14, 732, 42, 32, [0, 0, 7, 7], 'rgba(42,166,166,.75)');
  for (let i = 0; i < 3; i++) line(x + 12, 715 + i * 14, x + 22, 715 + i * 14, '#7aa6bd', 1.5);
  // erlenmeyer flask
  poly([[x + 78, 704], [x + 90, 704], [x + 90, 724], [x + 108, 766], [x + 60, 766], [x + 78, 724]], 'rgba(220,240,250,.55)', '#7aa6bd', 2);
  poly([[x + 70, 744], [x + 98, 744], [x + 107, 764], [x + 61, 764]], 'rgba(107,63,160,.75)');
  circ(x + 84, 690, 4, 'rgba(107,63,160,.4)'); circ(x + 90, 676, 3, 'rgba(107,63,160,.3)');
  // microscope
  const mx = x + 155;
  rr(mx - 30, 756, 62, 10, 3, '#3d4a59');
  ctx.save(); ctx.translate(mx + 10, 750); ctx.rotate(-0.15);
  rr(-5, -70, 10, 72, 4, '#56677a'); ctx.restore();
  ctx.save(); ctx.translate(mx - 4, 690); ctx.rotate(-0.5);
  rr(-7, -6, 14, 52, 4, '#e8edf2', '#56677a', 2); rr(-5, -16, 10, 12, 2, '#3d4a59'); ctx.restore();
  rr(mx - 20, 728, 34, 6, 2, '#3d4a59');
  // globe
  const gx = x + 50, gy = 838;
  ctx.beginPath(); ctx.arc(gx, gy, 38, -2.2, 0.9); ctx.strokeStyle = '#b5841f'; ctx.lineWidth = 3; ctx.stroke();
  circ(gx, gy, 30, '#3a8fd1');
  ctx.save(); ctx.beginPath(); ctx.arc(gx, gy, 30, 0, 7); ctx.clip();
  ctx.fillStyle = '#6cbf4a';
  ctx.beginPath(); ctx.ellipse(gx - 10, gy - 8, 13, 9, 0.6, 0, 7); ctx.fill();
  ctx.beginPath(); ctx.ellipse(gx + 12, gy + 10, 10, 13, -0.4, 0, 7); ctx.fill();
  ctx.restore();
  line(gx, gy + 38, gx, 885, '#b5841f', 4); rr(gx - 22, 884, 44, 8, 3, '#8a6214');
  // planets
  circ(x + 120, 872, 18, '#e8a33a'); circ(x + 114, 866, 5, 'rgba(255,255,255,.35)');
  ctx.beginPath(); ctx.ellipse(x + 120, 872, 30, 7, -0.3, 0, 7); ctx.strokeStyle = '#c9822a'; ctx.lineWidth = 3; ctx.stroke();
  circ(x + 168, 878, 13, '#c0392b'); circ(x + 178, 852, 8, '#7fb3e0'); circ(x + 150, 842, 6, '#bdc3c7');
}
function drawWhiteboard(t) {
  rr(206, 942, 318, 214, 6, '#aeb7c1');
  rr(214, 950, 302, 198, 3, '#ffffff');
  text('CURRICULUM MAP', 365, 970, 14, C.navy, 800, 'center', 2);
  const cols = [[C.teal, 'MATH'], [C.purple, 'ELA'], [C.green, 'SCI']];
  cols.forEach(([c, l], i) => {
    const x = 236 + i * 96;
    rr(x, 990, 70, 22, 5, c); text(l, x + 35, 1001, 11, '#fff', 800);
    for (let k = 0; k < 3; k++) {
      rr(x + 6, 1024 + k * 36, 58, 24, 5, '#fff', c, 2.5);
      text(`Unit ${k + 1}`, x + 35, 1036 + k * 36, 10, C.ink, 700);
      if (k < 2) line(x + 35, 1048 + k * 36, x + 35, 1060 + k * 36, c, 2.5);
    }
    if (i < 2) { line(x + 64, 1072, x + 102, 1072, '#c4ccd4', 2); }
  });
  rr(300, 1156, 130, 8, 2, '#8d97a2');
  rr(320, 1150, 30, 7, 3, C.red); rr(360, 1150, 30, 7, 3, C.teal);
}
function drawDeskTiny() {
  rr(540, 1170, 345, 20, 4, C.woodD);
  rr(540, 1170, 345, 6, [4, 4, 0, 0], '#a3714a');
  rr(556, 1190, 16, 150, 2, '#74482a'); rr(853, 1190, 16, 150, 2, '#74482a');
  rr(700, 1190, 140, 46, 3, '#9a6a44'); rr(755, 1210, 30, 6, 3, C.gold);
}
function drawLaptop(t) {
  rr(593, 1030, 184, 130, 8, '#2c3440');
  drawStoryboard(602, 1039, 166, 112, t, false);
  poly([[575, 1172], [795, 1172], [780, 1158], [590, 1158]], '#aeb6bf', '#7e8893', 1.5);
}
function drawWorkbook(t) {
  const o = eout(seg(t, 8.0, 8.55));
  const ang = o * Math.PI, c = Math.cos(ang);
  // page block thickness
  rr(790, 1168, 90, 8, 1, '#efe9dc', '#cbbfa6', 1);
  if (o > 0) rr(790 - 90 * Math.max(0, -c), 1168, 90 * Math.max(0, -c), 8, 1, '#efe9dc', '#cbbfa6', 1);
  // right page (always under the cover)
  poly([[790, 1170], [880, 1170], [872, 1146], [796, 1146]], '#ffffff', '#cbbfa6', 1);
  for (let i = 0; i < 4; i++) line(804, 1152 + i * 5, 866 - i * 2, 1152 + i * 5, '#c9d2dc', 1.5);
  if (c >= 0) {
    // cover still lying on the right side
    const wv = 90 * c;
    poly([[790, 1170], [790 + wv, 1170], [790 + wv - 8 * c, 1146], [796, 1146]], C.teal, '#176c70', 1.5);
    if (c > 0.6) { text('MATH', 790 + wv / 2 + 2, 1158, 11 * c, '#fff', 800); circ(790 + wv * 0.8, 1158, 4 * c, C.gold); }
  } else {
    // left page revealed + inside cover
    const wv = 90 * -c;
    poly([[790, 1170], [790 - wv, 1170], [790 - wv + 8 * -c, 1146], [784, 1146]], '#ffffff', '#cbbfa6', 1);
    if (-c > 0.7) {
      text('x² + 3', 745, 1153, 9, C.teal, 800); text('a b c', 748, 1164, 8, C.purple, 700);
    }
    rr(789, 1146, 2, 24, 0, '#d8cfbd');
  }
}
function drawSign(t) {
  ctx.save();
  rr(244, 389, 592, 157, 16, C.gold);
  const g = ctx.createLinearGradient(0, 395, 0, 540);
  g.addColorStop(0, '#1b3d60'); g.addColorStop(1, C.navy2);
  rr(250, 395, 580, 145, 12, g);
  const p = eback(seg(t, 3.95, 4.45));
  const a = seg(t, 3.95, 4.2);
  if (a > 0) {
    ctx.globalAlpha = a;
    ctx.save(); ctx.translate(330, 468); ctx.scale(p, p);
    circ(0, 0, 64, '#fff');
    ctx.beginPath(); ctx.arc(0, 0, 62, 0, 7); ctx.clip();
    if (logo.complete && logo.naturalWidth) ctx.drawImage(logo, -63, -62, 126, 124);
    ctx.restore();
    const ta = seg(t, 4.1, 4.45);
    ctx.globalAlpha = ta;
    text('EduCrew', 412 + (1 - ta) * 20, 452, 50, '#ffffff', 800, 'left');
    text('ACADEMIC STUDIO', 414 + (1 - ta) * 20, 500, 20, C.gold, 700, 'left', 4);
    // shine sweep
    const sw = seg(t, 4.3, 4.9);
    if (sw > 0 && sw < 1) {
      ctx.globalAlpha = 0.35 * Math.sin(sw * Math.PI);
      ctx.save(); ctx.beginPath(); ctx.roundRect(250, 395, 580, 145, 12); ctx.clip();
      const sx = lerp(200, 900, sw);
      const sg = ctx.createLinearGradient(sx - 60, 0, sx + 60, 0);
      sg.addColorStop(0, 'rgba(255,255,255,0)'); sg.addColorStop(0.5, '#fff'); sg.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = sg; ctx.fillRect(sx - 60, 395, 120, 145); ctx.restore();
    }
  } else {
    ctx.globalAlpha = 0.25;
    rr(280, 425, 520, 85, 8, null, C.gold, 2);
  }
  ctx.restore();
}
function drawDiorama(t) {
  const dy = dioDY(t);
  ctx.save(); ctx.translate(0, dy);
  // drop shadow on the desk grows as the studio lands
  const land = seg(t, 0.4, 1.65);
  ctx.save();
  ctx.shadowColor = `rgba(40,20,5,${0.15 + 0.35 * land})`;
  ctx.shadowBlur = lerp(140, 50, land);
  ctx.shadowOffsetX = lerp(60, 26, land); ctx.shadowOffsetY = lerp(110, 34, land);
  rr(120, 540, 840, 880, 18, '#e2c79c');
  ctx.restore();
  // box shell
  const sg = ctx.createLinearGradient(120, 0, 960, 0);
  sg.addColorStop(0, '#d9bb8c'); sg.addColorStop(0.5, '#ecd5ae'); sg.addColorStop(1, '#d3b382');
  rr(120, 540, 840, 880, 18, sg, '#b48c5a', 3);
  // interior: ceiling, side walls, floor, back wall
  poly([[150, 570], [930, 570], [890, 600], [190, 600]], '#d8c4a2');
  poly([[150, 570], [190, 600], [190, 1300], [150, 1390]], '#e4d3b5');
  poly([[930, 570], [890, 600], [890, 1300], [930, 1390]], '#dcc8a6');
  const fg = ctx.createLinearGradient(0, 1300, 0, 1390);
  fg.addColorStop(0, '#b9844f'); fg.addColorStop(1, '#d29c62');
  poly([[150, 1390], [190, 1300], [890, 1300], [930, 1390]], fg);
  for (let i = 1; i < 8; i++) {
    const xb = lerp(190, 890, i / 8), xf = lerp(150, 930, i / 8);
    line(xb, 1300, xf, 1390, 'rgba(90,50,20,.25)', 1.5);
  }
  const bw = ctx.createLinearGradient(0, 600, 0, 1300);
  bw.addColorStop(0, '#fdf8ef'); bw.addColorStop(1, '#f1e6d2');
  ctx.fillStyle = bw; ctx.fillRect(190, 600, 700, 700);
  // warm ceiling light
  const lg = ctx.createRadialGradient(540, 600, 10, 540, 700, 520);
  lg.addColorStop(0, 'rgba(255,230,170,.35)'); lg.addColorStop(1, 'rgba(255,230,170,0)');
  ctx.fillStyle = lg; ctx.fillRect(190, 600, 700, 700);
  // shelves
  drawMath(212); drawEnglish(440); drawScience(668);
  // placed items
  const placed = (s, fn) => {
    const a = itemAlpha(t, s); if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = a; ctx.translate(0, itemOff(t, s)); fn(); ctx.restore();
  };
  placed(ITEMS.board, () => drawWhiteboard(t));
  placed(ITEMS.desk, () => { drawDeskTiny(); });
  placed(ITEMS.laptop, () => drawLaptop(t));
  placed(ITEMS.desk, () => drawWorkbook(t));
  // inner rim shading
  ctx.strokeStyle = 'rgba(80,50,20,.25)'; ctx.lineWidth = 6;
  ctx.strokeRect(153, 573, 774, 814);
  drawSign(t);
  ctx.restore();
}

// ---------- hero particles ----------
const GLYPHS = ['1', '2', '3', '7', '9', '+', '×', '÷', 'π', '√', '=', 'A', 'a', 'B', 'c', 'E', 'g', 'Q', 'tri', 'sq', 'hex', 'circ', 'atom', 'atom', 'star'];
const PCOL = [C.teal2, C.purple, C.green, C.gold, C.navy, '#e1574c'];
const PARTS = [];
{
  const r = rng(42);
  for (let i = 0; i < 130; i++) {
    PARTS.push({
      birth: 8.25 + (i / 130) * 1.8 + r() * 0.1, life: 1.9 + r() * 0.6,
      g: GLYPHS[Math.floor(r() * GLYPHS.length)], col: PCOL[Math.floor(r() * PCOL.length)],
      sp: 170 + r() * 120, f: 2 + r() * 2.2, ph: r() * 6.28, amp: 6 + r() * 12, drift: (r() - 0.5) * 60,
      size: 16 + r() * 16, rot: (r() - 0.5) * 3, ox: (r() - 0.5) * 80,
    });
  }
}
function drawGlyph(g, s, col) {
  ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = Math.max(1.5, s * 0.14);
  if (g === 'tri') poly([[0, -s * 0.6], [s * 0.55, s * 0.4], [-s * 0.55, s * 0.4]], null, col, ctx.lineWidth);
  else if (g === 'sq') { ctx.strokeRect(-s * 0.45, -s * 0.45, s * 0.9, s * 0.9); }
  else if (g === 'hex') poly([...Array(6)].map((_, k) => [Math.cos(k * 1.047) * s * 0.55, Math.sin(k * 1.047) * s * 0.55]), null, col, ctx.lineWidth);
  else if (g === 'circ') circ(0, 0, s * 0.45, null, col, ctx.lineWidth);
  else if (g === 'star') {
    poly([...Array(10)].map((_, k) => { const rr2 = k % 2 ? s * 0.25 : s * 0.6, a = k * 0.628 - 1.57; return [Math.cos(a) * rr2, Math.sin(a) * rr2]; }), col);
  } else if (g === 'atom') {
    ctx.lineWidth = Math.max(1.2, s * 0.08);
    for (let k = 0; k < 3; k++) { ctx.beginPath(); ctx.ellipse(0, 0, s * 0.7, s * 0.25, k * 1.047, 0, 7); ctx.stroke(); }
    circ(0, 0, s * 0.14, col);
  } else text(g, 0, 0, s * 1.25, col, 800);
}
function drawParticles(t) {
  const bx = 790, by = 1146;
  const open = seg(t, 8.1, 8.6);
  if (open > 0) {
    const fade = 1 - seg(t, 10.2, 11.2);
    const gl = ctx.createRadialGradient(bx, by, 0, bx, by - 40, 180);
    gl.addColorStop(0, `rgba(255,214,120,${0.55 * open * fade})`); gl.addColorStop(1, 'rgba(255,214,120,0)');
    ctx.fillStyle = gl; ctx.fillRect(bx - 200, by - 260, 400, 330);
  }
  PARTS.forEach(p => {
    const age = t - p.birth; if (age < 0 || age > p.life) return;
    const u = age / p.life;
    // steam-like rise: slow start, curling sway that widens as it climbs
    const y = by - 6 - p.sp * age - 40 * age * age;
    const x = bx + p.ox * Math.min(1, age * 2) + Math.sin(age * p.f + p.ph) * (p.amp + age * 40) + p.drift * age;
    const a = Math.min(1, u * 6) * (1 - Math.pow(u, 2));
    ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.rotate(p.rot * age + Math.sin(age * 2 + p.ph) * 0.3);
    const s = p.size * (0.6 + 0.6 * Math.min(1, age * 1.5));
    drawGlyph(p.g, s, p.col);
    ctx.restore();
  });
}

// ---------- tray ----------
function drawTray(t) {
  if (t < 10.4) return;
  const ty = trayY(t);
  ctx.save();
  ctx.shadowColor = 'rgba(40,20,5,.45)'; ctx.shadowBlur = 40; ctx.shadowOffsetX = 18; ctx.shadowOffsetY = 26;
  rr(140, ty, 800, 300, 28, '#173a5c');
  ctx.restore();
  rr(140, ty, 800, 300, 28, null, C.gold, 5);
  rr(160, ty + 20, 760, 260, 18, '#1f4970');
  // teacher guide
  ctx.save(); ctx.translate(180, ty + 36); ctx.rotate(-0.02);
  ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 10; ctx.shadowOffsetY = 6;
  rr(0, 0, 170, 225, 6, '#f7f2e8'); ctx.shadowColor = 'transparent';
  rr(0, 0, 170, 225, 6, null, '#d9cdb5', 2);
  rr(0, 0, 170, 64, [6, 6, 0, 0], C.navy);
  text('TEACHER', 85, 26, 20, '#fff', 800, 'center', 2); text('GUIDE', 85, 49, 16, C.gold, 800, 'center', 4);
  for (let i = 0; i < 5; i++) line(18, 92 + i * 22, 152 - (i % 2) * 30, 92 + i * 22, '#c8cfd8', 4);
  circ(140, 200, 12, C.gold); ctx.restore();
  // student workbook
  ctx.save(); ctx.translate(368, ty + 34); ctx.rotate(0.02);
  ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 10; ctx.shadowOffsetY = 6;
  rr(0, 0, 170, 225, 6, C.teal); ctx.shadowColor = 'transparent';
  rr(0, 0, 14, 225, [6, 0, 0, 6], '#176c70');
  text('STUDENT', 92, 34, 20, '#fff', 800, 'center', 2); text('WORKBOOK', 92, 58, 15, C.gold, 800, 'center', 2);
  ctx.save(); ctx.translate(60, 130); drawGlyph('tri', 40, '#fff'); ctx.restore();
  ctx.save(); ctx.translate(120, 120); ctx.globalAlpha = 0.9; text('Aa', 0, 0, 34, '#fff', 800); ctx.restore();
  ctx.save(); ctx.translate(92, 182); drawGlyph('atom', 46, C.gold); ctx.restore();
  ctx.restore();
  // marked assessment
  ctx.save(); ctx.translate(560, ty + 30); ctx.rotate(-0.05);
  ctx.shadowColor = 'rgba(0,0,0,.3)'; ctx.shadowBlur = 8; ctx.shadowOffsetY = 5;
  rr(0, 0, 165, 235, 3, '#ffffff'); ctx.shadowColor = 'transparent';
  text('ASSESSMENT', 82, 22, 14, C.ink, 800, 'center', 1);
  line(14, 38, 150, 38, '#d5dbe2', 2);
  for (let i = 0; i < 5; i++) {
    const y = 60 + i * 30;
    text(`${i + 1}.`, 22, y, 13, C.ink, 700);
    line(36, y, 112, y, '#c8cfd8', 4);
    ctx.beginPath(); ctx.moveTo(122, y); ctx.lineTo(128, y + 6); ctx.lineTo(140, y - 8);
    ctx.strokeStyle = C.red; ctx.lineWidth = 3.5; ctx.lineCap = 'round'; ctx.stroke(); ctx.lineCap = 'butt';
  }
  ctx.save(); ctx.translate(122, 206); ctx.rotate(-0.15);
  ctx.beginPath(); ctx.ellipse(0, 0, 34, 22, 0, 0, 7); ctx.strokeStyle = C.red; ctx.lineWidth = 3; ctx.stroke();
  text('A+', 0, 1, 22, C.red, 800); ctx.restore();
  text('95%', 44, 208, 18, C.red, 800);
  ctx.restore();
  // tablet with LMS storyboard
  ctx.save(); ctx.translate(745, ty + 38); ctx.rotate(0.03);
  ctx.shadowColor = 'rgba(0,0,0,.4)'; ctx.shadowBlur = 10; ctx.shadowOffsetY = 6;
  rr(0, 0, 160, 222, 16, '#1d232b'); ctx.shadowColor = 'transparent';
  drawStoryboard(10, 14, 140, 194, t, true);
  ctx.restore();
}

// ---------- end card (screen space) ----------
function drawEndCard(t) {
  const d = seg(t, 12.5, 13.3);
  if (d <= 0) return;
  ctx.fillStyle = `rgba(9,24,40,${0.9 * eio(d)})`; ctx.fillRect(0, 0, W, H);
  const la = eout(seg(t, 12.85, 13.6));
  if (la > 0) {
    ctx.save(); ctx.globalAlpha = la;
    const s = lerp(0.82, 1, la);
    // gold halo
    const hg = ctx.createRadialGradient(540, 820, 200, 540, 820, 470);
    hg.addColorStop(0, 'rgba(232,176,58,.35)'); hg.addColorStop(1, 'rgba(232,176,58,0)');
    ctx.fillStyle = hg; ctx.fillRect(0, 300, W, 1100);
    ctx.translate(540, 820); ctx.scale(s, s);
    if (logo.complete && logo.naturalWidth) {
      const lw = 640, lh = lw * logo.naturalHeight / logo.naturalWidth;
      ctx.drawImage(logo, -lw / 2, -lh / 2, lw, lh);
    }
    ctx.restore();
  }
  // subject pills
  const subs = [['Mathematics', C.teal2], ['English Language Arts', '#8e5cc6'], ['Science', C.green]];
  ctx.font = `700 30px ${FONT}`;
  const widths = subs.map(s => ctx.measureText(s[0]).width + 64);
  const gap = 18, total = widths.reduce((a, b) => a + b, 0) + gap * 2;
  let x = (W - total) / 2;
  subs.forEach(([s, c], i) => {
    const a = eout(seg(t, 13.35 + i * 0.18, 13.85 + i * 0.18));
    ctx.save(); ctx.globalAlpha = a; ctx.translate(0, (1 - a) * 24);
    rr(x, 1190, widths[i], 64, 32, 'rgba(255,255,255,.08)', c, 3);
    circ(x + 28, 1222, 8, c);
    text(s, x + 42, 1223, 30, '#fff', 700, 'left');
    ctx.restore();
    x += widths[i] + gap;
  });
  const ha = eout(seg(t, 13.95, 14.5));
  ctx.save(); ctx.globalAlpha = ha; ctx.translate(0, (1 - ha) * 20);
  text('End-to-end academic project delivery', 540, 1330, 30, 'rgba(255,255,255,.75)', 500);
  rr(240, 1390, 600, 84, 42, C.gold);
  text('@educrew.academicsolution', 540, 1433, 36, C.navy2, 800);
  ctx.restore();
}

// ---------- frame ----------
function renderAt(t) {
  t = clamp(t, 0, DUR);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = '#5a3a20'; ctx.fillRect(0, 0, W, H);
  const cam = keyInterp(CAM, t);
  ctx.translate(W / 2, H / 2); ctx.scale(cam.z, cam.z); ctx.translate(-cam.cx, -cam.cy);
  drawDesk();
  drawTea(t);
  drawDeskProps();
  drawDiorama(t);
  drawParticles(t);
  drawTray(t);
  drawHand(handAt(t));
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  // vignette
  const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.75);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(20,10,0,.45)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  // hero moment: dim the room slightly so the swirl pops
  const hd = seg(t, 8.0, 8.6) * (1 - seg(t, 10.0, 10.8));
  if (hd > 0) { ctx.fillStyle = `rgba(10,20,35,${0.18 * hd})`; ctx.fillRect(0, 0, W, H); }
  drawEndCard(t);
  // fade in from black
  const fi = 1 - seg(t, 0, 0.35);
  if (fi > 0) { ctx.fillStyle = `rgba(0,0,0,${fi})`; ctx.fillRect(0, 0, W, H); }
}

window.DUR = DUR;
window.renderAt = renderAt;
window.ready = Promise.all([
  logo.decode().catch(() => {}),
  document.fonts.load(`800 40px Inter`), document.fonts.load(`700 40px Inter`), document.fonts.load(`500 40px Inter`),
]).then(() => renderAt(0));
