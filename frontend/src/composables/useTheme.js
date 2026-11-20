import * as Cesium from 'cesium';
import { effectScope, watch } from 'vue';
import { requestRender, viewer } from './useCesium';
import { setTheme } from './tilesetStyle';
import { useThemeStore } from '@/stores/themeStore';
import { getMapColors } from '@/utils/mapColors';

/**
 * Efek tema pada peta Cesium: warna dasar globe/latar, dan gaya tileset (lewat penyusun style).
 * Warna garis vektor dan kotak ikhtisar ditangani modul pemiliknya (useVectorLayers, use3DTiles);
 * basemap oleh useLayers. Penerapan ke DOM ada di stores/themeStore.js.
 * Aman dipanggil ulang; `releaseTheme()` melepas watcher (idempoten).
 */
let scope = null;

const applyToViewer = (theme) => {
  const v = viewer.value;
  if (!v || v.isDestroyed()) return;
  const base = Cesium.Color.fromCssColorString(getMapColors(theme).globeBase);
  v.scene.globe.baseColor = base; // terlihat sebelum tile peta dasar tiba (tanpa kilatan biru bawaan)
  v.scene.backgroundColor = base;
  requestRender();
};

export const startTheme = () => {
  if (scope) return;
  const store = useThemeStore();
  // effectScope(true) = detached: tidak ikut berhenti bersama komponen pemanggil.
  scope = effectScope(true);
  scope.run(() => {
    watch(
      () => store.theme,
      (theme) => {
        applyToViewer(theme);
        setTheme(theme);
      },
      { immediate: true }
    );
  });
};

export const releaseTheme = () => {
  scope?.stop();
  scope = null;
};

if (import.meta.hot) import.meta.hot.dispose(releaseTheme);
