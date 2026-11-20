// Uji regresi tema/basemap di Chromium headless (GPU nyata). Lihat README.md di folder ini.
//   node frontend/tests/browser/uji_tema.cjs            # semua uji; kode keluar 1 bila ada yang gagal
// Env: PLAYWRIGHT_DIR, CHROME_PATH, APP_URL (default http://localhost:3000), GPU_ARGS=swiftshader, SHOT_DIR (tangkapan layar opsional)
const fs = require('fs');
const path = require('path');
const HOME = process.env.HOME;
const { chromium } = require(process.env.PLAYWRIGHT_DIR || `${HOME}/.npm/_npx/e41f203b7505f1fb/node_modules/playwright`);
const CHROME = process.env.CHROME_PATH || `${HOME}/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`;
const URL = process.env.APP_URL || 'http://localhost:3000';
const ARGS = process.env.GPU_ARGS === 'swiftshader' ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : ['--use-gl=angle', '--use-angle=gl-egl'];
const SHOT = process.env.SHOT_DIR;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const hasil = [];
const cek = (nama, ok, info = '') => { hasil.push(ok); console.log(`${ok ? 'LULUS' : 'GAGAL'}  ${nama}${info ? '  ' + info : ''}`); };

// Kontras WCAG 2.x antara dua warna hex.
const lum = (h) => { const c = [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
const kontras = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const hexDari = (rgb) => '#' + rgb.trim().split(/\s+/).map((n) => Number(n).toString(16).padStart(2, '0')).join('');

async function buka(opsi = {}, init) {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox', '--ignore-gpu-blocklist', ...ARGS] });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 850 }, colorScheme: opsi.colorScheme || 'light' });
  if (init) await ctx.addInitScript(init);
  const page = await ctx.newPage();
  const log = { galat: [], konsol: [], tile: [] };
  page.on('pageerror', (e) => log.galat.push(String(e)));
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) log.konsol.push(m.text()); });
  page.on('request', (r) => { const m = r.url().match(/arcgisonline\.com\/.*?(World_\w+)\//); if (m) log.tile.push(m[1]); });
  await page.goto(`${URL}/?debug=perf`, { waitUntil: 'load' });
  await page.waitForFunction(() => !!window.__spectra, null, { timeout: 90000 });
  await sleep(2500);
  return { browser, ctx, page, log };
}
const tema = (p) => p.evaluate(() => document.documentElement.dataset.theme);
const klik = (p, label) => p.getByRole('button', { name: label }).first().click();
const baru = (log) => log.konsol.filter((t) => !/uniform3fv|\/api\/|Failed to load resource|Basemap .* gagal/.test(t));

(async () => {
  // 1. Kontras batas kontrol (>= 3:1) dari nilai nyata di main.css
  const css = fs.readFileSync(path.join(__dirname, '../../src/assets/main.css'), 'utf8');
  for (const t of ['terang', 'gelap']) {
    const blok = css.match(new RegExp(`html\\[data-theme="${t}"\\]\\s*{([^}]*)}`))[1];
    const v = (n) => hexDari(blok.match(new RegExp(`--bontang-${n}:\\s*([\\d ]+);`))[1]);
    const rendah = ['ink', 'panel', 'raised'].map((n) => [n, kontras(v('edge'), v(n))]).filter(([, k]) => k < 3);
    cek(`kontras edge >= 3:1 (${t})`, !rendah.length, ['ink', 'panel', 'raised'].map((n) => `${n} ${kontras(v('edge'), v(n)).toFixed(2)}`).join(' / '));
  }

  // 2. Tema: first paint, Sistem + perubahan OS tanpa reload, persist, localStorage diblokir
  for (const [os, simpan, harap] of [['light', null, 'terang'], ['dark', null, 'gelap'], ['light', 'gelap', 'gelap']]) {
    const awal = [];
    const { browser, page, log } = await buka({ colorScheme: os }, `
      try { ${simpan ? `localStorage.setItem('spectra.theme','${simpan}')` : ''} } catch {}
      new MutationObserver(() => window.__t = (window.__t || []).concat(document.documentElement.dataset.theme)).observe(document, { subtree: true, attributes: true, attributeFilter: ['data-theme'] });`);
    const riwayat = await page.evaluate(() => window.__t || []);
    cek(`tema awal OS ${os}${simpan ? ' + tersimpan ' + simpan : ''} = ${harap}, tanpa pergantian nilai`, (await tema(page)) === harap && new Set(riwayat).size <= 1, `riwayat=${[...new Set(riwayat)]}`);
    cek('  tanpa galat halaman', !log.galat.length, log.galat.join('|'));
    await browser.close();
  }
  {
    const { browser, ctx, page } = await buka({ colorScheme: 'light' });
    const cdp = await ctx.newCDPSession(page);
    const emu = (v) => cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: v }] });
    await klik(page, 'Tema mengikuti perangkat'); await sleep(300);
    await emu('dark'); await sleep(500); const a = await tema(page);
    await emu('light'); await sleep(500); const b = await tema(page);
    cek('mode Sistem mengikuti OS tanpa reload (gelap lalu terang)', a === 'gelap' && b === 'terang', `${a}, ${b}`);
    await klik(page, 'Tema gelap'); await sleep(300); await emu('light'); await page.reload({ waitUntil: 'load' }); await sleep(1500);
    cek('pilihan gelap tersimpan setelah reload walau OS terang', (await tema(page)) === 'gelap' && (await page.evaluate(() => localStorage.getItem('spectra.theme'))) === 'gelap');
    await browser.close();
  }
  {
    const { browser, page, log } = await buka({}, `Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('diblokir', 'SecurityError'); } });`);
    await klik(page, 'Tema gelap'); await sleep(300);
    cek('localStorage diblokir: app jalan dan toggle bekerja', (await tema(page)) === 'gelap' && !log.galat.length, log.galat.join('|'));
    await browser.close();
  }

  // 3. Basemap: Otomatis mengikuti tema, manual tidak tertimpa
  {
    const { browser, page, log } = await buka({ colorScheme: 'light' });
    const pakai = (re) => log.tile.some((t) => re.test(t));
    cek('Esri terang termuat di tema terang', pakai(/Light_Gray/));
    await klik(page, 'Tema gelap'); await sleep(4000);
    cek('Otomatis: tema gelap memuat Esri gelap', pakai(/Dark_Gray/));
    await klik(page, 'Tema terang'); await sleep(500);
    const label = page.getByText('Citra satelit', { exact: false }).first();
    if (await label.count()) {
      await label.click(); await sleep(3500);
      await klik(page, 'Tema gelap'); await sleep(2500);
      const ls = await page.evaluate(() => localStorage.getItem('spectra.basemap'));
      cek('basemap manual (satelit) tidak tertimpa saat tema berganti', /satelit/.test(ls || ''), `spectra.basemap=${ls}`);
    } else cek('pilihan basemap satelit ditemukan di panel', false, 'buka panel Lapisan dulu / label berubah');
    if (SHOT) await page.screenshot({ path: path.join(SHOT, 'basemap.png') });
    cek('konsol tanpa galat/peringatan baru', !baru(log).length && !log.galat.length, baru(log).concat(log.galat).join('|'));
    await browser.close();
  }

  // 4. Fallback: domain Esri diblokir -> tetap jalan, tanpa galat halaman
  {
    const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox', '--ignore-gpu-blocklist', ...ARGS] });
    const page = await (await browser.newContext({ viewport: { width: 1440, height: 850 } })).newPage();
    const galat = []; page.on('pageerror', (e) => galat.push(String(e)));
    await page.route(/arcgisonline\.com/, (r) => r.abort());
    await page.goto(`${URL}/?debug=perf`, { waitUntil: 'load' });
    await page.waitForFunction(() => !!window.__spectra, null, { timeout: 90000 }); await sleep(6000);
    const kredit = await page.evaluate(() => document.querySelector('.cesium-widget-credits')?.textContent || '');
    cek('fallback OSM saat Esri diblokir: atribusi OSM tampil, tanpa galat halaman', /OpenStreetMap/.test(kredit) && !galat.length, kredit.replace(/\s+/g, ' ').slice(0, 80));
    await browser.close();
  }

  const gagal = hasil.filter((x) => !x).length;
  console.log(`\n${hasil.length - gagal}/${hasil.length} lulus`);
  process.exit(gagal ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
