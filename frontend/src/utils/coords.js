// Format koordinat dan pembulatan skala peta (murni, tanpa Cesium).

const desimal = (n, d) => n.toFixed(d).replace('.', ',');

/** Derajat desimal -> "0,13456° LU, 117,48370° BT" (lintang utara/selatan, bujur timur/barat). */
export function formatCoord(lat, lon) {
  return `${desimal(Math.abs(lat), 5)}° ${lat >= 0 ? 'LU' : 'LS'}, ${desimal(Math.abs(lon), 5)}° ${lon >= 0 ? 'BT' : 'BB'}`;
}

/**
 * Pilih panjang batang skala yang "bulat" (1/2/5 x 10^n m) dan tidak melebihi jarak yang tersedia.
 * @param {number} meters jarak nyata yang mewakili lebar maksimum batang
 * @returns {{meters: number, label: string, fraction: number}|null} fraction = meters / jarak tersedia (0..1)
 */
export function niceScale(meters) {
  if (!Number.isFinite(meters) || meters <= 0) return null;
  const pangkat = 10 ** Math.floor(Math.log10(meters));
  const kandidat = [5, 2, 1].map((k) => k * pangkat).find((m) => m <= meters) ?? pangkat;
  const label = kandidat >= 1000 ? `${kandidat / 1000} km` : `${kandidat} m`;
  return { meters: kandidat, label, fraction: kandidat / meters };
}
