// Satu perintah untuk semua uji browser: npm run test:browser (dev server :3000 harus jalan).
// ukur_performa.cjs TIDAK ikut (pengukuran, bukan lulus/gagal); jalankan terpisah.
const { spawnSync } = require('child_process');
const path = require('path');
let gagal = 0;
for (const f of ['uji_tema.cjs', 'uji_tata_letak.cjs']) {
  console.log(`\n=== ${f} ===`);
  const r = spawnSync('node', [path.join(__dirname, f)], { stdio: 'inherit' });
  if (r.status !== 0) gagal++;
}
console.log(gagal ? `\n${gagal} berkas uji gagal` : '\nSemua uji browser lulus');
process.exit(gagal ? 1 : 0);
