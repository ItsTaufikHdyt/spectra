import * as Cesium from 'cesium';
import { effectScope, shallowRef, watch } from 'vue';
import { viewer } from './useCesium';
import { useMapStore } from '@/stores/mapStore';
import { useObjectStore } from '@/stores/objectStore';
import { parseContentUrl, pickFirst, slugToName } from '@/utils/tileMeta';
import { MAP_COLORS } from '@/utils/mapColors';

/** Master tileset 15 kelurahan (dibuat oleh data-pipeline/scripts/04_build_master.py). */
export const MASTER_TILESET_URL = '/tiles/master-tileset.json';

const MB = 1024 * 1024;

/**
 * Parameter performa Cesium 1.146.
 *  - cacheBytes 512 MB, cullWithChildrenBounds, cullRequestsWhileMoving, foveatedScreenSpaceError
 *    SUDAH default di 1.146; ditulis eksplisit agar tidak berubah diam-diam saat upgrade.
 *  - Yang benar-benar mengubah perilaku: maximumScreenSpaceError 24 (default 16),
 *    skipLevelOfDetail true (default false), maximumCacheOverflowBytes 256 MB (default 512 MB).
 *  - dynamicScreenSpaceError dibiarkan default (true): ikut menurunkan detail tile jauh/horizon.
 */
export const TILESET_OPTIONS = Object.freeze({
  maximumScreenSpaceError: 24,
  cacheBytes: 512 * MB,
  maximumCacheOverflowBytes: 256 * MB,
  cullWithChildrenBounds: true,
  cullRequestsWhileMoving: true,
  foveatedScreenSpaceError: true,
  skipLevelOfDetail: true
});

// Ikhtisar kelurahan (LOD kasar sisi klien) — lihat buildKelurahanOverview().
const OVERVIEW_ID_PREFIX = 'ikhtisar-kelurahan:';
const OVERVIEW_COLOR = Cesium.Color.fromCssColorString(MAP_COLORS.overview);
const SELECTION_COLOR = Cesium.Color.fromCssColorString(MAP_COLORS.selection);
// Nominal tinggi layar untuk memperkirakan jarak hilangnya bangunan (piksel).
const NOMINAL_SCREEN_HEIGHT = 1080;

// Kandidat nama properti metadata (jika suatu saat tile membawa EXT_structural_metadata).
// Kandidat nama/tinggi ada di services/buildingAttributes.js (ATTRIBUTE_KEYS).
const ID_KEYS = ['id', 'gml_id', 'gmlId', 'identifier', 'objectid'];

// ---------------------------------------------------------------------------
// State tingkat modul — instance tunggal yang dipakai bersama antar komponen.
// Objek Cesium disimpan di shallowRef / variabel biasa (BUKAN ref/reactive).
// ---------------------------------------------------------------------------
const tilesetRef = shallowRef(null);
/** [{ slug, name, region: [w,s,e,n,minH,maxH] (radian) }] — dari master-tileset.json. */
const kelurahanList = shallowRef([]);
const loadError = shallowRef(null);

let pickHandler = null; // ScreenSpaceEventHandler — WAJIB di-destroy
let selectionMarker = null; // entity penanda titik klik
let overviewSource = null; // CustomDataSource ikhtisar kelurahan (bukan ref)
let removeTileFailedListener = null;
let visibilityScope = null; // effectScope terpisah dari siklus hidup komponen
let loadingPromise = null;
let loadGeneration = 0; // membatalkan load yang masih berjalan saat release

// Highlight untuk jalur picking per-feature (hanya bila tile punya property table).
const highlighted = { feature: null, originalColor: new Cesium.Color() };

// ---------------------------------------------------------------------------
// Utilitas modul (tanpa ketergantungan pada store)
// ---------------------------------------------------------------------------
const isViewerAlive = () => !!viewer.value && !viewer.value.isDestroyed();

const clearFeatureHighlight = () => {
  const { feature, originalColor } = highlighted;
  highlighted.feature = null;
  if (!feature) return;
  try {
    feature.color = originalColor;
  } catch {
    // Tile sudah di-unload dari cache; tidak ada yang perlu dipulihkan.
  }
};

