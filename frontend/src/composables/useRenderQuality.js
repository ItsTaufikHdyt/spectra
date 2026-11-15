import { effectScope, watch } from 'vue';
import { requestRender, viewer } from './useCesium';
import { useSettingsStore } from '@/stores/settingsStore';
import { DISPLAY_MODES } from '@/utils/displayModes';

/**
 * Menerapkan "Mode tampilan" (utils/displayModes.js) ke viewer, scene, globe, dan tileset.
 * Mengubah mode di UI langsung berlaku tanpa memuat ulang halaman.
 *
 * `?rs=0.8` di URL menimpa resolutionScale (untuk uji/penyetelan; tidak disimpan).
 * Objek Cesium tidak disimpan di sini kecuali referensi tileset biasa (bukan ref/reactive).
 */
let tileset = null;
let scope = null;

const isAlive = () => !!viewer.value && !viewer.value.isDestroyed();

const rsOverride = () => {
  const n = Number(new URLSearchParams(window.location.search).get('rs'));
  return Number.isFinite(n) && n >= 0.25 && n <= 3 ? n : null;
};

/** Profil aktif; dipakai use3DTiles saat membuat tileset agar SSE awal sudah benar. */
export const currentProfile = () => DISPLAY_MODES[useSettingsStore().level];

/** Terapkan profil ke viewer dan tileset yang sedang aktif. */
export const applyRenderQuality = () => {
  if (!isAlive()) return;
  const v = viewer.value;
  const scene = v.scene;
  const p = currentProfile();

  v.resolutionScale = rsOverride() ?? p.resolutionScale(window.devicePixelRatio);
  scene.msaaSamples = p.msaa; // setter Cesium membatasi ke nilai yang didukung GPU
  scene.postProcessStages.fxaa.enabled = p.fxaa;
  v.targetFrameRate = p.targetFrameRate ?? undefined;

  scene.fog.enabled = p.efek.fog;
  if (scene.skyAtmosphere) scene.skyAtmosphere.show = p.efek.skyAtmosphere;
  scene.globe.showGroundAtmosphere = p.efek.groundAtmosphere;
  if (scene.sun) scene.sun.show = p.efek.sunMoon;
  if (scene.moon) scene.moon.show = p.efek.sunMoon;
  if (scene.skyBox) scene.skyBox.show = p.efek.skyBox;

  scene.globe.maximumScreenSpaceError = p.globeSSE;
  scene.globe.tileCacheSize = p.tileCacheSize;

  if (tileset && !tileset.isDestroyed()) tileset.maximumScreenSpaceError = p.tilesetSSE;
  requestRender();
};

/** Mulai: terapkan sekarang dan ikuti perubahan pilihan pengguna. Aman dipanggil ulang. */
export const startRenderQuality = (loadedTileset = null) => {
  if (loadedTileset) tileset = loadedTileset;
  if (!isAlive()) return;
  if (!scope) {
    // effectScope(true) = detached: tidak ikut berhenti bersama komponen pemanggil.
    scope = effectScope(true);
    const settings = useSettingsStore();
    scope.run(() => watch(() => settings.level, applyRenderQuality));
  }
  applyRenderQuality();
};

/** Lepas watcher dan referensi tileset. Idempoten; panggil di teardown. */
export const releaseRenderQuality = () => {
  scope?.stop();
  scope = null;
  tileset = null;
};

if (import.meta.hot) import.meta.hot.dispose(releaseRenderQuality);
