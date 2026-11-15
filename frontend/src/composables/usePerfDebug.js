import * as Cesium from 'cesium';
import { viewer } from './useCesium';

/**
 * Mode debug performa: hanya aktif lewat query string, mis. `/?debug=perf` atau
 * `/?debug=perf,inspector`. Tanpa query ini tidak ada listener atau overlay yang dipasang.
 *
 *  - perf      : overlay FPS Cesium + `window.__spectraPerf()` (dipakai skrip pengukuran).
 *  - inspector : panel Cesium3DTilesInspector (butuh tileset; ditambahkan setelah dimuat).
 *
 * `__spectraPerf()` mengembalikan data biasa (bukan objek Cesium): jumlah frame yang
 * benar-benar dirender sejak halaman dibuka (postRender hanya terpicu bila frame dirender,
 * jadi dengan requestRenderMode angkanya berhenti naik saat peta diam), statistik tileset,
 * dan daftar pengaturan viewer/scene/globe/tileset yang aktif.
 */
const params = new URLSearchParams(window.location.search);
const modes = new Set((params.get('debug') ?? '').split(',').map((s) => s.trim()).filter(Boolean));
export const isPerfDebug = modes.has('perf');

let frames = 0;
let removePostRender = null;

const isAlive = () => !!viewer.value && !viewer.value.isDestroyed();

const snapshot = (tileset) => {
  const v = viewer.value;
  const scene = v.scene;
  const gl = scene.context._gl;
  const info = gl.getExtension('WEBGL_debug_renderer_info');
  const s = tileset?.statistics;
  return {
    frames,
    renderer: info ? gl.getParameter(info.UNMASKED_RENDERER_WEBGL) : 'tidak diketahui',
    tileset: tileset
      ? {
          memoriBytes: tileset.totalMemoryUsageInBytes,
          tileSiapKonten: s.numberOfTilesWithContentReady,
          tileDimuatTotal: s.numberOfLoadedTilesTotal,
          tileTerpilih: s.selected,
          tileDikunjungi: s.visited,
          segitigaTerpilih: s.numberOfTrianglesSelected,
          permintaanTertunda: s.numberOfPendingRequests,
          geometriBytes: s.geometryByteLength,
          teksturBytes: s.texturesByteLength,
          tileLengkap: tileset.tilesLoaded
        }
      : null,
    pengaturan: {
      viewer: {
        resolutionScale: v.resolutionScale,
        useBrowserRecommendedResolution: v.useBrowserRecommendedResolution,
        targetFrameRate: v.targetFrameRate,
        ukuranCanvas: [v.canvas.width, v.canvas.height],
        devicePixelRatio: window.devicePixelRatio
      },
      scene: {
        requestRenderMode: scene.requestRenderMode,
        maximumRenderTimeChange: scene.maximumRenderTimeChange,
        msaaSamples: scene.msaaSamples,
        fxaa: scene.postProcessStages.fxaa.enabled,
        shadows: v.shadows,
        fog: scene.fog.enabled,
        skyAtmosphere: !!scene.skyAtmosphere?.show,
        skyBox: !!scene.skyBox?.show,
        sun: !!scene.sun?.show,
        moon: !!scene.moon?.show,
        highDynamicRange: scene.highDynamicRange,
        depthTestAgainstTerrain: scene.globe.depthTestAgainstTerrain
      },
      globe: {
        enableLighting: scene.globe.enableLighting,
        showGroundAtmosphere: scene.globe.showGroundAtmosphere,
        tileCacheSize: scene.globe.tileCacheSize,
        maximumScreenSpaceError: scene.globe.maximumScreenSpaceError,
        preloadSiblings: scene.globe.preloadSiblings
      },
      tileset: tileset
        ? {
            maximumScreenSpaceError: tileset.maximumScreenSpaceError,
            cacheBytes: tileset.cacheBytes,
            maximumCacheOverflowBytes: tileset.maximumCacheOverflowBytes,
            dynamicScreenSpaceError: tileset.dynamicScreenSpaceError,
            foveatedScreenSpaceError: tileset.foveatedScreenSpaceError,
            skipLevelOfDetail: tileset.skipLevelOfDetail,
            preloadWhenHidden: tileset.preloadWhenHidden,
            preloadFlightDestinations: tileset.preloadFlightDestinations,
            preferLeaves: tileset.preferLeaves
          }
        : null
    }
  };
};

/** Pasang mode debug (aman dipanggil ulang). Panggil setelah tileset dimuat (boleh null). */
export const setupPerfDebug = (tileset) => {
  if (!isPerfDebug || !isAlive()) return;
  const v = viewer.value;
  v.scene.debugShowFramesPerSecond = true;
  removePostRender?.();
  frames = 0;
  removePostRender = v.scene.postRender.addEventListener(() => {
    frames++;
  });
  window.__spectraPerf = () => (isAlive() ? snapshot(tileset) : null);
  // Hanya mode debug: akses langsung untuk eksperimen di konsol (jangan dipakai kode aplikasi).
  window.__spectra = { viewer: v, tileset };
  if (modes.has('inspector') && tileset && !v.cesium3DTilesInspector) {
    v.extend(Cesium.viewerCesium3DTilesInspectorMixin);
    v.cesium3DTilesInspector.viewModel.tileset = tileset;
  }
};

/** Lepas listener; panggil di teardown sebelum viewer dihancurkan. */
export const releasePerfDebug = () => {
  removePostRender?.();
  removePostRender = null;
  if (window.__spectraPerf) delete window.__spectraPerf;
  if (window.__spectra) delete window.__spectra;
};