const clearSelectionMarker = () => {
  if (selectionMarker && isViewerAlive()) {
    viewer.value.entities.remove(selectionMarker);
  }
  selectionMarker = null;
};

const clearSelectionVisuals = () => {
  clearFeatureHighlight();
  clearSelectionMarker();
};

const showSelectionMarker = (cartesian) => {
  if (!cartesian || !isViewerAlive()) return;
  if (selectionMarker) {
    selectionMarker.position = cartesian;
    return;
  }
  selectionMarker = viewer.value.entities.add({
    position: cartesian,
    point: {
      pixelSize: 12,
      color: SELECTION_COLOR,
      outlineColor: Cesium.Color.fromCssColorString('#0D1820'),
      outlineWidth: 2,
      disableDepthTestDistance: Number.POSITIVE_INFINITY
    }
  });
};

/** Posisi dunia titik klik: pickPosition (depth buffer) -> fallback ke elipsoid. */
const getClickPosition = (scene, windowPosition) => {
  try {
    if (scene.pickPositionSupported) {
      const p = scene.pickPosition(windowPosition);
      if (Cesium.defined(p)) return p;
    }
  } catch {
    // Lanjut ke fallback.
  }
  return scene.camera.pickEllipsoid(windowPosition, scene.globe.ellipsoid) ?? null;
};

/** Baca seluruh properti feature secara dinamis; aman bila tidak ada property table. */
const readFeatureProperties = (feature) => {
  const props = {};
  try {
    for (const name of feature.getPropertyIds()) {
      props[name] = feature.getProperty(name);
    }
  } catch {
    // Konten tanpa batch/property table.
  }
  return props;
};

/**
 * Normalisasi hasil scene.pick() menjadi { content, feature } atau null.
 *  - Jalur 1: Cesium3DTileFeature (tile PUNYA property table).
 *  - Jalur 2: objek pick konten glTF { content, primitive: tileset } (tile TANPA property table —
 *    kondisi data saat ini: .glb hanya berisi EXT_mesh_features, tanpa EXT_structural_metadata).
 */
const resolvePick = (picked) => {
  if (!Cesium.defined(picked)) return null;
  if (picked instanceof Cesium.Cesium3DTileFeature) {
    return { content: picked.content, feature: picked };
  }
  if (picked.content && picked.primitive === tilesetRef.value) {
    return { content: picked.content, feature: null };
  }
  return null;
};

/** Baca anak-anak master-tileset.json -> daftar kelurahan + region (radian). */
const fetchKelurahanIndex = async (url) => {
  const master = await Cesium.Resource.fetchJson({ url });
  return (master.root?.children ?? [])
    .map((child) => {
      const slug = (child.content?.uri ?? '').split('/')[0];
      const region = child.boundingVolume?.region;
      return slug && region?.length === 6
        ? { slug, name: slugToName(slug), region, geometricError: child.geometricError ?? 0 }
        : null;
    })
    .filter(Boolean);
};

/**
 * Jarak kamera (m) di mana root kelurahan mulai ditelusuri Cesium, yaitu saat
 * SSE root = geometricError * tinggiLayar / (jarak * 2 * tan(fovy/2)) melampaui batas.
 * Perkiraan nominal (layar 1080 px); dynamicScreenSpaceError bisa menggesernya.
 */
/** fovy kamera; fallback 60° bila frustum belum valid (kanvas belum berukuran -> NaN). */
const cameraFovy = (v) => {
  const f = v?.camera?.frustum?.fovy;
  return Number.isFinite(f) && f > 0 ? f : Cesium.Math.toRadians(60);
};

const buildingsVisibleWithin = (geometricError, fovy) =>
  (geometricError * NOMINAL_SCREEN_HEIGHT) /
  (TILESET_OPTIONS.maximumScreenSpaceError * 2 * Math.tan(fovy / 2));

/**
 * LOD kasar sisi klien: kotak region tiap kelurahan + label, hanya tampil saat kamera
 * cukup jauh sehingga bangunan belum dirender (root kelurahan tanpa konten).
 * Sumbernya region di master-tileset.json (hasil ETL), bukan GeoJSON/CityJSON mentah.
 *
 * shortcut: kotak bounding region, bukan footprint nyata; ganti bila ETL sudah
 * membuat konten root kasar (lihat TODO(ETL) di data-pipeline/scripts/04_build_master.py).
 */
