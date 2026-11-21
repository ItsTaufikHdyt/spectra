// Helper murni untuk "Kondisi Terkini": waktu WITA, arah mata angin, pemilihan slot cuaca. Tanpa Cesium/Vue.

const TZ = 'Asia/Makassar';
const jamFmt = new Intl.DateTimeFormat('en-GB', { timeZone: TZ, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
const tglFmt = new Intl.DateTimeFormat('id-ID', { timeZone: TZ, day: 'numeric', month: 'short' });

/** ISO (UTC atau beroffset) -> "HH:MM WITA". Nilai kosong/tidak valid -> '–'. */
export function jamWita(iso) {
  const d = new Date(iso ?? NaN);
  return Number.isNaN(d.getTime()) ? '–' : `${jamFmt.format(d)} WITA`;
}

/** ISO -> "22 Nov 03:52 WITA". */
export function tanggalJamWita(iso) {
  const d = new Date(iso ?? NaN);
  return Number.isNaN(d.getTime()) ? '–' : `${tglFmt.format(d)} ${jamFmt.format(d)} WITA`;
}

/** Waktu lokal tanpa zona dari sumber ("2026-11-22 07:00:00" / "2026-11-22T07:00") -> "07:00". */
export const jamLokal = (s) => (typeof s === 'string' && s.length >= 16 ? s.slice(11, 16) : '–');

const MATA_ANGIN = ['U', 'TL', 'T', 'TG', 'S', 'BD', 'B', 'BL']; // utara, timur laut, timur, tenggara, selatan, barat daya, barat, barat laut

/** Derajat arah (0–360, asal angin/gelombang) -> mata angin Indonesia. */
export function mataAngin(derajat) {
  if (!Number.isFinite(derajat)) return '–';
  return MATA_ANGIN[Math.round((((derajat % 360) + 360) % 360) / 45) % 8];
}

/** Slot cuaca "sekarang" = slot terakhir yang waktunya <= sekarang (atau slot pertama), diikuti `n` slot berikutnya. */
export function slotCuaca(jam, nowMs = Date.now(), n = 5) {
  if (!Array.isArray(jam) || !jam.length) return { sekarang: null, berikut: [] };
  let i = 0;
  jam.forEach((s, k) => { if (Date.parse(s.waktu_utc.replace(' ', 'T') + (/[zZ]|[+-]\d\d:?\d\d$/.test(s.waktu_utc) ? '' : 'Z')) <= nowMs) i = k; });
  return { sekarang: jam[i], berikut: jam.slice(i + 1, i + 1 + n) };
}

/** Umur data (detik) dari `diambil_pada`; null bila tidak diketahui. */
export const umurDetik = (diambilPada, nowMs = Date.now()) => {
  const t = Date.parse(diambilPada ?? '');
  return Number.isNaN(t) ? null : Math.max(0, Math.round((nowMs - t) / 1000));
};

/**
 * Ikon untuk deskripsi cuaca BMKG ("Cerah Berawan", "Hujan Ringan", ...). Tidak dikenal -> null (tanpa ikon, bukan tebakan).
 * `waktuLokal` ("2026-11-22 19:00:00") menentukan malam (18.00-05.59) untuk ikon bulan.
 */
export function ikonCuaca(desc, waktuLokal) {
  const d = String(desc ?? '').toLowerCase();
  const jam = Number(String(waktuLokal ?? '').slice(11, 13));
  const malam = Number.isFinite(jam) && (jam >= 18 || jam < 6);
  if (/petir|badai/.test(d)) return 'petir';
  if (/hujan/.test(d)) return 'hujan';
  if (/kabut|asap|kabur/.test(d)) return 'kabut';
  if (/cerah berawan/.test(d)) return malam ? 'cerah-berawan-malam' : 'cerah-berawan';
  if (/berawan/.test(d)) return 'berawan';
  if (/cerah/.test(d)) return malam ? 'cerah-malam' : 'cerah';
  return null;
}
