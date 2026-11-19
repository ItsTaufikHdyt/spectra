// Uji tampil di Chromium headless (WebGL SwiftShader) tanpa mengubah kode frontend.
//   node data-pipeline/scripts/citygml/uji_tampil.cjs sebelum|sesudah
// Frontend dev server harus jalan di :3000. Mode `sebelum` menyajikan tile LAMA dari cadangan
// (data-pipeline/processed/backup_public_tiles) lewat page.route, jadi tidak ada berkas yang diubah.
// Memakai `?debug=perf` agar window.__spectra = { viewer, tileset } tersedia.
// Env: PLAYWRIGHT_DIR (default cache npx), CHROME_PATH (default Chromium cache Playwright).
const fs = require('fs');
const path = require('path');
const HOME = process.env.HOME;
const PW = process.env.PLAYWRIGHT_DIR || `${HOME}/.npm/_npx/e41f203b7505f1fb/node_modules/playwright`;
const CHROME = process.env.CHROME_PATH || `${HOME}/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`;
const { chromium } = require(PW);
const ROOT = path.resolve(__dirname, '../../..');
const BACKUP = path.join(ROOT, 'data-pipeline/processed/backup_public_tiles');
const OUT = path.join(ROOT, 'data-pipeline/reports/uji_tampil_bontang_lestari');
const mode = process.argv[2];
if (!['sebelum', 'sesudah'].includes(mode)) throw new Error('mode: sebelum|sesudah');
fs.mkdirSync(OUT, { recursive: true });

// Pandangan (lon, lat, jarak kamera m, pitch derajat). Heading 0 (utara).
const VIEWS = [
  { nama: 'A_perumahan', lon: 117.4516, lat: 0.0773, R: 320, pitch: -35 },
  { nama: 'B_pltu', lon: 117.4935, lat: 0.0548, R: 520, pitch: -35 },
  { nama: 'C_atap_miring', lon: 117.450646, lat: 0.077657, R: 90, pitch: -35 },
  { nama: 'D_atap_datar', lon: 117.451792, lat: 0.076814, R: 90, pitch: -35 },
  { nama: 'E_bangunan_tinggi', lon: 117.492562, lat: 0.05424, R: 170, pitch: -30 },
  { nama: 'F_atas_atap_datar', lon: 117.451792, lat: 0.076814, R: 60, pitch: -90 },
];
const KLIK = [
  { nama: 'atap_miring', id: 'BTG-BLD-001072', lon: 117.450646, lat: 0.077657, tinggi: 6.9, R: 90, pitch: -35 },
  { nama: 'atap_datar', id: 'BTG-BLD-001082', lon: 117.451792, lat: 0.076814, tinggi: 3.16, R: 90, pitch: -35 },
  { nama: 'tinggi_lebih_40m', id: 'BTG-BLD-000700', lon: 117.492562, lat: 0.05424, tinggi: 49.1, R: 170, pitch: -30 },
];

