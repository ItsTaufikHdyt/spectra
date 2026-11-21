// Uji "Kondisi Terkini" di Chromium headless: panel tampil, data asli muncul, sumber gagal -> "data lama"/"tidak tersedia",
// browser tidak memanggil host luar untuk data terkini, kontras teks >= 4,5:1, dan polling tidak memicu render (GPU diam).
//   APP_URL=http://localhost:3001 node frontend/tests/browser/uji_terkini.cjs      (butuh backend baru di balik proxy /api)
// Env: APP_URL (http://localhost:3000), SHOT_DIR (tangkapan layar), PLAYWRIGHT_DIR, CHROME_PATH, GPU_BUSY, GPU_ARGS=swiftshader.
// Catatan: uji ini memakai sumber ASLI (butuh internet di backend); kasus gagal disimulasikan lewat page.route di browser.
const fs = require('fs');
const path = require('path');
const HOME = process.env.HOME;
const { chromium } = require(process.env.PLAYWRIGHT_DIR || `${HOME}/.npm/_npx/e41f203b7505f1fb/node_modules/playwright`);
const CHROME = process.env.CHROME_PATH || `${HOME}/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`;
const URL = process.env.APP_URL || 'http://localhost:3000';
const SHOT = process.env.SHOT_DIR;
const GPU_BUSY = process.env.GPU_BUSY || '/sys/class/drm/card1/device/gpu_busy_percent';
const ARGS = process.env.GPU_ARGS === 'swiftshader' ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : ['--use-gl=angle', '--use-angle=gl-egl'];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const gpu = () => { try { return Number(fs.readFileSync(GPU_BUSY, 'utf8')); } catch { return null; } };
const hasil = [];
const cek = (nama, ok, info = '') => { hasil.push(!!ok); console.log(`${ok ? 'LULUS' : 'GAGAL'}  ${nama}${info ? '  ' + info : ''}`); };
const HOST_TERLARANG = /bmkg\.go\.id|open-meteo\.com|firms\.modaps|earthdata\.nasa|nasa\.gov/;

let browser;
async function buka(tema, atur) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript((t) => { try { localStorage.setItem('spectra.theme', t); } catch {} }, tema);
  const page = await ctx.newPage(); page.err = []; page.req = [];
  page.on('pageerror', (e) => page.err.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error' && !/status of 5\d\d|uniform3fv|Failed to load resource/.test(m.text())) page.err.push(m.text()); });
  page.on('request', (r) => page.req.push(r.url()));
  if (atur) await atur(page);
  await page.goto(`${URL}/?debug=perf`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__spectra?.tileset, null, { timeout: 90000 });
  await sleep(2500);
  await page.evaluate(() => { for (const d of document.querySelectorAll('body > div')) if (d.style.position === 'fixed') d.remove(); });
  await page.getByRole('button', { name: /Tampilkan informasi objek/ }).click();
  await page.getByRole('tab', { name: 'Kondisi terkini' }).click();
  return page;
}

// Kontras teks di panel kanan: warna teks vs latar efektif (menelusuri induk; alfa dicampur ke latar induknya).
const kontrasPanel = (page) => page.evaluate(() => {
  const parse = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const [r, g, b, a = 1] = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return { r, g, b, a }; };
  const mix = (f, b) => ({ r: f.r * f.a + b.r * (1 - f.a), g: f.g * f.a + b.g * (1 - f.a), b: f.b * f.a + b.b * (1 - f.a), a: 1 });
  const lum = ({ r, g, b }) => [r, g, b].map((u) => { u /= 255; return u <= 0.03928 ? u / 12.92 : ((u + 0.055) / 1.055) ** 2.4; }).reduce((s, v, i) => s + v * [0.2126, 0.7152, 0.0722][i], 0);
  const bg = (el) => { const pile = []; for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c.a > 0) { pile.push(c); if (c.a === 1) break; } } let r = { r: 255, g: 255, b: 255, a: 1 }; for (const c of pile.reverse()) r = mix(c, r); return r; };
  const gagal = []; let n = 0;
  const w = document.createTreeWalker(document.querySelector('#panel-kanan'), NodeFilter.SHOW_TEXT);
  for (let t; (t = w.nextNode());) {
    const el = t.parentElement; if (!t.nodeValue.trim() || !el.offsetParent || getComputedStyle(el).visibility === 'hidden') continue;
    const b = bg(el); const fg = mix(parse(getComputedStyle(el).color), b); const [x, y] = [lum(fg), lum(b)].sort((p, q) => q - p);
    const k = (x + 0.05) / (y + 0.05); n++; if (k < 4.5) gagal.push(`${k.toFixed(2)} "${t.nodeValue.trim().slice(0, 30)}"`);
  }
  return { n, gagal: [...new Set(gagal)].slice(0, 6) };
});

