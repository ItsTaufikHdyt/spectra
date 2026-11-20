// Uji tata letak dan fitur UI v2 di Chromium headless (GPU nyata). Lihat README.md di folder ini.
//   node frontend/tests/browser/uji_tata_letak.cjs      # kode keluar 1 bila ada uji gagal
// Env: PLAYWRIGHT_DIR, CHROME_PATH, APP_URL (http://localhost:3000), GPU_ARGS=swiftshader, SHOT_DIR (tangkapan layar opsional)
// Backend selalu dipalsukan mati (/api/** -> HTTP 500 teks biasa, seperti proxy Vite tanpa backend) agar hasilnya deterministik.
const path = require('path');
const HOME = process.env.HOME;
const { chromium } = require(process.env.PLAYWRIGHT_DIR || `${HOME}/.npm/_npx/e41f203b7505f1fb/node_modules/playwright`);
const CHROME = process.env.CHROME_PATH || `${HOME}/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`;
const URL = process.env.APP_URL || 'http://localhost:3000';
const ARGS = process.env.GPU_ARGS === 'swiftshader' ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : ['--use-gl=angle', '--use-angle=gl-egl'];
const SHOT = process.env.SHOT_DIR;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const hasil = [];
const cek = (nama, ok, info = '') => { hasil.push(!!ok); console.log(`${ok ? 'LULUS' : 'GAGAL'}  ${nama}${info ? '  ' + info : ''}`); };
const DERAJAT = 180 / Math.PI;

let browser;
async function buka(w, h, tema) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h } });
  await ctx.addInitScript((t) => { try { localStorage.setItem('spectra.theme', t); } catch {} }, tema);
  await ctx.route('**/api/**', (r) => r.fulfill({ status: 500, contentType: 'text/plain', body: 'Internal Server Error' }));
  const page = await ctx.newPage(); page.err = [];
  page.on('pageerror', (e) => page.err.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error' && !/status of 500|uniform3fv/.test(m.text())) page.err.push(m.text()); });
  await page.goto(`${URL}/?debug=perf`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__spectra?.tileset, null, { timeout: 90000 });
  for (let i = 0; i < 60; i++) { if (await page.evaluate(() => window.__spectra.tileset.tilesLoaded)) break; await sleep(500); }
  await sleep(3000);
  // panel debug FPS menutupi kontrol peta
  await page.evaluate(() => { for (const d of document.querySelectorAll('body > div')) if (d.style.position === 'fixed') d.remove(); });
  return page;
}
const kamera = (p) => p.evaluate(() => { const c = window.__spectra.viewer.camera; return { pitch: c.pitch, heading: c.heading, lon: c.positionCartographic.longitude, h: c.positionCartographic.height }; });
const tampil = (p, sel) => p.locator(sel).isVisible();

// Tangkapan layar kanvas (base64) dan jumlah piksel yang berbeda di antara dua tangkapan pada kamera yang sama.
const snap = async (page) => (await page.screenshot({ clip: await page.locator('#cesiumContainer').boundingBox() })).toString('base64');
const beda = (page, a, b) => page.evaluate(async ([a, b]) => {
  const px = async (s) => { const bm = await createImageBitmap(await (await fetch(`data:image/png;base64,${s}`)).blob()); const c = new OffscreenCanvas(bm.width, bm.height); const g = c.getContext('2d'); g.drawImage(bm, 0, 0); return g.getImageData(0, 0, bm.width, bm.height).data; };
  const [A, B] = [await px(a), await px(b)]; let n = 0;
  for (let i = 0; i < A.length; i += 4) if (Math.abs(A[i] - B[i]) + Math.abs(A[i + 1] - B[i + 1]) + Math.abs(A[i + 2] - B[i + 2]) > 24) n++;
  return n;
}, [a, b]);

// Klik titik-titik di kanvas (dari tengah ke luar) sampai sebuah bangunan terpilih.
async function pilihBangunan(page) {
  const b = await page.locator('#cesiumContainer').boundingBox(); const [cx, cy] = [b.x + b.width / 2, b.y + b.height / 2];
  const titik = [];
  for (let x = b.x + 60; x < b.x + b.width - 90; x += 45) for (let y = b.y + 110; y < b.y + b.height - 60; y += 45) titik.push([x, y]);
  titik.sort((p, q) => Math.hypot(p[0] - cx, p[1] - cy) - Math.hypot(q[0] - cx, q[1] - cy));
  for (const [x, y] of titik.slice(0, 60)) {
    await page.mouse.click(x, y); await sleep(900);
    if (await page.locator('#judul-objek').count()) return true;
  }
  return false;
}

