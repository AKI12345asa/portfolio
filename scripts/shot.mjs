/**
 * 用 CDP 截真实设备尺寸的整页图（Windows 下 --window-size 小于 500 会被强制放大，
 * 所以移动端必须走设备模拟，不能用命令行 --screenshot）
 *
 * 用法：node scripts/shot.mjs
 * 输出到 .shots/
 */
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as sleep } from 'node:timers/promises';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(__dirname, '../.shots');
mkdirSync(OUT, { recursive: true });

const EDGE =
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PORT = 9333;
const BASE = process.env.SHOT_BASE ?? 'http://localhost:4321';

const shots = [
  { name: 'desktop-home', url: '/', w: 1440, h: 900, mobile: false },
  { name: 'desktop-about', url: '/about/', w: 1440, h: 900, mobile: false },
  { name: 'desktop-framework', url: '/framework/', w: 1440, h: 900, mobile: false },
  { name: 'desktop-fw-module', url: '/framework/battle/', w: 1440, h: 900, mobile: false },
  { name: 'mobile-home', url: '/', w: 390, h: 844, mobile: true },
  { name: 'mobile-framework', url: '/framework/', w: 390, h: 844, mobile: true },
];

const profile = join(tmpdir(), `dsh-edge-shot-${Date.now()}`);
const proc = spawn(
  EDGE,
  [
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${profile}`,
    'about:blank',
  ],
  { stdio: 'ignore', detached: false }
);

async function waitForDevtools() {
  for (let i = 0; i < 100; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      if (r.ok) return await r.json();
    } catch {
      /* not ready yet */
    }
    await sleep(150);
  }
  throw new Error('DevTools 没有起来');
}

const version = await waitForDevtools();
const ws = new WebSocket(version.webSocketDebuggerUrl);
await new Promise((res, rej) => {
  ws.onopen = res;
  ws.onerror = rej;
});

let msgId = 0;
const pending = new Map();
const listeners = [];

ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) {
    const { resolve: r, reject: j } = pending.get(msg.id);
    pending.delete(msg.id);
    msg.error ? j(new Error(JSON.stringify(msg.error))) : r(msg.result);
  } else if (msg.method) {
    listeners.forEach((fn) => fn(msg));
  }
};

function send(method, params = {}, sessionId) {
  const id = ++msgId;
  const payload = { id, method, params };
  if (sessionId) payload.sessionId = sessionId;
  ws.send(JSON.stringify(payload));
  return new Promise((r, j) => pending.set(id, { resolve: r, reject: j }));
}

function once(method, sessionId) {
  return new Promise((r) => {
    const fn = (msg) => {
      if (msg.method === method && msg.sessionId === sessionId) {
        listeners.splice(listeners.indexOf(fn), 1);
        r(msg.params);
      }
    };
    listeners.push(fn);
  });
}

const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
const { sessionId } = await send('Target.attachToTarget', {
  targetId,
  flatten: true,
});

await send('Page.enable', {}, sessionId);
await send('Runtime.enable', {}, sessionId);

for (const shot of shots) {
  await send(
    'Emulation.setDeviceMetricsOverride',
    {
      width: shot.w,
      height: shot.h,
      deviceScaleFactor: 1,
      mobile: shot.mobile,
    },
    sessionId
  );

  const loaded = once('Page.loadEventFired', sessionId);
  await send('Page.navigate', { url: BASE + shot.url }, sessionId);
  await loaded;
  // 等字体、入场动画、图片
  await sleep(1400);

  // 整页截图时视口外的元素不会触发 IntersectionObserver，
  // 手动把它们标记成「已入场」，截出来才是访客最终看到的样子
  await send(
    'Runtime.evaluate',
    {
      expression: `document.querySelectorAll('[data-reveal]').forEach(el => el.classList.add('is-in'));
        document.querySelectorAll('img[loading="lazy"]').forEach(img => { img.loading = 'eager'; });`,
    },
    sessionId
  );
  await sleep(900);

  const metrics = await send('Page.getLayoutMetrics', {}, sessionId);
  const size = metrics.cssContentSize ?? metrics.contentSize;
  const width = Math.ceil(size.width);
  const height = Math.min(Math.ceil(size.height), 12000);

  const { data } = await send(
    'Page.captureScreenshot',
    {
      format: 'png',
      captureBeyondViewport: true,
      clip: { x: 0, y: 0, width, height, scale: 1 },
    },
    sessionId
  );

  const file = join(OUT, `${shot.name}.png`);
  writeFileSync(file, Buffer.from(data, 'base64'));
  console.log(`[ok] ${shot.name}  ${width}x${height}`);
}

// ---------- 交互自检 ----------
async function open(url, w = 1440, h = 900, mobile = false) {
  await send(
    'Emulation.setDeviceMetricsOverride',
    { width: w, height: h, deviceScaleFactor: 1, mobile },
    sessionId
  );
  const loaded = once('Page.loadEventFired', sessionId);
  await send('Page.navigate', { url: BASE + url }, sessionId);
  await loaded;
  await sleep(1200);
}

async function evaluate(expression) {
  const r = await send(
    'Runtime.evaluate',
    { expression, returnByValue: true, awaitPromise: true },
    sessionId
  );
  if (r.exceptionDetails) return 'ERROR ' + JSON.stringify(r.exceptionDetails.text);
  return r.result?.value;
}

console.log('\n--- 交互自检 ---');

console.log(
  await evaluate(`(async () => {
    const btn = document.querySelector('[data-embed]');
    if (!btn) return 'FAIL 找不到视频封面按钮';
    btn.click();
    const frame = document.querySelector('.video__frame');
    if (!frame) return 'FAIL 点击后没有插入 iframe';
    return 'OK 视频门面 → ' + frame.tagName + ' src=' + (frame.getAttribute('src') || '').slice(0, 42);
  })()`)
);

await open('/', 390, 844, true);
console.log(
  await evaluate(`(async () => {
    const t = document.querySelector('[data-nav-toggle]');
    const n = document.querySelector('[data-nav]');
    if (!t || !n) return 'FAIL 找不到导航';
    t.click();
    await new Promise(r => setTimeout(r, 300));
    const opened = n.classList.contains('is-open') && t.getAttribute('aria-expanded') === 'true';
    t.click();
    await new Promise(r => setTimeout(r, 300));
    const closed = !n.classList.contains('is-open');
    return (opened && closed ? 'OK' : 'FAIL') + ' 移动端菜单 开=' + opened + ' 关=' + closed;
  })()`)
);

for (const [name, url, mobile] of [
  ['首页', '/', true],
  ['关于', '/about/', true],
  ['框架总览', '/framework/', true],
  ['框架模块', '/framework/battle/', true],
]) {
  await open(url, 390, 844, mobile);
  console.log(
    (await evaluate(`(() => {
      const d = document.documentElement;
      const over = d.scrollWidth - d.clientWidth;
      return (over > 1 ? 'FAIL 横向溢出 ' + over + 'px' : 'OK 无横向溢出') + ' · ' + ${JSON.stringify(name)};
    })()`)) ?? ''
  );
}

ws.close();
proc.kill();
await sleep(300);
try {
  rmSync(profile, { recursive: true, force: true });
} catch {
  /* ignore */
}
process.exit(0);
