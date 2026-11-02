// Format angka Indonesia (koma desimal, titik ribuan) untuk semua nilai di UI.
// Helper murni (tanpa Vue/Cesium) agar bisa diuji dengan `npm test`.

const cache = new Map();
const formatter = (min, max) => {
  const key = `${min}:${max}`;
  if (!cache.has(key)) {
    cache.set(
      key,
      new Intl.NumberFormat('id-ID', { minimumFractionDigits: min, maximumFractionDigits: max })
    );
  }
  return cache.get(key);
};

/** Angka -> string id-ID. Nilai non-angka -> null (biar pemanggil memilih tampilan kosong). */
export function formatNumber(value, { minDigits = 0, maxDigits = 2 } = {}) {
  const n = typeof value === 'number' ? value : Number.parseFloat(value);
  if (!Number.isFinite(n)) return null;
  return formatter(minDigits, Math.max(minDigits, maxDigits)).format(n);
}

/** Derajat desimal, 6 digit (~0,1 m). */
export const formatDegrees = (value) => {
  const s = formatNumber(value, { minDigits: 6, maxDigits: 6 });
  return s === null ? null : `${s}°`;
};

/** Nilai dengan satuan, mis. formatWithUnit(12.5, 'm') -> '12,5 m'. */
export const formatWithUnit = (value, unit, options) => {
  const s = formatNumber(value, options);
  return s === null ? null : `${s} ${unit}`;
};
