/**
 * 生成作品封面占位图（浅色抽象几何 SVG）
 * 用法：node scripts/generate-covers.mjs
 *
 * 做好真封面后直接换成自己的图，放到 public/covers/ 即可。
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const outDir = resolve(__dirname, '../public/covers');
mkdirSync(outDir, { recursive: true });

function mulberry32(a) {
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const W = 1200;
const H = 675;

const specs = [
  { file: 'cover-01.svg', seed: 11, motif: 'rings' },
  { file: 'cover-02.svg', seed: 23, motif: 'mesh' },
  { file: 'cover-03.svg', seed: 37, motif: 'bars' },
  { file: 'cover-04.svg', seed: 51, motif: 'rings' },
  { file: 'placeholder.svg', seed: 5, motif: 'mesh' },
];

const INK = '#1b1b19';
const LINE = '#bcbcb4';
const LINE_SOFT = '#d3d3ce';

function rings(rnd) {
  const cx = 700 + rnd() * 80;
  const cy = 300 + rnd() * 40;
  const p = [];

  // 实心小圆做视觉重心
  p.push(`<circle cx="${cx.toFixed(0)}" cy="${cy.toFixed(0)}" r="9" fill="${INK}" fill-opacity="0.85"/>`);

  for (let i = 0; i < 7; i++) {
    const r = 60 + i * 54;
    p.push(
      `<circle cx="${cx.toFixed(0)}" cy="${cy.toFixed(0)}" r="${r}" fill="none" stroke="${LINE}" stroke-width="1"/>`
    );
  }

  // 外侧刻度
  for (let i = 0; i < 32; i++) {
    const ang = (i / 32) * Math.PI * 2;
    const r1 = 372;
    const r2 = i % 8 === 0 ? 352 : 362;
    p.push(
      `<line x1="${(cx + Math.cos(ang) * r1).toFixed(1)}" y1="${(cy + Math.sin(ang) * r1).toFixed(1)}" x2="${(cx + Math.cos(ang) * r2).toFixed(1)}" y2="${(cy + Math.sin(ang) * r2).toFixed(1)}" stroke="${LINE}" stroke-width="1"/>`
    );
  }

  p.push(
    `<path d="M60 ${cy} H${cx}" stroke="${LINE_SOFT}" stroke-width="1"/>`,
    `<path d="M${cx} ${H} V${cy}" stroke="${LINE_SOFT}" stroke-width="1"/>`
  );

  return p.join('');
}

function mesh(rnd) {
  const pts = [];
  for (let i = 0; i < 9; i++) pts.push([200 + rnd() * 840, 130 + rnd() * 420]);

  const lines = [];
  for (let i = 0; i < pts.length; i++) {
    for (let j = i + 1; j < pts.length; j++) {
      const d = Math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]);
      if (d < 340) {
        lines.push(
          `<line x1="${pts[i][0].toFixed(0)}" y1="${pts[i][1].toFixed(0)}" x2="${pts[j][0].toFixed(0)}" y2="${pts[j][1].toFixed(0)}" stroke="${LINE}" stroke-width="1"/>`
        );
      }
    }
  }
  const nodes = pts
    .map(
      ([x, y], i) =>
        `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${i % 3 === 0 ? 6 : 3}" fill="${INK}" fill-opacity="${i % 3 === 0 ? 0.85 : 0.45}"/>`
    )
    .join('');
  return lines.join('') + nodes;
}

function bars(rnd) {
  const p = [];
  const base = 520;
  for (let i = 0; i < 26; i++) {
    const x = 580 + i * 22;
    const h = 40 + rnd() * 240 * (1 - i / 42);
    p.push(
      `<rect x="${x}" y="${(base - h).toFixed(0)}" width="8" height="${h.toFixed(0)}" fill="${INK}" fill-opacity="${(0.1 + (h / 280) * 0.55).toFixed(3)}"/>`
    );
  }
  p.push(`<line x1="560" y1="${base}" x2="1160" y2="${base}" stroke="${LINE}" stroke-width="1"/>`);
  return p.join('');
}

function build({ seed, motif }) {
  const rnd = mulberry32(seed);
  let art = '';
  if (motif === 'rings') art = rings(rnd);
  if (motif === 'mesh') art = mesh(rnd);
  if (motif === 'bars') art = bars(rnd);

  // 少量散点，很轻
  let dots = '';
  for (let i = 0; i < 26; i++) {
    const x = rnd() * W;
    const y = rnd() * H;
    dots += `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${(rnd() * 1.2 + 0.5).toFixed(1)}" fill="${INK}" fill-opacity="${(rnd() * 0.12 + 0.04).toFixed(2)}"/>`;
  }

  // 斜向大色块，极淡
  const band = `<path d="M0 ${H} L440 ${H} L0 300 Z" fill="${INK}" fill-opacity="0.03"/>`;

  // 大号方框
  const frame = `<rect x="${W * 0.52}" y="${H * 0.1}" width="${H * 0.8}" height="${H * 0.8}" fill="none" stroke="${LINE_SOFT}" stroke-width="1"/>`;

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#fbfbf9"/>
      <stop offset="1" stop-color="#f2f2ef"/>
    </linearGradient>
    <radialGradient id="soft" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#e9e9e4" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#e9e9e4" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
      <path d="M48 0H0V48" fill="none" stroke="${INK}" stroke-opacity="0.04" stroke-width="1"/>
    </pattern>
    <filter id="blur"><feGaussianBlur stdDeviation="70"/></filter>
  </defs>

  <rect width="${W}" height="${H}" fill="url(#bg)"/>
  <rect width="${W}" height="${H}" fill="url(#grid)"/>
  <ellipse cx="${W * 0.6}" cy="${H * 0.5}" rx="380" ry="280" fill="url(#soft)" filter="url(#blur)"/>

  ${band}
  ${frame}
  <g>${art}</g>
  ${dots}

  <rect x="0.5" y="0.5" width="${W - 1}" height="${H - 1}" fill="none" stroke="#e3e3de"/>
</svg>
`;
}

for (const spec of specs) {
  writeFileSync(resolve(outDir, spec.file), build(spec), 'utf8');
  console.log('[ok]', spec.file);
}

const favicon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#ffffff"/>
  <g fill="none" stroke="#1b1b19" stroke-width="2" stroke-linecap="square">
    <path d="M7 13V7h6M19 7h6v6M25 19v6h-6M13 25H7v-6"/>
  </g>
</svg>
`;
writeFileSync(resolve(__dirname, '../public/favicon.svg'), favicon, 'utf8');
console.log('[ok] favicon.svg');
