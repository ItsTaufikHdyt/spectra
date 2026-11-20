// Ukur kontras bangunan terhadap basemap (selisih piksel dengan/tanpa tileset) pada beberapa kandidat penyesuaian.
//   TEMA=gelap SHOT_DIR=/tmp/x node frontend/tests/browser/ukur_kontras.cjs
// Kandidat = potongan JS yang dijalankan di halaman (v = viewer, T = tileset, Cesium = modul cesium dari Vite dev); env KANDIDAT berisi JSON [{nama, js}].
// Env: APP_URL, TEMA (terang|gelap), SHOT_DIR, PLAYWRIGHT_DIR, CHROME_PATH, GPU_ARGS=swiftshader.
const fs = require('fs');
const path = require('path');
const HOME = process.env.HOME;
const { chromium } = require(process.env.PLAYWRIGHT_DIR || `${HOME}/.npm/_npx/e41f203b7505f1fb/node_modules/playwright`);
const CHROME = process.env.CHROME_PATH || `${HOME}/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`;
const URL = process.env.APP_URL || 'http://localhost:3000';
const TEMA = process.env.TEMA || 'gelap';
const SHOT = process.env.SHOT_DIR;
const ARGS = process.env.GPU_ARGS === 'swiftshader' ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : ['--use-gl=angle', '--use-angle=gl-egl'];
const T = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../../data-pipeline/reports/uji_tampil_impor_resmi/targets.json'))).target;
const VIEWS = { padat_loktuan: { ...T.luar_batas_loktuan, R: 700 }, lestari: { ...T.luar_batas_bontang_lestari, R: 700 } };
const KANDIDAT = JSON.parse(process.env.KANDIDAT || JSON.stringify([
  { nama: 'dasar', js: '' },
  { nama: 'dasar_ulang', js: '' },
  { nama: 'ibl_2', js: 'T.imageBasedLighting.imageBasedLightingFactor = new Cesium.Cartesian2(2, 2);' },
  { nama: 'ibl_3', js: 'T.imageBasedLighting.imageBasedLightingFactor = new Cesium.Cartesian2(3, 3);' }
]));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox', '--ignore-gpu-blocklist', ...ARGS] });
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 850 } });
  await ctx.addInitScript((t) => { try { localStorage.setItem('spectra.theme', t); } catch {} }, TEMA);
  const page = await ctx.newPage();
  await page.goto(`${URL}/?debug=perf&mode=kualitas`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__spectra?.tileset, null, { timeout: 90000 }); await sleep(3000);
  await page.evaluate(() => { for (const d of document.querySelectorAll('body > div')) if (d.style.position === 'fixed') d.remove(); });
  const snap = async () => (await page.screenshot({ clip: await page.locator('#cesiumContainer').boundingBox() })).toString('base64');
  const stabil = async () => {
    for (let i = 0; i < 80; i++) { if ((await page.evaluate(() => { window.__spectra.viewer.scene.requestRender(); return window.__spectra.tileset.tilesLoaded; })) && i > 3) break; await sleep(400); }
    await sleep(1200);
  };
  for (const [vn, view] of Object.entries(VIEWS)) {
    await page.evaluate((v) => {
      const { viewer } = window.__spectra; const C = viewer.camera.position.constructor; const p = (-35 * Math.PI) / 180; const rh = v.R * Math.cos(-p);
      viewer.camera.setView({ destination: C.fromDegrees(v.lon, v.lat - rh / 111320, v.R * Math.sin(-p)), orientation: { heading: 0, pitch: p, roll: 0 } }); viewer.scene.requestRender();
    }, view);
    await stabil();
    for (const k of KANDIDAT) {
      await page.evaluate(async (js) => { const v = window.__spectra.viewer, T = window.__spectra.tileset, C3 = v.camera.position.constructor; const Cesium = await import(performance.getEntriesByType('resource').map((e) => e.name).find((n) => /deps\/cesium\.js/.test(n))); T.lightColor = undefined; v.scene.light.intensity = 2; T.imageBasedLighting.imageBasedLightingFactor = new Cesium.Cartesian2(1, 1); try { await eval(`(async () => { ${js} })()`); } catch (e) { return String(e.message || e); } v.scene.requestRender(); return null; }, k.js).then((m) => { if (m) throw new Error(`kandidat ${k.nama}: ${m}`); });
      await stabil(); const dengan = await snap();
      await page.evaluate(() => { window.__spectra.tileset.show = false; window.__spectra.viewer.scene.requestRender(); }); await sleep(900);
      const tanpa = await snap();
      await page.evaluate(() => { window.__spectra.tileset.show = true; window.__spectra.viewer.scene.requestRender(); });
      const r = await page.evaluate(async ([a, b]) => {
        const px = async (s) => { const bm = await createImageBitmap(await (await fetch(`data:image/png;base64,${s}`)).blob()); const c = new OffscreenCanvas(bm.width, bm.height); const g = c.getContext('2d'); g.drawImage(bm, 0, 0); return g.getImageData(0, 0, bm.width, bm.height).data; };
        const [A, B] = [await px(a), await px(b)]; const lin = (u) => { u /= 255; return u <= 0.03928 ? u / 12.92 : ((u + 0.055) / 1.055) ** 2.4; };
        const L = (d, i) => 0.2126 * lin(d[i]) + 0.7152 * lin(d[i + 1]) + 0.0722 * lin(d[i + 2]);
        const kon = []; const lum = [];
        for (let i = 0; i < A.length; i += 4) {
          if (Math.abs(A[i] - B[i]) + Math.abs(A[i + 1] - B[i + 1]) + Math.abs(A[i + 2] - B[i + 2]) < 18) continue;
          const [x, y] = [L(A, i), L(B, i)]; kon.push((Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05)); lum.push(x);
        }
        kon.sort((p, q) => p - q); lum.sort((p, q) => p - q); const q = (arr, f) => arr[Math.floor(arr.length * f)] ?? null;
        return { piksel: kon.length, median: q(kon, 0.5), p10: q(kon, 0.1), p25: q(kon, 0.25), lum: q(lum, 0.5) };
      }, [dengan, tanpa]);
      const f = (n) => (n == null ? null : +n.toFixed(2));
      console.log(vn.padEnd(14), k.nama.padEnd(12), JSON.stringify({ piksel: r.piksel, median: f(r.median), p10: f(r.p10), p25: f(r.p25), lum_median: f(r.lum) }));
      if (SHOT) fs.writeFileSync(path.join(SHOT, `kontras_${TEMA}_${vn}_${k.nama}.png`), Buffer.from(dengan, 'base64'));
    }
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
