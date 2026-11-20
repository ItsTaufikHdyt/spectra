// Penyusun SPESIFIKASI gaya tileset (murni, tanpa Cesium) — dipakai composables/tilesetStyle.js.
// Prioritas tampilan: sorotan (per fitur, di tilesetStyle.js) > simulasi > tema.
// Kondisi simulasi menang atas warna tema; tanpa simulasi hanya warna tema.

/**
 * Pengali warna bangunan per tema (Cesium3DTileStyle.color mengalikan warna material).
 * Gelap: tanpa gaya (material apa adanya). Terang: bangunan digelapkan agar kontras di atas peta terang.
 * Nilai terang disetel secara visual (STATUS/spesifikasi §7).
 */
export const BUILDING_STYLE_COLOR = Object.freeze({ gelap: null, terang: '#7C8E9C' });

const isCondition = (c) => Array.isArray(c) && c.length === 2 && typeof c[0] === 'string' && typeof c[1] === 'string';

/**
 * @param {{ theme: 'terang'|'gelap', simulation?: { conditions: [string, string][] } | null }} opts
 * @returns {null | { color: { conditions: [string, string][] } }} null = tanpa gaya (material asli)
 */
export const buildStyleSpec = ({ theme, simulation = null }) => {
  const conditions = simulation?.conditions ?? [];
  if (!conditions.every(isCondition)) {
    throw new Error('Kondisi gaya simulasi harus berupa pasangan [ekspresi, warna] bertipe string');
  }
  const themeColor = BUILDING_STYLE_COLOR[theme] ?? null;
  if (!conditions.length && !themeColor) return null;
  const fallback = themeColor ? `color("${themeColor}")` : 'color("#FFFFFF")';
  return { color: { conditions: [...conditions, ['true', fallback]] } };
};
