import * as Cesium from 'cesium';
import { shallowRef } from 'vue';
import { viewer } from './useCesium';
import { useMapStore } from '@/stores/mapStore';
import { useObjectStore } from '@/stores/objectStore';
import { watch } from 'vue';

// Instance tileset & handler disimpan di tingkat modul agar dibagikan antar
// komponen (CesiumCanvas memuat, LayerControl memanggil zoom). shallowRef
// dipakai agar objek Cesium tidak dibungkus deep proxy Vue.
const tilesetRef = shallowRef(null);
let pickHandler = null;

// State highlight: menyimpan fitur terakhir yang di-highlight beserta warna aslinya
const highlighted = {
  feature: null,
  originalColor: new Cesium.Color()
};

export function use3DTiles() {
  const mapStore = useMapStore();
  const objectStore = useObjectStore();

  /**
   * Memuat 3D Tiles Kelurahan Bontang Kuala.
   * @param {string} url - path absolut ke tileset.json (disajikan dari /public).
   */
  const load3DTiles = async (url = '/tiles/bontang_kuala/tileset.json') => {
    if (!viewer.value) return null;

    try {
      // Pemuatan 3D Tiles v1.1. Pada Cesium >=1.107 fromUrl() me-resolve
      // Promise setelah tileset siap, sehingga tidak perlu readyPromise lagi.
      tilesetRef.value = await Cesium.Cesium3DTileset.fromUrl(url, {
        maximumScreenSpaceError: 16,
        maximumMemoryUsage: 512,
        cullWithChildrenBounds: true,
        skipLevelOfDetail: true
      });

      viewer.value.scene.primitives.add(tilesetRef.value);

      // Sinkronkan visibilitas awal dengan state store.
      tilesetRef.value.show = mapStore.is3DTilesActive;

      // --- Koreksi elevasi vertikal (opsional) ---
      // Jika dasar bangunan "melayang" atau "tenggelam" terhadap terrain/ellipsoid,
      // terapkan offset translasi pada modelMatrix. Default 0 (tanpa koreksi).
      applyHeightOffset(0);

      console.log('[use3DTiles] Tileset Bontang Kuala loaded:', url);
      return tilesetRef.value;
    } catch (err) {
      console.warn('[use3DTiles] Gagal memuat 3D Tiles:', err.message);
      return null;
    }
  };

  /**
   * Menggeser tileset secara vertikal (meter) relatif terhadap pusat boundingSphere.
   * Berguna untuk menyelaraskan dasar bangunan LOD2 dengan permukaan terrain.
   * @param {number} heightMeters
   */
  const applyHeightOffset = (heightMeters = 0) => {
    if (!tilesetRef.value || !heightMeters) return;
    const center = tilesetRef.value.boundingSphere.center;
    const surfaceNormal = Cesium.Cartesian3.normalize(center, new Cesium.Cartesian3());
    const offset = Cesium.Cartesian3.multiplyByScalar(
      surfaceNormal,
      heightMeters,
      new Cesium.Cartesian3()
    );
    tilesetRef.value.modelMatrix = Cesium.Matrix4.fromTranslation(offset);
  };

  /**
   * Arahkan & dekatkan kamera ke tileset Bontang Kuala.
   */
  const zoomToBontangKuala = () => {
    if (!viewer.value || !tilesetRef.value) return;
    viewer.value.zoomTo(
      tilesetRef.value,
      new Cesium.HeadingPitchRange(
        Cesium.Math.toRadians(15),
        Cesium.Math.toRadians(-35),
        // range dibiarkan undefined agar Cesium menghitung jarak otomatis
        // berdasarkan boundingSphere tileset.
        undefined
      )
    );
  };

  /**
   * Bersihkan highlight pada fitur sebelumnya.
   */
  const clearHighlight = () => {
    if (highlighted.feature && Cesium.defined(highlighted.feature.color)) {
      highlighted.feature.color = highlighted.originalColor;
    }
    highlighted.feature = null;
  };

  /**
   * Pasang handler klik kiri untuk feature picking + highlight.
   */
  const setupTilePicking = () => {
    if (!viewer.value) return;

    pickHandler = new Cesium.ScreenSpaceEventHandler(viewer.value.scene.canvas);

    pickHandler.setInputAction((movement) => {
      // Reset highlight fitur sebelumnya.
      clearHighlight();

      const picked = viewer.value.scene.pick(movement.position);

      if (!Cesium.defined(picked) || !(picked instanceof Cesium.Cesium3DTileFeature)) {
        // Klik di area kosong -> bersihkan panel atribut.
        objectStore.clearSelection();
        return;
      }

      // Ekstrak seluruh properti dari EXT_structural_metadata.
      const propertyIds = picked.getPropertyIds();
      const allProperties = {};
      propertyIds.forEach((name) => {
        allProperties[name] = picked.getProperty(name);
      });

      objectStore.selectObject({
        identity: {
          id:
            picked.getProperty('id') ||
            picked.getProperty('gml_id') ||
            'BTG-BKL-UNKNOWN',
          name: picked.getProperty('name') || 'Bangunan Bontang Kuala',
          category: 'LOD2 Building'
        },
        source: {
          lod: '2',
          height:
            picked.getProperty('measuredHeight') ||
            picked.getProperty('Height') ||
            '-'
        },
        properties: allProperties
      });

      // Terapkan highlight kuning terang sementara.
      if (Cesium.defined(picked.color)) {
        Cesium.Color.clone(picked.color, highlighted.originalColor);
      }
      highlighted.feature = picked;
      picked.color = Cesium.Color.YELLOW.withAlpha(0.8);
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
  };

  // Watcher toggle visibilitas 3D Tiles.
  watch(
    () => mapStore.is3DTilesActive,
    (isActive) => {
      if (tilesetRef.value) {
        tilesetRef.value.show = isActive;
      }
    }
  );

  return {
    load3DTiles,
    setupTilePicking,
    zoomToBontangKuala,
    applyHeightOffset
  };
}