(async () => {
  const browser = await chromium.launch({
    executablePath: CHROME, headless: true,
    args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
  });
  const page = await browser.newPage({ viewport: { width: 1400, height: 850 } });
  const log = { mode, konsol: [], galatHalaman: [], permintaanGagal: [], tampilan: {}, klik: {}, warna: {} };
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) log.konsol.push(`${m.type()}: ${m.text()}`); });
  page.on('pageerror', (e) => log.galatHalaman.push(String(e)));
  page.on('response', (r) => { if (r.status() >= 400) log.permintaanGagal.push(`${r.status()} ${r.url()}`); });
  if (mode === 'sebelum') {
    await page.route('**/tiles/**', (route) => {
      const rel = decodeURIComponent(new URL(route.request().url()).pathname.replace(/^\/tiles\//, ''));
      const f = path.join(BACKUP, rel);
      if (!f.startsWith(BACKUP) || !fs.existsSync(f)) return route.continue();
      const type = f.endsWith('.json') ? 'application/json' : 'model/gltf-binary';
      return route.fulfill({ status: 200, contentType: type, body: fs.readFileSync(f) });
    });
  }
  await page.goto('http://localhost:3000/?debug=perf', { waitUntil: 'load' });
  await page.waitForFunction(() => !!window.__spectra, null, { timeout: 90000 });

  const pasang = (v) => page.evaluate((v) => {
    const { viewer } = window.__spectra; const C = viewer.camera.position.constructor;
    const rad = (d) => (d * Math.PI) / 180; const p = rad(v.pitch);
    const dLat = v.pitch === -90 ? 0 : -(v.R * Math.cos(-p)) / 111320;
    viewer.camera.setView({ destination: C.fromDegrees(v.lon, v.lat + dLat, v.R * Math.sin(-p)), orientation: { heading: 0, pitch: p, roll: 0 } });
    viewer.scene.requestRender();
  }, v);
  const tunggu = async () => {
    for (let i = 0; i < 120; i++) {
      const ok = await page.evaluate(() => { const { viewer, tileset } = window.__spectra; viewer.scene.requestRender(); return tileset.tilesLoaded; });
      if (ok && i > 4) break;
      await page.waitForTimeout(500);
    }
    await page.waitForTimeout(1200);
  };

  for (const v of VIEWS) {
    await pasang(v); await tunggu();
    await page.screenshot({ path: path.join(OUT, `${mode}_${v.nama}.png`) });
    const st = await page.evaluate(() => { const s = window.__spectra.tileset.statistics; return { dipilih: s.selected, dimuat: s.numberOfLoadedTilesTotal, kontenSiap: s.numberOfTilesWithContentReady }; });
    log.tampilan[v.nama] = st;
  }

  // Warna piksel atap datar dari atas (render + baca kanvas dalam satu tugas)
  await pasang(VIEWS[5]); await tunggu();
  log.warna = await page.evaluate(async (v) => {
    const { viewer } = window.__spectra; const C = viewer.camera.position.constructor;
    viewer.scene.render();
    const cv = viewer.scene.canvas; const img = new Image(); img.src = cv.toDataURL('image/png'); await img.decode();
    const c2 = document.createElement('canvas'); c2.width = cv.width; c2.height = cv.height; const g = c2.getContext('2d'); g.drawImage(img, 0, 0);
    const pt = viewer.scene.cartesianToCanvasCoordinates(C.fromDegrees(v.lon, v.lat, 3.2));
    const sx = cv.width / cv.clientWidth, sy = cv.height / cv.clientHeight;
    const d = g.getImageData(Math.round(pt.x * sx) - 2, Math.round(pt.y * sy) - 2, 5, 5).data; const m = [0, 0, 0];
    for (let i = 0; i < d.length; i += 4) { m[0] += d[i]; m[1] += d[i + 1]; m[2] += d[i + 2]; }
    return { titik: [Math.round(pt.x), Math.round(pt.y)], rgbRataRata: m.map((x) => Math.round(x / (d.length / 4))) };
  }, VIEWS[5]);

  if (mode === 'sesudah') {
    for (const k of KLIK) {
      await pasang(k); await tunggu();
      const pos = await page.evaluate((k) => {
        const { viewer } = window.__spectra; const C = viewer.camera.position.constructor;
        const p = viewer.scene.cartesianToCanvasCoordinates(C.fromDegrees(k.lon, k.lat, k.tinggi * 0.5)); const r = viewer.scene.canvas.getBoundingClientRect();
        return { x: r.left + p.x, y: r.top + p.y };
      }, k);
      await page.mouse.click(pos.x, pos.y);
      await page.waitForTimeout(1500);
      await page.evaluate(() => window.__spectra.viewer.scene.requestRender());
      await page.waitForTimeout(800);
      await page.screenshot({ path: path.join(OUT, `sesudah_klik_${k.nama}.png`) });
      log.klik[k.nama] = { diharapkan: k.id, klik: pos, teksHalaman: (await page.evaluate(() => document.body.innerText)).slice(0, 1800) };
    }
  }
  fs.writeFileSync(path.join(OUT, `log_${mode}.json`), JSON.stringify(log, null, 2));
  console.log(JSON.stringify({ mode, konsol: log.konsol.length, galat: log.galatHalaman.length, gagal: log.permintaanGagal.length, warna: log.warna, tampilan: log.tampilan }, null, 1));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