(async () => {
  browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox', '--ignore-gpu-blocklist', ...ARGS] });

  // ---- 1440: fitur peta, kedua tema ----
  for (const tema of ['terang', 'gelap']) {
    const p = await buka(1440, 800, tema);
    await p.mouse.move(5, 5); await sleep(300);
    const lain = tema === 'terang' ? 'gelap' : 'terang';
    // panel kanan dibuka dulu: ukuran peta berubah saat panel terbuka, dan itu akan merusak pembandingan piksel
    await p.getByRole('button', { name: /Tampilkan informasi objek/ }).click(); await p.mouse.move(5, 5); await sleep(2500);
    // dekat ke kawasan padat Loktuan agar bangunan terpilih cukup besar untuk terukur
    await p.evaluate(() => { const { viewer } = window.__spectra; const C = viewer.camera.position.constructor; const pt = (-40 * Math.PI) / 180;
      viewer.camera.setView({ destination: C.fromDegrees(117.4808, 0.1627 - (130 * Math.cos(-pt)) / 111320, 130 * Math.sin(-pt)), orientation: { heading: 0, pitch: pt, roll: 0 } }); viewer.scene.requestRender(); });
    for (let i = 0; i < 40; i++) { if (await p.evaluate(() => { window.__spectra.viewer.scene.requestRender(); return window.__spectra.tileset.tilesLoaded; })) break; await sleep(500); }
    await sleep(1500);
    const dasar = await snap(p);
    const terpilih = await pilihBangunan(p);
    cek(`[${tema}] klik bangunan menampilkan atribut di panel kanan`, terpilih && (await tampil(p, '#panel-kanan')) && (await p.getByRole('heading', { name: /BTG-BLD-\d{6}/ }).count()) > 0);
    const idAwal = await p.locator('#judul-objek').innerText();
    const ganti = async (t) => { await p.mouse.move(5, 5); await p.getByRole('button', { name: `Tema ${t}` }).click(); await p.mouse.move(5, 5); await sleep(3500); };
    await p.mouse.move(5, 5); await sleep(600);
    const selA = await snap(p);
    const bedaA = await beda(p, dasar, selA);
    cek(`[${tema}] sorotan tampak setelah dipilih`, bedaA > 150, `piksel berbeda dari dasar: ${bedaA}`);
    await ganti(lain);
    const selB = await snap(p);
    cek(`[${tema}] objek sama dan panel tetap setelah ganti ke ${lain}`, (await p.locator('#judul-objek').innerText()) === idAwal);
    await p.getByRole('button', { name: 'Hapus pilihan objek' }).click(); await p.mouse.move(5, 5); await sleep(1500);
    const bersihB = await snap(p);
    const bedaB = await beda(p, selB, bersihB);
    cek(`[${tema}] sorotan bertahan setelah ganti tema ke ${lain}`, bedaB > 150, `piksel berbeda dari setelah dibatalkan: ${bedaB}`);
    await ganti(tema);
    const bedaDasar = await beda(p, dasar, await snap(p));
    // gaya tileset harus sama dengan tema (terang = warna bangunan abu-biru, gelap = tanpa gaya); piksel hanya pelengkap (derau LOD/basemap)
    const gaya = await p.evaluate(() => { const st = window.__spectra.tileset.style; return st ? JSON.stringify(st.style ?? st._style ?? st.color ?? 'ada') : null; });
    const gayaOk = tema === 'terang' ? !!gaya && /7C8E9C/i.test(gaya) : gaya === null;
    cek(`[${tema}] setelah batal pilih dan kembali ke ${tema}, gaya bangunan = gaya tema dan piksel mendekati dasar (tanpa warna campuran)`, gayaOk && bedaDasar < 1200, `gaya=${(gaya || 'null').slice(0, 60)}; piksel berbeda dari dasar: ${bedaDasar}`);
    cek(`[${tema}] panel kanan tidak menutup otomatis tetapi menampilkan keadaan kosong`, await p.getByText('Belum ada objek dipilih').isVisible());
    if (tema === 'terang') {
      const k0 = await kamera(p);
      await p.getByRole('button', { name: 'Atas' }).click(); await sleep(2500);
      cek('mode Atas: pitch ≈ -90°', (await kamera(p)).pitch * DERAJAT < -85);
      await p.getByRole('button', { name: '3D', exact: true }).click(); await sleep(2500);
      cek('mode 3D: pitch ≈ -45°', Math.abs((await kamera(p)).pitch * DERAJAT + 45) < 3);
      await p.getByRole('button', { name: 'Perbesar' }).click(); await sleep(900);
      cek('zoom in menurunkan tinggi kamera', (await kamera(p)).h < k0.h * 0.95);
      await p.evaluate(() => { const c = window.__spectra.viewer.camera; c.setView({ orientation: { heading: 1.0, pitch: c.pitch, roll: 0 } }); window.__spectra.viewer.scene.requestRender(); }); await sleep(600);
      await p.getByRole('button', { name: /Kompas/ }).click(); await sleep(2000);
      const hd = (await kamera(p)).heading; cek('kompas mengembalikan arah utara', Math.min(hd, 2 * Math.PI - hd) < 0.05);
      const lon0 = (await kamera(p)).lon;
      const cari = p.getByRole('combobox', { name: 'Cari kelurahan' });
      await cari.fill('loktuan'); await sleep(300);
      cek('pencarian menampilkan kelurahan yang cocok', (await p.getByRole('option', { name: /Loktuan/ }).count()) > 0);
      await p.keyboard.press('Enter'); await sleep(3500);
      cek('Enter pada hasil pencarian menerbangkan kamera', Math.abs((await kamera(p)).lon - lon0) * DERAJAT > 0.003);
      await cari.fill('zzzz'); await sleep(200);
      cek('pencarian tanpa hasil memberi pesan', await p.getByText('Tidak ada kelurahan yang cocok').isVisible());
      // gerak mouse tidak memicu render
      const f0 = await p.evaluate(() => window.__spectra.viewer.scene.frameState.frameNumber);
      for (let i = 0; i < 30; i++) { await p.mouse.move(400 + i * 8, 400 + i * 3); await sleep(30); }
      await sleep(500);
      cek('gerak mouse tidak memicu render', (await p.evaluate(() => window.__spectra.viewer.scene.frameState.frameNumber)) - f0 <= 2);
      // geoportal dengan backend mati (HTTP 500 dari proxy)
      const kiri = p.locator('#panel-kiri'); await kiri.evaluate((e) => (e.scrollTop = e.scrollHeight)); await sleep(500);
      cek('geoportal: pesan ramah saat backend mati (HTTP 500)', /Backend spectra tidak dapat dihubungi/.test(await kiri.innerText()) && !/Internal Server Error/.test(await kiri.innerText()));
      await p.locator('#url-geoportal').fill('https://geoportal.bontangkota.go.id/geoserver/ows');
      await p.getByRole('button', { name: 'Periksa', exact: true }).click(); await sleep(1500);
      cek('geoportal: Periksa saat backend mati juga ramah', (await p.getByRole('alert').filter({ hasText: 'tidak dapat dihubungi' }).count()) > 0);
      // aksesibilitas
      cek('semua tombol punya nama', (await p.evaluate(() => [...document.querySelectorAll('button')].filter((b) => !(b.getAttribute('aria-label') || b.innerText.trim() || b.getAttribute('aria-labelledby'))).length)) === 0);
      await p.reload({ waitUntil: 'load' }); await sleep(1500);
      cek('tema tersimpan setelah reload', (await p.evaluate(() => document.documentElement.dataset.theme)) === 'terang');
      if (SHOT) await p.screenshot({ path: path.join(SHOT, 'tata_letak_1440.png') });
    }
    cek(`[${tema}] 1440: tanpa galat konsol/halaman`, !p.err.length, p.err.join('|'));
    await p.context().close();
  }

  // ---- Panel dan laci di 1440 / 1024 / 390 ----
  for (const [w, h] of [[1440, 800], [1024, 768], [390, 800]]) {
    const p = await buka(w, h, 'terang'); const lebar = w >= 1280;
    cek(`${w}: panel kiri ${lebar ? 'terbuka' : 'tertutup'} awalnya, panel kanan tertutup`, (await tampil(p, '#panel-kiri')) === lebar && !(await tampil(p, '#panel-kanan')));
    const bukaKanan = w >= 768 ? p.getByRole('button', { name: /Tampilkan informasi objek/ }) : p.getByRole('button', { name: 'Tampilkan panel informasi' });
    await bukaKanan.click(); await sleep(400);
    cek(`${w}: tombol membuka panel kanan`, await tampil(p, '#panel-kanan'));
    if (!lebar) cek(`${w}: membuka panel kanan menutup laci kiri (satu per satu)`, !(await tampil(p, '#panel-kiri')));
    await p.keyboard.press('Escape'); await sleep(400);
    cek(`${w}: Esc menutup panel kanan`, !(await tampil(p, '#panel-kanan')));
    cek(`${w}: fokus kembali ke tombol pembuka`, /informasi/.test(await p.evaluate(() => document.activeElement.getAttribute('aria-label') || '')));
    const kiri = p.getByRole('button', { name: /panel layer/ });
    await kiri.click(); await sleep(400); const sesudahKlik = await tampil(p, '#panel-kiri');
    await kiri.click(); await sleep(400);
    cek(`${w}: tombol header membuka/menutup panel kiri`, sesudahKlik !== (await tampil(p, '#panel-kiri')));
    if (!lebar) {
      await kiri.click(); await sleep(400); await p.keyboard.press('Escape'); await sleep(400);
      cek(`${w}: Esc menutup laci kiri`, !(await tampil(p, '#panel-kiri')));
    }
    cek(`${w}: tanpa scroll horizontal`, await p.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    if (w === 390) {
      const hdr = await p.evaluate(() => { const e = [...document.querySelectorAll('header span')].find((s) => s.textContent.trim() === 'spectra'); const r = e?.getBoundingClientRect(); return !!r && r.width > 0 && r.right <= innerWidth; });
      cek('390: nama spectra terlihat di header, judul tidak terpotong (disembunyikan secara visual)', hdr && (await p.getByRole('heading', { level: 1, name: 'Digital Twin Kota Bontang' }).count()) === 1);
    }
    cek(`${w}: tanpa galat`, !p.err.length, p.err.join('|'));
    await p.context().close();
  }

  await browser.close();
  const gagal = hasil.filter((x) => !x).length;
  console.log(`\n${hasil.length - gagal}/${hasil.length} lulus`);
  process.exit(gagal ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