(async () => {
  // GPU sistem tanpa browser (aplikasi lain ikut memakai GPU), pembanding untuk uji "GPU saat diam"
  const dasar = []; for (let i = 0; i < 10; i++) { dasar.push(gpu()); await sleep(500); }
  const gpuSistem = dasar.some((x) => x == null) ? null : dasar.reduce((a, b) => a + b, 0) / dasar.length;
  browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox', '--ignore-gpu-blocklist', ...ARGS] });
  const kartu = (p, judul) => p.locator('section', { has: p.getByRole('button', { name: judul, exact: true }) });

  for (const tema of ['terang', 'gelap']) {
    const p = await buka(tema);
    for (const j of ['Gempa', 'Cuaca', 'Hotspot', 'Laut']) await p.getByRole('button', { name: j, exact: true }).waitFor({ timeout: 15000 });
    await p.waitForFunction(() => document.querySelectorAll('#panel-kanan a[href^="http"]').length >= 4 && !/Memuat/.test(document.querySelector('#panel-kanan').innerText), null, { timeout: 40000 }).catch(() => {});
    const teks = await p.locator('#panel-kanan').innerText();
    cek(`[${tema}] empat kartu tampil dengan data asli`, /titik dalam 24 jam/.test(teks) && /Perkiraan \d\d:\d\d WITA/.test(teks) && /km dari pusat Bontang/.test(teks) && /tinggi gelombang/.test(teks));
    cek(`[${tema}] tiap kartu memuat sumber, tautan, dan "diperbarui HH:MM WITA"`, (teks.match(/diperbarui \d\d:\d\d WITA/g) || []).length === 4 && (await p.locator('#panel-kanan a[href^="http"]').count()) === 4 && /Open-Meteo \(CC BY 4\.0\)/.test(teks) && /NASA FIRMS/.test(teks) && /BMKG/.test(teks));
    cek(`[${tema}] tanpa label "data lama" saat sumber sehat`, !/data lama/.test(teks));
    const k = await kontrasPanel(p);
    cek(`[${tema}] kontras teks panel >= 4,5:1`, k.gagal.length === 0, `${k.n} teks diperiksa${k.gagal.length ? '; rendah: ' + k.gagal.join(' | ') : ''}`);
    if (SHOT) await p.screenshot({ path: path.join(SHOT, `terkini_${tema}.png`) });

    if (tema === 'terang') {
      const luar = p.req.filter((u) => HOST_TERLARANG.test(u));
      cek('browser tidak memanggil host BMKG/FIRMS/Open-Meteo langsung', luar.length === 0, luar.slice(0, 2).join(' '));
      cek('permintaan data terkini lewat /api/terkini/*', p.req.filter((u) => /\/api\/terkini\//.test(u)).length >= 4);
      // GPU diam dan tanpa render selama panel terbuka (polling hidup): 10 dtk
      await sleep(9000); // animasi ikon (berhingga, ≤ 6 dtk) sudah selesai: keadaan diam sebenarnya
      const f0 = await p.evaluate(() => window.__spectraPerf().frames); const g = [];
      for (let i = 0; i < 20; i++) { g.push(gpu()); await sleep(500); }
      const f1 = await p.evaluate(() => window.__spectraPerf().frames);
      const mean = g.some((x) => x == null) ? null : g.reduce((a, b) => a + b, 0) / g.length;
      cek('panel terbuka + polling tidak memicu render kanvas (0 frame / 10 dtk)', f1 - f0 === 0, `frame +${f1 - f0}`);
      cek('GPU saat diam tidak naik oleh panel (≤ baseline sistem + 3 poin)', mean === null || gpuSistem === null || mean <= gpuSistem + 3, `app ${mean === null ? '?' : mean.toFixed(1)}% vs sistem tanpa browser ${gpuSistem === null ? '?' : gpuSistem.toFixed(1)}%`);
      await p.getByRole('tab', { name: 'Kondisi terkini' }).focus(); await p.keyboard.press('ArrowLeft');
      cek('tab bisa dipindah dengan panah keyboard', (await p.getByRole('tab', { name: 'Peta dan objek' }).getAttribute('aria-selected')) === 'true');
    }
    cek(`[${tema}] tanpa galat konsol/halaman`, !p.err.length, p.err.join('|'));
    await p.context().close();
  }

  // Sumber gagal total (backend mati): tidak tersedia + tombol coba lagi, tanpa angka karangan
  {
    const p = await buka('terang', (pg) => pg.route('**/api/terkini/**', (r) => r.fulfill({ status: 500, contentType: 'text/plain', body: 'Internal Server Error' })));
    await sleep(2500);
    const t = await p.locator('#panel-kanan').innerText();
    cek('backend mati (HTTP 500): "Data tidak tersedia" + pesan ramah + Coba lagi di tiap kartu', (t.match(/Data tidak tersedia/g) || []).length === 4 && /Backend spectra tidak dapat dihubungi/.test(t) && (await p.getByRole('button', { name: 'Coba lagi' }).count()) === 4);
    cek('backend mati: tidak ada angka karangan (tanpa suhu, magnitudo, jumlah)', !/°C|titik dalam|\bM\d|tinggi gelombang/.test(t));
    if (SHOT) await p.screenshot({ path: path.join(SHOT, 'terkini_tidak_tersedia.png') });
    cek('backend mati: tanpa galat halaman', !p.err.length, p.err.join('|'));
    await p.context().close();
  }

  // Data lama: backend menyajikan cache lama (stale=true); dan sumber belum dikonfigurasi (FIRMS)
  {
    const p = await buka('terang', async (pg) => {
      await pg.route('**/api/terkini/gempa', async (r) => { const j = await (await r.fetch()).json(); r.fulfill({ json: { ...j, stale: true, diambil_pada: '2026-11-22T01:00:00+00:00' } }); });
      await pg.route('**/api/terkini/hotspot', (r) => r.fulfill({ json: { sumber: 'NASA FIRMS', atribusi: 'x', url_sumber: 'https://firms.modaps.eosdis.nasa.gov/', dikonfigurasi: false, tersedia: false, stale: false, diambil_pada: null } }));
    });
    await sleep(3500);
    const g = await kartu(p, 'Gempa').innerText();
    cek('stale=true: kartu gempa berlabel "data lama" dengan waktu pengambilan (09:00 WITA)', /data lama/.test(g) && /diperbarui 09:00 WITA/.test(g) && /km dari pusat Bontang/.test(g));
    cek('FIRMS belum dikonfigurasi: pesan "Hotspot belum dikonfigurasi (FIRMS_MAP_KEY)."', /Hotspot belum dikonfigurasi \(FIRMS_MAP_KEY\)\./.test(await kartu(p, 'Hotspot').innerText()));
    if (SHOT) await p.screenshot({ path: path.join(SHOT, 'terkini_data_lama.png') });
    cek('data lama/belum dikonfigurasi: tanpa galat halaman', !p.err.length, p.err.join('|'));
    await p.context().close();
  }

  // Ganti kelurahan saat backend mati: cuaca kelurahan lain tidak boleh tampil sebagai kelurahan ini
  {
    let mati = false;
    const p = await buka('terang', (pg) => pg.route('**/api/terkini/cuaca**', (r) => (mati ? r.fulfill({ status: 500, contentType: 'text/plain', body: 'x' }) : r.continue())));
    await sleep(3500);
    mati = true;
    await p.locator('#cuaca-kelurahan').selectOption('loktuan');
    await sleep(2000);
    const t = await kartu(p, 'Cuaca').innerText();
    cek('ganti kelurahan saat backend mati: "Data tidak tersedia", tanpa cuaca kelurahan lain', /Data tidak tersedia/.test(t) && !/°C/.test(t));
    await p.context().close();
  }

  await browser.close();
  const gagal = hasil.filter((x) => !x).length;
  console.log(`\n${hasil.length - gagal}/${hasil.length} lulus`);
  process.exit(gagal ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
