// Logika tema murni (tanpa Vue/Cesium/DOM) agar mudah diuji di Node.
// Nilai tema memakai bahasa Indonesia: 'terang' | 'gelap'. Preferensi pengguna: 'sistem' | 'terang' | 'gelap'.

export const THEMES = Object.freeze(['terang', 'gelap']);
export const THEME_PREFS = Object.freeze(['sistem', 'terang', 'gelap']);
export const THEME_STORAGE_KEY = 'spectra.theme';
export const BASEMAP_STORAGE_KEY = 'spectra.basemap';
/** Mode basemap otomatis = mengikuti tema (id basemap 'terang' / 'gelap'). */
export const BASEMAP_AUTO = 'otomatis';

export const isThemePref = (v) => THEME_PREFS.includes(v);
export const isTheme = (v) => THEMES.includes(v);

/** Tema yang dipakai: pilihan eksplisit menang; 'sistem' mengikuti prefers-color-scheme. */
export const resolveTheme = (preference, systemDark) => {
  if (preference === 'terang' || preference === 'gelap') return preference;
  return systemDark ? 'gelap' : 'terang';
};

/** Mode basemap valid bila 'otomatis' atau salah satu id basemap yang dikenal. */
export const isBasemapMode = (v, ids) => v === BASEMAP_AUTO || ids.includes(v);

/** id basemap yang ditampilkan: otomatis -> mengikuti tema; mode manual tidak tertimpa tema. */
export const resolveBasemap = (mode, theme) => (mode === BASEMAP_AUTO ? theme : mode);

// localStorage bisa melempar error (jendela privat, data situs diblokir): selalu dibungkus.
export const readStored = (key) => {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
};
export const writeStored = (key, value) => {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Tidak tersimpan; pilihan tetap berlaku selama sesi ini.
  }
};
