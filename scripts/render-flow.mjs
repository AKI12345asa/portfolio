/**
 * 把 09-工作流程图.md 里的 ```mermaid 代码块渲染成 SVG
 * 用法：node scripts/render-flow.mjs
 * 依赖：.tools/node_modules/mermaid/dist/mermaid.min.js（npm i mermaid）
 */
import { spawn } from 'node:child_process';
import { copyFileSync, mkdirSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as sleep } from 'node:timers/promises';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const MD = process.argv[2] ? resolve(process.argv[2]) : join(ROOT, '框架文档', '09-工作流程图.md');
const OUT = process.argv[3] ? resolve(process.argv[3]) : join(ROOT, '框架文档', '流程图');
const MERMAID = join(ROOT, '.tools', 'node_modules', 'mermaid', 'dist', 'mermaid.min.js');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PORT = 9444;

const names = [
  '01-动画系统',
  '02-战斗与技能系统',
  '03-GOAP系统',
  '04-节点树系统',
  '05-资源与对象池',
  '06-UI系统',
  '07-时间系统',
  '08-存档系统',
  '09-系统关系总览',
];

// ---------- 1. 抽取 mermaid 代码块 ----------
const md = readFileSync(MD, 'utf8');
const blocks = [...md.matchAll(/```mermaid\r?\n([\s\S]*?)```/g)].map((m) => m[1].trim());
console.log(`找到 ${blocks.length} 个 mermaid 代码块`);
if (blocks.length !== names.length) {
  console.warn(`⚠ 代码块数量(${blocks.length})与命名表(${names.length})不一致，按位对应`);
}

// ---------- 2. 准备临时页面 ----------
const work = join(tmpdir(), `flow-render-${Date.now()}`);
mkdirSync(work, { recursive: true });
copyFileSync(MERMAID, join(work, 'mermaid.min.js'));
writeFileSync(
  join(work, 'index.html'),
  `<!doctype html><html><head><meta charset="utf-8">
   <style>body{background:#fff;margin:0;font-family:"Microsoft YaHei","PingFang SC",sans-serif}</style>
   </head><body><div id="host"></div><script src="mermaid.min.js"></script></body></html>`,
  'utf8'
);
mkdirSync(OUT, { recursive: true });

// ---------- 3. 起浏览器 ----------
const proc = spawn(
  EDGE,
  [
    '--headless=new',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    '--allow-file-access-from-files',
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${join(work, 'profile')}`,
    'about:blank',
  ],
  { stdio: 'ignore' }
);

async function waitForDevtools() {
  for (let i = 0; i < 120; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      if (r.ok) return await r.json();
    } catch {
      /* retry */
    }
    await sleep(150);
  }
  throw new Error('DevTools 未就绪');
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
  } else if (msg.method) listeners.forEach((fn) => fn(msg));
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
const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
await send('Page.enable', {}, sessionId);
await send('Runtime.enable', {}, sessionId);

const loaded = once('Page.loadEventFired', sessionId);
await send('Page.navigate', { url: `file:///${join(work, 'index.html').replace(/\\/g, '/')}` }, sessionId);
await loaded;
await sleep(500);

// ---------- 4. 初始化 mermaid ----------
await send(
  'Runtime.evaluate',
  {
    expression: `document.body.style.width = '1800px';
    document.body.style.margin = '0';
    mermaid.initialize({
      startOnLoad: false,
      theme: 'neutral',
      fontFamily: '"Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif',
      flowchart: { htmlLabels: false, useMaxWidth: false, wrappingWidth: 420, curve: 'basis', padding: 14, nodeSpacing: 45, rankSpacing: 55 },
      themeVariables: {
        primaryColor: '#f7f7f5',
        primaryTextColor: '#1b1b19',
        primaryBorderColor: '#c9c9c1',
        lineColor: '#8a8a84',
        secondaryColor: '#eef1f0',
        tertiaryColor: '#fafaf9',
        fontSize: '14px'
      }
    });`,
  },
  sessionId
);

// ---------- 5. 逐张渲染 ----------
let ok = 0;
for (let i = 0; i < blocks.length; i++) {
  const name = names[i] ?? `图${i + 1}`;
  const expr = `(async () => {
    const { svg } = await mermaid.render('d${i}', ${JSON.stringify(blocks[i])});
    return svg;
  })()`;
  const res = await send(
    'Runtime.evaluate',
    { expression: expr, awaitPromise: true, returnByValue: true },
    sessionId
  );
  if (res.exceptionDetails) {
    console.error(`✗ ${name}:`, res.exceptionDetails.text, res.exceptionDetails.exception?.description ?? '');
    continue;
  }
  const svg = res.result?.value;
  if (!svg || !svg.startsWith('<svg')) {
    console.error(`✗ ${name}: 返回内容不是 svg`);
    continue;
  }
  // 兜底：个别标签里可能残留未闭合的 <br>，会让 SVG 作为 XML 解析失败
  const clean = svg.replace(/<br\s*>/gi, '<br/>');
  writeFileSync(join(OUT, `${name}.svg`), clean, 'utf8');
  ok++;
  console.log(`✓ ${name}.svg`);
}

console.log(`\n完成 ${ok}/${blocks.length}`);
ws.close();
proc.kill();
await sleep(300);
try {
  rmSync(work, { recursive: true, force: true });
} catch {
  /* ignore */
}
process.exit(ok === blocks.length ? 0 : 1);