const buildKelurahanOverview = (v, list) => {
  const source = new Cesium.CustomDataSource('ikhtisar-kelurahan');
  const fovy = cameraFovy(v);

  for (const k of list) {
    // geometricError 0 = root sudah berkonten (mis. bontang_lestari): bangunan selalu tampil.
    if (!(k.geometricError > 0)) continue;
    // Muncul sedikit sebelum bangunan hilang (faktor 0,8) agar tidak ada jeda kosong.
    const near = buildingsVisibleWithin(k.geometricError, fovy) * 0.8;
    const showFar = new Cesium.DistanceDisplayCondition(near, Number.POSITIVE_INFINITY);
    const [w, s, e, n] = k.region;
    const rect = Cesium.Rectangle.fromRadians(w, s, e, n);

    source.entities.add({
      id: `${OVERVIEW_ID_PREFIX}${k.slug}`,
      name: k.name,
      rectangle: {
        coordinates: rect,
        height: 0, // tinggi eksplisit: outline tidak didukung pada geometri clamp-to-ground
        material: OVERVIEW_COLOR.withAlpha(0.05),
        outline: true,
        outlineColor: OVERVIEW_COLOR.withAlpha(0.85),
        distanceDisplayCondition: showFar
      },
      position: Cesium.Cartesian3.fromRadians((w + e) / 2, (s + n) / 2, 0),
      label: {
        text: k.name,
        font: '600 13px "Public Sans", system-ui, sans-serif',
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.fromCssColorString('#0D1820'),
        outlineWidth: 3,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
        distanceDisplayCondition: showFar
      }
    });
  }
  return source;
};

/** Slug kelurahan bila objek pick adalah entity ikhtisar; selain itu null. */
const overviewSlugOf = (picked) => {
  const id = picked?.id?.id;
  return typeof id === 'string' && id.startsWith(OVERVIEW_ID_PREFIX)
    ? id.slice(OVERVIEW_ID_PREFIX.length)
    : null;
};

const round = (n, digits) => Number(n.toFixed(digits));

const teardownTilePicking = () => {
  if (pickHandler && !pickHandler.isDestroyed()) pickHandler.destroy();
  pickHandler = null;
};

/**
 * Lepas SELURUH resource modul: handler picking, marker, watcher, listener, dan tileset.
 * Idempoten. Dipakai oleh unload3DTiles() dan HMR dispose.
 */
const releaseResources = () => {
  loadGeneration++; // batalkan load yang sedang berjalan
  teardownTilePicking();
  clearSelectionVisuals();

  visibilityScope?.stop();
  visibilityScope = null;

  removeTileFailedListener?.();
  removeTileFailedListener = null;

  if (overviewSource && isViewerAlive()) viewer.value.dataSources.remove(overviewSource, true);
  overviewSource = null;

  const tileset = tilesetRef.value;
  tilesetRef.value = null;
  kelurahanList.value = [];

  if (tileset && !tileset.isDestroyed()) {
    // primitives.remove() ikut men-destroy tileset (destroyPrimitives default true).
    if (isViewerAlive()) viewer.value.scene.primitives.remove(tileset);
    if (!tileset.isDestroyed()) tileset.destroy();
  }
};

// Hot reload (dev): bersihkan resource modul lama agar handler/tileset tidak bocor.
if (import.meta.hot) {
  import.meta.hot.dispose(releaseResources);
}

