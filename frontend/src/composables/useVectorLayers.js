import * as Cesium from 'cesium';
import { effectScope, shallowRef, watch } from 'vue';
import { viewer } from './useCesium';
import { useMapStore } from '@/stores/mapStore';
import { MAP_COLORS } from '@/utils/mapColors';

/**
 * Layer vektor batas kelurahan, batas RT, dan sungai.
 *
 * Sumber: GeoJSON hasil ETL (data-pipeline/processed/geojson/, sudah WGS84) yang disalin ke
 * frontend/public/geojson/ oleh data-pipeline/scripts/sync_geojson.py.
 * shortcut: GeoJSON dimuat utuh di browser (±2,9 MB total). Ganti ke GeoServer WMS/WFS atau
 * vector tiles bila data membesar / backend tersedia (AGENTS.md §3.2, PRD Milestone 4).
 *
 * Semua garis (termasuk batas polygon) digambar sebagai polyline clamp-to-ground:
 * outline polygon Cesium tidak didukung saat di-clamp dan lebarnya terbatas 1 px.
 * classificationType TERRAIN -> garis tidak "menempel" di dinding/atap bangunan 3D.
 */
export const VECTOR_LAYERS = Object.freeze([
  { key: 'kelurahan', flag: 'isKelurahanActive', label: 'batas kelurahan', url: '/geojson/batas-kelurahan.norm.geojson' },
  { key: 'rt', flag: 'isRtActive', label: 'batas RT', url: '/geojson/batas-rt.norm.geojson' },
  { key: 'sungai', flag: 'isSungaiActive', label: 'sungai', url: '/geojson/sungai_ln.wgs84.geojson' }
]);

/** Fitur bernama "Drainase …" digambar beda (kategori belum diputuskan; data tidak diubah). */
export const isDrainase = (props) => String(props?.nama ?? '').startsWith('Drainase');

const STYLE = {
  kelurahan: () => ({ color: MAP_COLORS.kelurahan, width: 2.5 }),
  rt: () => ({ color: MAP_COLORS.rt, width: 1.25 }),
  sungai: (props) =>
    isDrainase(props) ? { color: MAP_COLORS.drainase, width: 2 } : { color: MAP_COLORS.sungai, width: 3 }
};

// ---------------------------------------------------------------------------
// State tingkat modul. Objek Cesium di Map biasa (BUKAN ref/reactive).
// ---------------------------------------------------------------------------
const sources = new Map(); // key -> CustomDataSource
const loading = new Map(); // key -> Promise
/** { [key]: pesan error } — hanya teks, aman di shallowRef. */
const layerErrors = shallowRef({});
let scope = null; // effectScope terpisah dari siklus hidup komponen
let generation = 0; // membatalkan pemuatan yang masih berjalan saat release

const isViewerAlive = () => !!viewer.value && !viewer.value.isDestroyed();

const setError = (key, message) => {
  const next = { ...layerErrors.value };
  if (message) next[key] = message;
  else delete next[key];
  layerErrors.value = next;
};

/** Daftar garis [[lon, lat], ...] dari geometri GeoJSON (ring polygon = garis batas). */
const linesOf = (geometry) => {
  switch (geometry?.type) {
    case 'LineString':
      return [geometry.coordinates];
    case 'MultiLineString':
    case 'Polygon':
      return geometry.coordinates;
    case 'MultiPolygon':
      return geometry.coordinates.flat();
    default:
      return [];
  }
};

const buildSource = (key, geojson) => {
  const source = new Cesium.CustomDataSource(`vektor-${key}`);
  const materials = new Map(); // satu material per warna -> batch ground polyline lebih sedikit
  const material = (css) => {
    if (!materials.has(css)) {
      materials.set(css, new Cesium.ColorMaterialProperty(Cesium.Color.fromCssColorString(css)));
    }
    return materials.get(css);
  };

  for (const feature of geojson?.features ?? []) {
    const { color, width } = STYLE[key](feature.properties);
    for (const line of linesOf(feature.geometry)) {
      if (!Array.isArray(line) || line.length < 2) continue;
      source.entities.add({
        polyline: {
          positions: Cesium.Cartesian3.fromDegreesArray(line.flatMap(([lon, lat]) => [lon, lat])),
          width,
          material: material(color),
          clampToGround: true,
          classificationType: Cesium.ClassificationType.TERRAIN
        },
        properties: feature.properties ?? {}
      });
    }
  }
  return source;
};

/** Muat satu layer sekali (lazy); pemanggilan berikutnya memakai hasil yang sama. */
const ensureLayer = (layer) => {
  if (sources.has(layer.key)) return Promise.resolve(sources.get(layer.key));
  if (loading.has(layer.key)) return loading.get(layer.key);

  const gen = generation;
  const v = viewer.value;
  const promise = (async () => {
    try {
      const geojson = await Cesium.Resource.fetchJson({ url: layer.url });
      if (gen !== generation || !v || v.isDestroyed()) return null;
      const source = buildSource(layer.key, geojson);
      await v.dataSources.add(source);
      if (gen !== generation) {
        // release dipanggil selama add: source belum tercatat, lepas di sini.
        if (!v.isDestroyed()) v.dataSources.remove(source, true);
        return null;
      }
      sources.set(layer.key, source);
      setError(layer.key, null);
      return source;
    } catch (err) {
      if (gen !== generation) return null;
      console.warn(`[useVectorLayers] Gagal memuat ${layer.label}:`, err);
      // Dev server mengembalikan index.html untuk path tak dikenal -> JSON gagal di-parse.
      setError(layer.key, `File ${layer.url} tidak terbaca. Jalankan data-pipeline/scripts/sync_geojson.py.`);
      return null;
    } finally {
      if (loading.get(layer.key) === promise) loading.delete(layer.key);
    }
  })();
  loading.set(layer.key, promise);
  return promise;
};

const applyVisibility = async (layer, visible, store) => {
  if (!visible) {
    const source = sources.get(layer.key);
    if (source) source.show = false;
    return;
  }
  const source = await ensureLayer(layer);
  // Toggle bisa saja dimatikan lagi selama pemuatan.
  if (source) source.show = !!store[layer.flag];
};

/**
 * Lepas SEMUA resource modul. Idempoten. Panggil sebelum unload3DTiles()/destroyViewer().
 */
export const releaseVectorLayers = () => {
  generation++;
  scope?.stop();
  scope = null;
  for (const source of sources.values()) {
    if (isViewerAlive()) viewer.value.dataSources.remove(source, true);
    else source.entities.removeAll();
  }
  sources.clear();
  loading.clear();
  layerErrors.value = {};
};

if (import.meta.hot) {
  import.meta.hot.dispose(releaseVectorLayers);
}

export function useVectorLayers() {
  const mapStore = useMapStore();

  /** Mulai sinkronisasi toggle -> layer. Aman dipanggil ulang. */
  const startVectorLayers = () => {
    if (scope || !isViewerAlive()) return;
    // effectScope(true) = detached: watcher tidak ikut berhenti bersama komponen pemanggil.
    scope = effectScope(true);
    scope.run(() => {
      for (const layer of VECTOR_LAYERS) {
        watch(
          () => mapStore[layer.flag],
          (visible) => applyVisibility(layer, visible, mapStore),
          { immediate: true }
        );
      }
    });
  };

  return { layerErrors, startVectorLayers, releaseVectorLayers };
}
