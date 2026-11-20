// Uji tampil tile hasil pipeline CityGML (15 kelurahan) di Chromium headless dengan GPU sungguhan, tanpa mengubah kode frontend.
//   node data-pipeline/scripts/citygml/uji_impor_resmi.cjs klik   # klik bangunan per kategori (nilai kosong, duplikat, luar batas, ...)
//   node data-pipeline/scripts/citygml/uji_impor_resmi.cjs fps     # FPS dan beban GPU, mode Hemat/Seimbang (kamera diam dan memutar)
// Frontend :3000 harus jalan dan frontend/public/tiles berisi master hasil `04_build_master.py --sync`. Beban GPU = sysfs gpu_busy_percent (AMD).
// Env: PLAYWRIGHT_DIR, CHROME_PATH, GPU_BUSY (default /sys/class/drm/card1/device/gpu_busy_percent), GPU_ARGS=swiftshader untuk software.
const fs = require('fs');
const path = require('path');
const HOME = process.env.HOME;
const PW = process.env.PLAYWRIGHT_DIR || `${HOME}/.npm/_npx/e41f203b7505f1fb/node_modules/playwright`;
const CHROME = process.env.CHROME_PATH || `${HOME}/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`;
const GPU_BUSY = process.env.GPU_BUSY || '/sys/class/drm/card1/device/gpu_busy_percent';
const { chromium } = require(PW);
const ROOT = path.resolve(__dirname, '../../..');
const OUT = path.join(ROOT, 'data-pipeline/reports/uji_tampil_impor_resmi');
const mode = process.argv[2];
const ARGS = process.env.GPU_ARGS === 'swiftshader' ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : ['--use-gl=angle', '--use-angle=gl-egl'];
const T = JSON.parse(fs.readFileSync(path.join(OUT, 'targets.json'))).target;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const gpu = () => { try { return Number(fs.readFileSync(GPU_BUSY, 'utf8')); } catch { return null; } };

async function buka(url) {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox', '--ignore-gpu-blocklist', ...ARGS] });
  const page = await browser.newPage({ viewport: { width: 1400, height: 850 } });
  const log = { konsol: [], galat: [], gagal: [] };
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) log.konsol.push(`${m.type()}: ${m.text()}`); });
  page.on('pageerror', (e) => log.galat.push(String(e)));
  page.on('response', (r) => { if (r.status() >= 400) log.gagal.push(`${r.status()} ${r.url()}`); });
  await page.goto(url, { waitUntil: 'load' });
  await page.waitForFunction(() => !!window.__spectra, null, { timeout: 90000 });
  return { browser, page, log };
}
const pasang = (page, v) => page.evaluate((v) => {
  const { viewer } = window.__spectra; const C = viewer.camera.position.constructor; const p = (v.pitch * Math.PI) / 180;
  const h = ((v.heading || 0) * Math.PI) / 180; const rh = v.R * Math.cos(-p); const lat = v.lat - (rh * Math.cos(h)) / 111320;
  const lon = v.lon - (rh * Math.sin(h)) / (111320 * Math.cos((v.lat * Math.PI) / 180));
  viewer.camera.setView({ destination: C.fromDegrees(lon, lat, v.R * Math.sin(-p)), orientation: { heading: h, pitch: p, roll: 0 } }); viewer.scene.requestRender();
}, v);
const tunggu = async (page) => {
  for (let i = 0; i < 160; i++) { const ok = await page.evaluate(() => { const { viewer, tileset } = window.__spectra; viewer.scene.requestRender(); return tileset.tilesLoaded; }); if (ok && i > 4) break; await sleep(500); }
  await sleep(1500);
};

