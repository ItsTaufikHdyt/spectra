import * as Cesium from 'cesium';
import { effectScope, watch } from 'vue';
import { viewer } from './useCesium';
import { useRemoteLayerStore } from '@/stores/remoteLayerStore';
import { layerDataUrl } from '@/services/geoportalApi';

/**
 * Layer geoportal yang ditambahkan pengguna (terpisah dari useLayers.js / useVectorLayers.js).
 *
 * - mode geojson: GeoJSON hasil normalisasi backend (/api/layers/<id>/data, EPSG:4326 lon/lat)
 *   -> GeoJsonDataSource. Polygon diisi transparan + garis batas sebagai polyline clamp-to-ground
 *   (outline polygon tidak didukung saat di-clamp). Titik digambar sebagai point, bukan pin.
 * - mode wms: WebMapServiceImageryProvider langsung ke geoportal (butuh CORS di GeoServer).
 *
 * Objek Cesium disimpan di Map modul biasa (bukan ref/reactive). Setiap DataSource/ImageryLayer
 * yang tidak lagi ada di store di-remove + destroy.
 */
const PREFIX = 'geoportal:';
const MIN_ZOOM_SPAN_DEG = 0.004; // ~450 m: bbox satu titik tetap bisa di-zoom
const WMS_ERROR =
  'Gambar WMS gagal dimuat dari geoportal. Kemungkinan GeoServer belum mengizinkan CORS untuk domain spectra.';

/** id -> { kind: 'geojson'|'wms', version, obj, mats?, style? } */
const entries = new Map();
let scope = null;
let generation = 0;

const isViewerAlive = () => !!viewer.value && !viewer.value.isDestroyed();

const disposeEntry = (id) => {
  const e = entries.get(id);
  entries.delete(id);
  if (!e?.obj || !isViewerAlive()) return;
  if (e.kind === 'wms') viewer.value.imageryLayers.remove(e.obj, true);
  else viewer.value.dataSources.remove(e.obj, true);
};

const lineColor = (layer) => Cesium.Color.fromCssColorString(layer.warna).withAlpha(Math.min(1, layer.opasitas + 0.3));
const fillColor = (layer) => Cesium.Color.fromCssColorString(layer.warna).withAlpha(layer.opasitas * 0.5);

/** Gaya awal; material dipakai bersama semua entity sehingga ganti warna cukup ubah 3 properti. */
const prepareEntities = (ds, mats) => {
  const now = Cesium.JulianDate.now();
  for (const entity of ds.entities.values) {
    if (entity.polygon) {
      entity.polygon.material = mats.fill;
      entity.polygon.outline = false;
      entity.polygon.classificationType = Cesium.ClassificationType.TERRAIN; // tidak menempel di bangunan 3D
      const ring = entity.polygon.hierarchy?.getValue(now)?.positions ?? [];
      if (ring.length > 2) {
        entity.polyline = new Cesium.PolylineGraphics({
          positions: ring[0].equals(ring[ring.length - 1]) ? ring : [...ring, ring[0]],
          width: 2,
          material: mats.line,
          clampToGround: true,
          classificationType: Cesium.ClassificationType.TERRAIN
        });
      }
    } else if (entity.polyline) {
      entity.polyline.material = mats.line;
      entity.polyline.width = 2.5;
      entity.polyline.classificationType = Cesium.ClassificationType.TERRAIN;
    } else if (entity.billboard) {
      entity.billboard = undefined;
      entity.point = new Cesium.PointGraphics({
        pixelSize: 9,
        color: mats.point,
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: 1.5,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY // tetap terlihat di antara bangunan
      });
    }
  }
};

const applyStyle = (e, layer) => {
  const key = `${layer.warna}|${layer.opasitas}`;
  if (e.style === key) return;
  e.style = key;
  e.mats.fill.color = fillColor(layer);
  e.mats.line.color = lineColor(layer);
  e.mats.point.setValue(lineColor(layer));
};

const loadGeojson = async (layer, gen) => {
  const mats = {
    fill: new Cesium.ColorMaterialProperty(fillColor(layer)),
    line: new Cesium.ColorMaterialProperty(lineColor(layer)),
    point: new Cesium.ConstantProperty(lineColor(layer))
  };
  const ds = await Cesium.GeoJsonDataSource.load(layerDataUrl(layer.id), { clampToGround: true });
  ds.name = `${PREFIX}${layer.id}`;
  prepareEntities(ds, mats);
  if (gen !== generation || !isViewerAlive()) return null;
  await viewer.value.dataSources.add(ds);
  return { ds, mats };
};