// ---------------------------------------------------------------------------
// Composable
// ---------------------------------------------------------------------------
export function use3DTiles() {
  const mapStore = useMapStore();
  const objectStore = useObjectStore();

  const startVisibilitySync = () => {
    if (visibilityScope) return;
    // effectScope(true) = detached, sehingga watcher TIDAK ikut berhenti saat komponen
    // pemanggil (mis. LayerControl) di-unmount.
    visibilityScope = effectScope(true);
    visibilityScope.run(() => {
      watch(
        () => mapStore.is3DTilesActive,
        (isActive) => {
          if (tilesetRef.value && !tilesetRef.value.isDestroyed()) {
            tilesetRef.value.show = isActive; // show=false menghentikan traversal & request tile
          }
          if (overviewSource) overviewSource.show = isActive;
          if (!isActive) {
            clearSelectionVisuals();
            objectStore.clearSelection();
          }
        }
      );
    });
  };

  /**
   * Muat master-tileset.json. Idempoten dan aman terhadap unmount di tengah pemuatan.
   * @returns {Promise<Cesium.Cesium3DTileset|null>}
   */
  const load3DTiles = async (url = MASTER_TILESET_URL) => {
    if (!isViewerAlive()) return null;
    if (tilesetRef.value) return tilesetRef.value;
    if (loadingPromise) return loadingPromise;

    const generation = ++loadGeneration;
    const v = viewer.value;
    loadError.value = null;

    loadingPromise = (async () => {
      try {
        const tileset = await Cesium.Cesium3DTileset.fromUrl(url, { ...TILESET_OPTIONS });

        // Dibatalkan (release dipanggil) atau viewer sudah dihancurkan selama await.
        if (generation !== loadGeneration || v.isDestroyed()) {
          tileset.destroy();
          return null;
        }

        removeTileFailedListener = tileset.tileFailed.addEventListener((e) => {
          console.warn('[use3DTiles] Tile gagal dimuat:', e.url, e.message);
        });

        v.scene.primitives.add(tileset);
        tileset.show = mapStore.is3DTilesActive;
        tilesetRef.value = tileset;
        startVisibilitySync();

        // Daftar kelurahan untuk navigasi; kegagalan di sini tidak boleh menggagalkan tileset.
        const list = await fetchKelurahanIndex(url).catch((err) => {
          console.warn('[use3DTiles] Gagal membaca daftar kelurahan:', err.message);
          return [];
        });
        if (generation !== loadGeneration) return null; // dibatalkan saat fetch indeks
        kelurahanList.value = list;

        overviewSource = buildKelurahanOverview(v, list);
        overviewSource.show = mapStore.is3DTilesActive;
        await v.dataSources.add(overviewSource);
        if (generation !== loadGeneration) return null; // release sudah melepas overviewSource

        console.log(`[use3DTiles] Master tileset dimuat (${list.length} kelurahan)`);
        return tileset;
      } catch (err) {
        loadError.value = err.message;
        console.warn('[use3DTiles] Gagal memuat master tileset:', err.message);
        return null;
      } finally {
        loadingPromise = null;
      }
    })();

    return loadingPromise;
  };

  // -------------------------------------------------------------------------
  // Picking — hanya LEFT_CLICK (tanpa MOUSE_MOVE/hover), satu handler pada satu waktu.
  // -------------------------------------------------------------------------
  const handleLeftClick = (movement) => {
    if (!isViewerAlive()) return;
    const scene = viewer.value.scene;

    clearSelectionVisuals();

    const picked = scene.pick(movement.position);

    // Klik kotak ikhtisar kelurahan (kamera jauh) -> terbang ke kelurahan tersebut.
    const overviewSlug = overviewSlugOf(picked);
    if (overviewSlug) {
      objectStore.clearSelection();
      flyToKelurahan(overviewSlug);
      return;
    }

    const hit = resolvePick(picked);
    if (!hit) {
      objectStore.clearSelection();
      return;
    }

    const { content, feature } = hit;
    const { slug, tile } = parseContentUrl(content?.url);
    const kelurahan = slugToName(slug) || 'Tidak diketahui';
    const metadata = feature ? readFeatureProperties(feature) : {};
    const featureId = feature?.featureId;

    const cartesian = getClickPosition(scene, movement.position);
    let location = null;
    if (cartesian) {
      const c = Cesium.Cartographic.fromCartesian(cartesian);
      location = {
        longitude: round(Cesium.Math.toDegrees(c.longitude), 6),
        latitude: round(Cesium.Math.toDegrees(c.latitude), 6),
        elevation: round(c.height, 2) // tinggi elipsoid titik klik, bukan FFL
      };
    }

    const baseId = slug ? `${slug}/${tile}` : tile || 'BTG-UNKNOWN';
    const id =
      pickFirst(metadata, ID_KEYS) ?? (featureId !== undefined ? `${baseId}#${featureId}` : baseId);

    // Nama/tinggi final diturunkan di panel dari atribut (tile atau backend); ini nama cadangan.
    objectStore.selectObject({
      identity: {
        id: String(id),
        name: featureId !== undefined ? `Bangunan #${featureId}` : 'Bangunan',
        kelurahan,
        category: 'Bangunan LOD2'
      },
      attributes: metadata,
      location,
      tile: { path: tile, featureId }
    });

    if (feature) {
      // Highlight warna aksen pada fitur terpilih (jalur property table).
      if (Cesium.defined(feature.color)) Cesium.Color.clone(feature.color, highlighted.originalColor);
      highlighted.feature = feature;
      feature.color = SELECTION_COLOR.withAlpha(0.85);
    } else {
      // Tanpa feature table, bangunan tidak bisa di-highlight per objek -> beri penanda titik.
      showSelectionMarker(cartesian);
    }
  };

  /** Pasang handler klik. Aman dipanggil ulang: handler lama di-destroy lebih dulu. */
  const setupTilePicking = () => {
    if (!isViewerAlive()) return;
    teardownTilePicking();
    pickHandler = new Cesium.ScreenSpaceEventHandler(viewer.value.scene.canvas);
    pickHandler.setInputAction(handleLeftClick, Cesium.ScreenSpaceEventType.LEFT_CLICK);
  };

  // -------------------------------------------------------------------------
  // Navigasi kamera
  // -------------------------------------------------------------------------
  const flyToSphere = (sphere, { heading = 15, pitch = -35, duration = 2, range = 0 } = {}) => {
    if (!isViewerAlive()) return;
    // range = 0 -> Cesium menghitung jarak otomatis agar seluruh sphere terlihat.
    viewer.value.camera.flyToBoundingSphere(sphere, {
      duration,
      offset: new Cesium.HeadingPitchRange(
        Cesium.Math.toRadians(heading),
        Cesium.Math.toRadians(pitch),
        range
      )
    });
  };

  /** Arahkan kamera agar seluruh kota Bontang (union 15 kelurahan) terlihat. */
  const zoomToKota = (options) => {
    const tileset = tilesetRef.value;
    if (!tileset || tileset.isDestroyed()) return;
    flyToSphere(tileset.boundingSphere, options);
  };

  /** Arahkan kamera ke satu kelurahan berdasarkan slug (mis. 'bontang_kuala'). */
  const flyToKelurahan = (slug, options) => {
    const item = kelurahanList.value.find((k) => k.slug === slug);
    if (!item) {
      console.warn('[use3DTiles] Kelurahan tidak dikenal:', slug);
      return;
    }
    const [w, s, e, n, minH, maxH] = item.region;
    const sphere = Cesium.BoundingSphere.fromRectangle3D(
      Cesium.Rectangle.fromRadians(w, s, e, n),
      Cesium.Ellipsoid.WGS84,
      (minH + maxH) / 2
    );
    // Jarak "muat seluruh kelurahan" sering melebihi ambang render bangunan (root tanpa
    // konten), sehingga yang tampil hanya kotak ikhtisar. Batasi agar bangunan ikut dimuat.
    let range = 0;
    if (item.geometricError > 0) {
      const fovy = cameraFovy(viewer.value);
      const fitRange = sphere.radius / Math.sin(fovy / 2);
      range = Math.min(fitRange, buildingsVisibleWithin(item.geometricError, fovy) * 0.75);
      if (!Number.isFinite(range) || range <= 0) range = 0; // 0 = jarak otomatis Cesium
    }
    flyToSphere(sphere, { range, ...options });
  };

  const zoomToBontangKuala = (options) => flyToKelurahan('bontang_kuala', options);

  return {
    // state (shallowRef)
    tilesetRef,
    kelurahanList,
    loadError,
    // siklus hidup
    load3DTiles,
    unload3DTiles: releaseResources,
    // interaksi
    setupTilePicking,
    teardownTilePicking,
    // navigasi
    zoomToKota,
    flyToKelurahan,
    zoomToBontangKuala
  };
}
