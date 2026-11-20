// Helper murni (tanpa Vue/Cesium) untuk membaca metadata dari hasil picking 3D Tiles.
// Dipisah agar mudah diuji di Node tanpa browser/WebGL.

export const TILES_BASE_PATH = '/tiles/';

/**
 * Ubah slug folder menjadi nama tampilan. 'tanjung_laut_indah' -> 'Tanjung Laut Indah'.
 * @param {string} slug
 */
export function slugToName(slug) {
  if (!slug) return '';
  return slug
    .split('_')
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

/**
 * Urai URL konten tile menjadi slug kelurahan & path tile.
 * 'http://x/tiles/api_api/t/3/2/2.glb?v=1' -> { slug: 'api_api', tile: 't/3/2/2' }
 * URL di luar '/tiles/<slug>/...' dikembalikan apa adanya (slug null, tanpa query/hash,
 * ekstensi tidak diubah).
 * @param {string} url
 * @returns {{ slug: string|null, tile: string }}
 */
export function parseContentUrl(url = '') {
  const clean = String(url).split(/[?#]/)[0];
  const idx = clean.indexOf(TILES_BASE_PATH);
  if (idx === -1) return { slug: null, tile: clean };

  const rest = clean.slice(idx + TILES_BASE_PATH.length); // 'api_api/t/3/2/2.glb'
  const slash = rest.indexOf('/');
  if (slash === -1) return { slug: null, tile: rest };

  return {
    slug: rest.slice(0, slash),
    tile: rest.slice(slash + 1).replace(/\.[a-z0-9]+$/i, '')
  };
}

/**
 * Ambil nilai pertama yang terisi dari kandidat kunci (tidak peka huruf besar/kecil).
 * Nilai null/undefined/'' dilewati; angka 0 tetap dianggap nilai valid.
 * @param {Record<string, unknown>} props
 * @param {string[]} candidates
 */
export function pickFirst(props, candidates) {
  const lower = new Map(Object.keys(props).map((k) => [k.toLowerCase(), props[k]]));
  for (const key of candidates) {
    const value = lower.get(key.toLowerCase());
    if (value !== undefined && value !== null && value !== '') return value;
  }
  return undefined;
}

/**
 * Baca seluruh properti feature 3D Tiles secara dinamis; aman bila tidak ada property table.
 * Properti bernilai undefined/null dilewati: Cesium mengembalikan undefined untuk nilai `noData`
 * (mis. jumlah_lantai atau luas_tapak kosong), dan tile tanpa kolom itu sama sekali tidak
 * punya properti tersebut; keduanya harus tampil sama (baris tidak muncul). Angka 0 dan '' tetap disimpan.
 * @param {{ getPropertyIds: () => string[], getProperty: (id: string) => unknown }} feature
 * @returns {Record<string, unknown>}
 */
export function readFeatureProperties(feature) {
  const props = {};
  try {
    for (const name of feature.getPropertyIds()) {
      const value = feature.getProperty(name);
      if (value !== undefined && value !== null) props[name] = value;
    }
  } catch {
    // Konten tanpa batch/property table.
  }
  return props;
}
