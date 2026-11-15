// Profil "Mode tampilan": data murni (tanpa Vue/Cesium) agar bisa diuji dengan `npm test`.
// Dipakai oleh stores/settingsStore.js (pilihan pengguna) dan composables/useRenderQuality.js
// (menerapkan ke viewer, scene, globe, dan tileset).
//
// Aturan pemilihan nilai:
//  - tilesetSSE: maximumScreenSpaceError 3D Tiles (default Cesium 16; lebih besar = lebih kasar).
//  - globeSSE  : maximumScreenSpaceError imagery/terrain globe (default Cesium 2).
//  - msaa / fxaa: pilih salah satu (MSAA 4x mahal di GPU terintegrasi). FXAA murah.
//  - efek      : tidak berpengaruh pada analisis kota; tetap menyala hanya di mode Kualitas.

export const DEFAULT_LEVEL = 'seimbang';

export const DISPLAY_MODES = Object.freeze({
  hemat: {
    label: 'Hemat',
    note: 'GPU terintegrasi atau baterai. Resolusi 75%, detail lebih kasar, 30 fps saat bergerak.',
    resolutionScale: () => 0.75,
    tilesetSSE: 32,
    globeSSE: 4,
    tileCacheSize: 60,
    msaa: 1,
    fxaa: true,
    targetFrameRate: 30,
    efek: { fog: false, skyAtmosphere: false, groundAtmosphere: false, sunMoon: false, skyBox: false }
  },
  seimbang: {
    label: 'Seimbang',
    note: 'Bawaan. Resolusi penuh, anti-aliasing MSAA 2x, tanpa efek atmosfer tanah.',
    resolutionScale: () => 1,
    tilesetSSE: 24,
    globeSSE: 3,
    tileCacheSize: 100,
    msaa: 2,
    fxaa: false,
    targetFrameRate: null,
    efek: { fog: true, skyAtmosphere: true, groundAtmosphere: false, sunMoon: false, skyBox: false }
  },
  kualitas: {
    label: 'Kualitas',
    note: 'GPU kuat. Ikut resolusi layar (maks. 2x), detail tertinggi, MSAA 4x, semua efek.',
    resolutionScale: (dpr) => Math.max(1, Math.min(dpr || 1, 2)),
    tilesetSSE: 16,
    globeSSE: 2,
    tileCacheSize: 200,
    msaa: 4,
    fxaa: false,
    targetFrameRate: null,
    efek: { fog: true, skyAtmosphere: true, groundAtmosphere: true, sunMoon: true, skyBox: true }
  }
});

export const DISPLAY_LEVELS = Object.freeze(Object.keys(DISPLAY_MODES));

export const isDisplayLevel = (v) => typeof v === 'string' && Object.hasOwn(DISPLAY_MODES, v);
