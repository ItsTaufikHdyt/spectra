// Warna yang dipakai di peta DAN legenda — satu sumber agar keduanya tidak menyimpang.
// Dua set (per tema): garis dan objek harus terbaca di atas peta dasar terang maupun gelap
// (kontras diukur; lihat docs/desain/spesifikasi-redesign.md §7).

/** Sorotan objek terpilih: tetap amber di kedua tema (hue berbeda dari bangunan abu dan aksen biru UI). */
export const HIGHLIGHT_HEX = '#F0B43C';

const GELAP = Object.freeze({
  building: '#D9DEE2', // perkiraan tampilan material glb di atas peta gelap
  overview: '#CFE0E8', // kotak ikhtisar kelurahan saat kamera jauh
  selection: HIGHLIGHT_HEX,
  kelurahan: '#FFFFFF', // batas kelurahan (garis tebal)
  rt: '#C3D3DC', // batas RT (garis tipis)
  sungai: '#38BDF8',
  drainase: '#5EEAD4', // fitur "Drainase …" dibedakan dari sungai (kategori belum diputuskan)
  globeBase: '#0D1820', // warna globe sebelum tile peta dasar tiba
  markerOutline: '#0D1820',
  labelFill: '#FFFFFF', // label kotak ikhtisar kelurahan
  labelOutline: '#0D1820'
});

const TERANG = Object.freeze({
  building: '#7C8E9C', // = warna gaya tileset tema terang (tilesetStyleSpec.js); render berkisar lebih gelap/terang menurut pencahayaan
  overview: '#4F6B7D',
  selection: HIGHLIGHT_HEX,
  kelurahan: '#0D1820',
  rt: '#5B7385',
  sungai: '#0284C7',
  drainase: '#0F766E',
  globeBase: '#E9EEF1',
  markerOutline: '#0D1820',
  labelFill: '#0D1820',
  labelOutline: '#FFFFFF'
});

export const MAP_COLORS_BY_THEME = Object.freeze({ gelap: GELAP, terang: TERANG });

/** Warna peta untuk tema ('terang' | 'gelap'); tema tak dikenal memakai gelap (tampilan awal aplikasi). */
export const getMapColors = (theme) => MAP_COLORS_BY_THEME[theme] ?? GELAP;