async function klik() {
  const { browser, page, log } = await buka('http://localhost:3000/?debug=perf&mode=seimbang');
  log.renderer = await page.evaluate(() => window.__spectraPerf().renderer);
  log.klik = {};
  for (const [key, k] of Object.entries(T)) {
    let hasil = null;
    for (const R of [90, 55]) {
      await pasang(page, { lon: k.lon, lat: k.lat, R, pitch: -35 }); await tunggu(page);
      const pos = await page.evaluate((k) => { const { viewer } = window.__spectra; const C = viewer.camera.position.constructor;
        const p = viewer.scene.cartesianToCanvasCoordinates(C.fromDegrees(k.lon, k.lat, k.tinggi * 0.5)); const r = viewer.scene.canvas.getBoundingClientRect(); return { x: r.left + p.x, y: r.top + p.y }; }, k);
      await page.mouse.click(pos.x, pos.y); await sleep(1200);
      await page.evaluate(() => window.__spectra.viewer.scene.requestRender()); await sleep(800);
      const teks = await page.evaluate(() => document.body.innerText);
      const a = teks.indexOf('Bangunan LOD2'); const b = teks.indexOf('Elevasi adalah');
      const panel = a >= 0 ? teks.slice(a, b > a ? b : a + 900) : '(panel tidak menampilkan objek)';
      const idPanel = (panel.match(/BTG-BLD-\d{6}/) || [null])[0];
      hasil = { R, idDiharapkan: k.id, idDiPanel: idPanel, cocok: idPanel === k.id, panel, mencurigakan: (panel.match(/undefined|null|NaN|2147483647|3\.40282|Infinity/g) || []) };
      await page.screenshot({ path: path.join(OUT, `klik_${key}.png`) });
      if (hasil.cocok) break;
    }
    log.klik[key] = { target: k, ...hasil };
    console.log(key, k.id, '->', hasil.idDiPanel, hasil.cocok ? 'cocok' : 'TIDAK cocok', hasil.mencurigakan.length ? hasil.mencurigakan : '');
  }
  fs.writeFileSync(path.join(OUT, 'log_klik.json'), JSON.stringify(log, null, 2));
  console.log('konsol', log.konsol.length, 'galat', log.galat.length, 'gagal', log.gagal.length);
  await browser.close();
}

async function fps() {
  const hasil = { renderer: null, gpu_idle_sistem: null, pengukuran: [] };
  const base = []; for (let i = 0; i < 12; i++) { base.push(gpu()); await sleep(500); }
  hasil.gpu_idle_sistem = { mean: +(base.reduce((s, x) => s + x, 0) / base.length).toFixed(1), min: Math.min(...base), maks: Math.max(...base) };
  const view = { lon: T.luar_batas_loktuan.lon, lat: T.luar_batas_loktuan.lat, R: 700, pitch: -35 };
  for (const md of ['hemat', 'seimbang']) {
    const { browser, page, log } = await buka(`http://localhost:3000/?debug=perf&mode=${md}`);
    hasil.renderer = await page.evaluate(() => window.__spectraPerf().renderer);
    await pasang(page, view); await tunggu(page);
    const ukur = async (aksi) => {
      const f0 = await page.evaluate(() => window.__spectraPerf().frames); const s = []; const t0 = Date.now();
      if (aksi === 'putar') page.evaluate(({ v, ms }) => new Promise((res) => { const { viewer } = window.__spectra; const C = viewer.camera.position.constructor; const t0 = performance.now();
        const p = (v.pitch * Math.PI) / 180; const rh = v.R * Math.cos(-p);
        const f = (t) => { const e = t - t0; if (e > ms) return res(); const h = (e / ms) * 2 * Math.PI;
          viewer.camera.setView({ destination: C.fromDegrees(v.lon - (rh * Math.sin(h)) / (111320 * Math.cos((v.lat * Math.PI) / 180)), v.lat - (rh * Math.cos(h)) / 111320, v.R * Math.sin(-p)), orientation: { heading: h, pitch: p, roll: 0 } }); requestAnimationFrame(f); };
        requestAnimationFrame(f); }), { v: view, ms: 10000 });
      while (Date.now() - t0 < 10000) { s.push(gpu()); await sleep(500); }
      const f1 = await page.evaluate(() => window.__spectraPerf().frames);
      return { fps: +((f1 - f0) / ((Date.now() - t0) / 1000)).toFixed(1), gpu_mean: +(s.reduce((a, x) => a + x, 0) / s.length).toFixed(1), gpu_min: Math.min(...s), gpu_maks: Math.max(...s) };
    };
    await sleep(3000);
    const diam = await ukur('diam'); const putar = await ukur('putar');
    const st = await page.evaluate(() => window.__spectraPerf().tileset);
    hasil.pengukuran.push({ mode: md, diam, putar, tileset: st, konsol: log.konsol.length });
    console.log(md, 'diam', JSON.stringify(diam), 'putar', JSON.stringify(putar));
    await browser.close();
  }
  fs.writeFileSync(path.join(OUT, 'log_fps.json'), JSON.stringify(hasil, null, 2));
}

(mode === 'klik' ? klik() : mode === 'fps' ? fps() : Promise.reject(new Error('mode: klik|fps'))).catch((e) => { console.error(e); process.exit(1); });
