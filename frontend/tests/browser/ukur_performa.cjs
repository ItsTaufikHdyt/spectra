// Ukur FPS dan beban GPU (prosedur uji impor resmi: Loktuan 700 m, pitch -35, tile v2; diam dan memutar 10 dtk).
//   node frontend/tests/browser/ukur_performa.cjs [--keluar berkas.json]
// Env: APP_URL (http://localhost:3000), TEMA="terang,gelap" ("-" = tanpa pengaturan tema, untuk UI sebelum redesign),
//      MODE="hemat,seimbang", VIEWPORT="1400x850", GPU_BUSY, PLAYWRIGHT_DIR, CHROME_PATH, GPU_ARGS=swiftshader.
// Beban GPU dibaca dari sysfs gpu_busy_percent (AMD); tanpa itu nilainya null.
const fs = require('fs');
const path = require('path');
const HOME = process.env.HOME;
const { chromium } = require(process.env.PLAYWRIGHT_DIR || `${HOME}/.npm/_npx/e41f203b7505f1fb/node_modules/playwright`);
const CHROME = process.env.CHROME_PATH || `${HOME}/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`;
const URL = process.env.APP_URL || 'http://localhost:3000';
const GPU_BUSY = process.env.GPU_BUSY || '/sys/class/drm/card1/device/gpu_busy_percent';
const ARGS = process.env.GPU_ARGS === 'swiftshader' ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : ['--use-gl=angle', '--use-angle=gl-egl'];
const [VW, VH] = (process.env.VIEWPORT || '1400x850').split('x').map(Number);
const TEMA = (process.env.TEMA || 'terang,gelap').split(',');
const MODE = (process.env.MODE || 'hemat,seimbang').split(',');
const T = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../../data-pipeline/reports/uji_tampil_impor_resmi/targets.json'))).target.luar_batas_loktuan;
const VIEW = { lon: T.lon, lat: T.lat, R: 700, pitch: -35 };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const gpu = () => { try { return Number(fs.readFileSync(GPU_BUSY, 'utf8')); } catch { return null; } };
const rata = (a) => (a.some((x) => x == null) ? null : +(a.reduce((s, x) => s + x, 0) / a.length).toFixed(1));

async function pasang(page, v) {
  await page.evaluate((v) => {
    const { viewer } = window.__spectra; const C = viewer.camera.position.constructor; const p = (v.pitch * Math.PI) / 180;
    const rh = v.R * Math.cos(-p);
    viewer.camera.setView({ destination: C.fromDegrees(v.lon, v.lat - rh / 111320, v.R * Math.sin(-p)), orientation: { heading: 0, pitch: p, roll: 0 } });
    viewer.scene.requestRender();
  }, v);
  for (let i = 0; i < 160; i++) {
    const ok = await page.evaluate(() => { const { viewer, tileset } = window.__spectra; viewer.scene.requestRender(); return tileset.tilesLoaded; });
    if (ok && i > 4) break; await sleep(500);
  }
  await sleep(1500);
}

async function ukur(page, aksi) {
  const f0 = await page.evaluate(() => window.__spectraPerf().frames); const s = []; const t0 = Date.now();
  if (aksi === 'putar') {
    page.evaluate(({ v, ms }) => new Promise((res) => {
      const { viewer } = window.__spectra; const C = viewer.camera.position.constructor; const t0 = performance.now();
      const p = (v.pitch * Math.PI) / 180; const rh = v.R * Math.cos(-p);
      const f = (t) => { const e = t - t0; if (e > ms) return res(); const h = (e / ms) * 2 * Math.PI;
        viewer.camera.setView({ destination: C.fromDegrees(v.lon - (rh * Math.sin(h)) / (111320 * Math.cos((v.lat * Math.PI) / 180)), v.lat - (rh * Math.cos(h)) / 111320, v.R * Math.sin(-p)), orientation: { heading: h, pitch: p, roll: 0 } }); requestAnimationFrame(f); };
      requestAnimationFrame(f);
    }), { v: VIEW, ms: 10000 });
  }
  while (Date.now() - t0 < 10000) { s.push(gpu()); await sleep(500); }
  const f1 = await page.evaluate(() => window.__spectraPerf().frames);
  return { fps: +((f1 - f0) / ((Date.now() - t0) / 1000)).toFixed(1), gpu_rata: rata(s), gpu_maks: s.some((x) => x == null) ? null : Math.max(...s) };
}

(async () => {
  const keluar = process.argv.includes('--keluar') ? process.argv[process.argv.indexOf('--keluar') + 1] : null;
  const hasil = { url: URL, viewport: `${VW}x${VH}`, renderer: null, gpu_idle: null, pengukuran: [] };
  const idle = []; for (let i = 0; i < 10; i++) { idle.push(gpu()); await sleep(500); } hasil.gpu_idle = rata(idle);
  for (const tema of TEMA) for (const mode of MODE) {
    const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox', '--ignore-gpu-blocklist', ...ARGS] });
    const ctx = await browser.newContext({ viewport: { width: VW, height: VH } });
    if (tema !== '-') await ctx.addInitScript((t) => { try { localStorage.setItem('spectra.theme', t); } catch {} }, tema);
    const page = await ctx.newPage(); const galat = []; page.on('pageerror', (e) => galat.push(String(e)));
    await page.goto(`${URL}/?debug=perf&mode=${mode}`, { waitUntil: 'load' });
    await page.waitForFunction(() => !!window.__spectra, null, { timeout: 90000 });
    hasil.renderer = await page.evaluate(() => window.__spectraPerf().renderer);
    await pasang(page, VIEW); await sleep(3000);
    const canvas = await page.evaluate(() => { const c = window.__spectra.viewer.scene.canvas; return `${c.clientWidth}x${c.clientHeight}`; });
    const diam = await ukur(page, 'diam'); const putar = await ukur(page, 'putar');
    const r = { tema, mode, canvas, diam, putar, galat: galat.length };
    hasil.pengukuran.push(r); console.log(JSON.stringify(r));
    await browser.close();
  }
  if (keluar) fs.writeFileSync(keluar, JSON.stringify(hasil, null, 2));
})().catch((e) => { console.error(e); process.exit(1); });
