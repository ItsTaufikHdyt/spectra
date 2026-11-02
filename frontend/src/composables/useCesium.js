import { shallowRef } from 'vue';
import * as Cesium from 'cesium';

// Instance Cesium Viewer disimpan di shallowRef agar tidak terkena deep proxy Vue
export const viewer = shallowRef(null);

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
      baseLayer: false
    });
    // Simpan segera agar destroyViewer() tetap bisa melepasnya bila langkah berikut gagal.
    viewer.value = v;

    // Rendering optimization
    v.resolutionScale = Math.min(window.devicePixelRatio, 1.5);
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

  const flyToBontang = () => {
    if (!viewer.value) return;
    viewer.value.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(117.5169, 0.1415, 1500),
      orientation: {
        heading: Cesium.Math.toRadians(15),
        pitch: Cesium.Math.toRadians(-45),
        roll: 0
      },
      duration: 2.0
    });
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
    destroyViewer,
    flyToBontang
  };
}
