import { shallowRef } from 'vue';
import * as Cesium from 'cesium';

// Instance Cesium Viewer disimpan di shallowRef agar tidak terkena deep proxy Vue
export const viewer = shallowRef(null);

/**
 * Minta satu frame baru. Dengan requestRenderMode, Cesium hanya merender saat kamera bergerak,
 * tile/imagery dimuat, atau ukuran canvas berubah. Panggil helper ini SETELAH setiap perubahan
 * lain yang terlihat di peta: show/alpha/warna, entity & data source, highlight, imagery layer,
 * layer simulasi. Aman dipanggil kapan saja (viewer belum ada / sudah dihancurkan = tidak apa-apa).
 */
export const requestRender = () => {
  const v = viewer.value;
  if (v && !v.isDestroyed()) v.scene.requestRender();
};

export function useCesium() {
  /** @param {string|HTMLElement} container id atau elemen DOM wadah viewer */
  const initViewer = async (container) => {
    // Pusat Kelurahan Bontang Kuala
    const defaultLng = 117.5169;
    const defaultLat = 0.1415;
    const defaultAlt = 1500;

    const v = new Cesium.Viewer(container, {
      animation: false,
      timeline: false,
      navigationHelpButton: false,
      sceneModePicker: false,
      homeButton: false,
      geocoder: false,
      baseLayerPicker: false,
      fullscreenButton: false,
      infoBox: false,
      selectionIndicator: false,
      baseLayer: false,
      // Render hanya saat ada perubahan (peta diam = GPU idle). Perubahan yang tidak memicu
      // render otomatis WAJIB memanggil requestRender() di bawah. Tanpa jam dinamis di
      // aplikasi ini, jadi perubahan waktu tidak perlu memicu render (Infinity).
      requestRenderMode: true,
      maximumRenderTimeChange: Number.POSITIVE_INFINITY,
      // Render pada resolusi CSS; ketajaman diatur lewat resolutionScale (useRenderQuality.js).
      useBrowserRecommendedResolution: true,
      shadows: false
    });
    // Simpan segera agar destroyViewer() tetap bisa melepasnya bila langkah berikut gagal.
    viewer.value = v;

    // Resolusi, anti-aliasing, dan efek visual diatur per "Mode tampilan" (useRenderQuality.js).
    v.scene.globe.depthTestAgainstTerrain = true;
    v.scene.globe.enableLighting = false;

    // Set Initial Camera
    v.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(defaultLng, defaultLat, defaultAlt),
      orientation: {
        heading: Cesium.Math.toRadians(0),
        pitch: Cesium.Math.toRadians(-45),
        roll: 0.0
      }
    });

    return v;
  };

  /**
   * Hancurkan viewer (melepas WebGL context, handler, dan seluruh primitive).
   * Panggil SETELAH resource turunan (mis. unload3DTiles) dilepas.
   */
  const destroyViewer = () => {
    const v = viewer.value;
    viewer.value = null;
    if (v && !v.isDestroyed()) v.destroy();
  };

  return {
    viewer,
    initViewer,
    destroyViewer
  };
}