const ensureEntry = (layer, store) => {
  const version = `${layer.mode}|${layer.diambil}`;
  let e = entries.get(layer.id);
  if (e && e.version !== version) {
    disposeEntry(layer.id); // refresh / ganti mode -> buat ulang
    e = null;
  }
  if (e) return e;
  if (!layer.aktif) return null; // dimuat saat pertama kali dinyalakan

  if (layer.mode === 'wms') {
    const provider = new Cesium.WebMapServiceImageryProvider({
      url: layer.wms_url,
      layers: layer.typename,
      parameters: { transparent: true, format: 'image/png' }
    });
    let reported = false;
    provider.errorEvent.addEventListener((tileError) => {
      tileError.retry = false;
      if (!reported) {
        reported = true;
        store.setError(layer.id, WMS_ERROR);
      }
    });
    e = { kind: 'wms', version, obj: viewer.value.imageryLayers.addImageryProvider(provider) };
    entries.set(layer.id, e);
    return e;
  }

  e = { kind: 'geojson', version, obj: null };
  entries.set(layer.id, e);
  loadGeojson(layer, generation)
    .then((res) => {
      if (!res) return;
      if (entries.get(layer.id) !== e) {
        // dihapus / di-refresh selama memuat: lepas hasil yang sudah usang
        if (isViewerAlive()) viewer.value.dataSources.remove(res.ds, true);
        return;
      }
      Object.assign(e, { obj: res.ds, mats: res.mats });
      sync(store); // terapkan status terbaru (bisa berubah selama memuat)
    })
    .catch((err) => {
      if (entries.get(layer.id) === e) entries.delete(layer.id);
      console.warn(`[useRemoteLayers] Gagal memuat ${layer.id}:`, err);
      store.setError(layer.id, `Data layer gagal dimuat: ${err?.message ?? err}`);
    });
  return e;
};

/** Samakan isi viewer dengan store.layers. */
function sync(store) {
  if (!isViewerAlive()) return;
  const ids = new Set(store.layers.map((l) => l.id));
  for (const id of [...entries.keys()]) if (!ids.has(id)) disposeEntry(id);

  for (const layer of store.layers) {
    const e = ensureEntry(layer, store);
    if (!e?.obj) continue;
    e.obj.show = layer.aktif;
    if (e.kind === 'wms') e.obj.alpha = layer.opasitas;
    else applyStyle(e, layer);
  }
  // Imagery WMS mengikuti `urutan` (di atas basemap; urutan lebih besar = lebih atas).
  for (const layer of [...store.layers].sort((a, b) => a.urutan - b.urutan)) {
    const e = entries.get(layer.id);
    if (e?.kind === 'wms' && e.obj) viewer.value.imageryLayers.raiseToTop(e.obj);
  }
}

/** Lepas semua resource. Idempoten; panggil sebelum destroyViewer(). */
export const releaseRemoteLayers = () => {
  generation++;
  scope?.stop();
  scope = null;
  for (const id of [...entries.keys()]) disposeEntry(id);
};

if (import.meta.hot) import.meta.hot.dispose(releaseRemoteLayers);

/** Objek pick -> data untuk objectStore, atau null bila bukan fitur layer geoportal. */
export const describeRemotePick = (picked, store) => {
  const entity = picked?.id;
  const ds = entity instanceof Cesium.Entity ? entity.entityCollection?.owner : null;
  if (!ds?.name?.startsWith?.(PREFIX)) return null;
  const layer = store.layers.find((l) => `${PREFIX}${l.id}` === ds.name);
  if (!layer) return null;
  const p = entity.properties?.getValue(Cesium.JulianDate.now()) ?? {};
  const fid = p.fid_sumber ?? entity.id;
  return {
    identity: {
      id: `${layer.id}#${fid}`,
      name: p.nama ?? `Fitur ${fid}`,
      kelurahan: null,
      category: `Data geoportal: ${layer.judul}`
    },
    attributes: p.atribut ?? {},
    tile: null,
    source: { judul: layer.judul, typename: layer.typename, diambil: layer.diambil, fid: String(fid) }
  };
};

export function useRemoteLayers() {
  const store = useRemoteLayerStore();

  /** Muat registry lalu mulai sinkronisasi store -> viewer. Aman dipanggil ulang. */
  const startRemoteLayers = async () => {
    if (scope || !isViewerAlive()) return;
    scope = effectScope(true); // detached: tidak berhenti bersama komponen pemanggil
    scope.run(() => watch(() => store.layers, () => sync(store), { deep: true, immediate: true }));
    await store.load();
  };

  const zoomToLayer = (layer) => {
    if (!isViewerAlive() || !layer?.bbox) return;
    let [w, s, e, n] = layer.bbox;
    const padLon = Math.max(0, (MIN_ZOOM_SPAN_DEG - (e - w)) / 2);
    const padLat = Math.max(0, (MIN_ZOOM_SPAN_DEG - (n - s)) / 2);
    [w, s, e, n] = [w - padLon, s - padLat, e + padLon, n + padLat];
    viewer.value.camera.flyTo({ destination: Cesium.Rectangle.fromDegrees(w, s, e, n), duration: 1.2 });
  };

  // Hanya mode dev: penghitung resource untuk uji kebocoran (DataSource/ImageryLayer tertinggal).
  if (import.meta.env.DEV) {
    window.__spectraRemoteDebug = () => {
      if (!isViewerAlive()) return null;
      const v = viewer.value;
      const names = Array.from({ length: v.dataSources.length }, (_, i) => v.dataSources.get(i).name);
      return {
        dataSources: v.dataSources.length,
        geoportalDataSources: names.filter((n) => n?.startsWith(PREFIX)).length,
        imageryLayers: v.imageryLayers.length,
        entries: entries.size
      };
    };
  }

  return { startRemoteLayers, releaseRemoteLayers, zoomToLayer };
}
