import * as Cesium from 'cesium';
import { effectScope, watch } from 'vue';
import { requestRender, viewer } from './useCesium';
import { BASEMAPS, basemapById } from '@/config/basemaps';
import { useThemeStore } from '@/stores/themeStore';

// Terrain DTM belum tersambung: data quantized-mesh 1m belum ada di proyek.
// Globe memakai EllipsoidTerrainProvider bawaan Viewer; UI menampilkan "Segera hadir".

/**
 * Basemap berbasis konfigurasi (config/basemaps.js). Penyedia dibuat MALAS (saat pertama dipilih) agar
 * startup tidak menambah permintaan jaringan. Bila satu basemap gagal dimuat, dipakai `fallback` dari
 * konfigurasi tanpa mengubah pilihan pengguna. Basemap bersifat sekunder: kegagalannya tidak fatal.
 * Objek Cesium disimpan di Map/variabel biasa (BUKAN ref/reactive).
 */
const entries = new Map(); // id -> Promise<{ layers: ImageryLayer[], def }>  (null bila gagal)
let activeCredit = null; // Cesium.Credit statis dari basemap yang tampil
let activeId = null;
let scope = null;
let token = 0; // pilihan terbaru menang bila pengguna berpindah cepat

const viewerAlive = () => !!viewer.value && !viewer.value.isDestroyed();

const createProvider = async (def) => {
  switch (def.kind) {
    case 'arcgis':
      return Cesium.ArcGisMapServerImageryProvider.fromUrl(def.url);
    case 'osm':
      return new Cesium.OpenStreetMapImageryProvider({ url: def.url, credit: new Cesium.Credit(def.credit, true) }); // true = tampil di layar (ketentuan OSM)
    case 'xyz':
      return new Cesium.UrlTemplateImageryProvider({ url: def.url, credit: def.credit, maximumLevel: def.maximumLevel });
    default:
      throw new Error(`Jenis basemap tidak dikenal: ${def.kind}`);
  }
};

/** Buat lapisan (basemap + label) sekali; mengembalikan null bila gagal. */
const ensure = (id) => {
  if (entries.has(id)) return entries.get(id);
  const def = basemapById(id);
  const promise = (async () => {
    if (!def || !viewerAlive()) return null;
    try {
      const layers = [];
      const base = viewer.value.imageryLayers.addImageryProvider(await createProvider(def));
      base.show = false;
      viewer.value.imageryLayers.lowerToBottom(base);
      layers.push(base);
      if (def.reference) {
        const ref = viewer.value.imageryLayers.addImageryProvider(await Cesium.ArcGisMapServerImageryProvider.fromUrl(def.reference.url));
        ref.show = false;
        viewer.value.imageryLayers.raiseToTop(ref);
        layers.push(ref);
      }
      return { layers, def };
    } catch (err) {
      console.warn(`[useLayers] Basemap "${id}" gagal dimuat:`, err.message);
      return null;
    }
  })();
  entries.set(id, promise);
  return promise;
};

/** Tampilkan satu basemap (dan sembunyikan yang lain); atribusi dari konfigurasi ikut berganti. */
const show = async (id) => {
  const mine = ++token;
  let entry = await ensure(id);
  let def = basemapById(id);
  // Rantai fallback (dibatasi agar tidak berputar).
  for (let hops = 0; !entry && def?.fallback && hops < BASEMAPS.length; hops++) {
    def = basemapById(def.fallback);
    entry = def ? await ensure(def.id) : null;
  }
  if (mine !== token || !viewerAlive()) return; // pilihan lebih baru sudah masuk / viewer dihancurkan
  if (!entry) {
    requestRender();
    return;
  }
  for (const p of entries.values()) {
    const e = await p;
    if (e) for (const l of e.layers) l.show = e === entry;
  }
  if (mine !== token || !viewerAlive()) return;
  // Kredit statis dari konfigurasi: opsi credit Cesium diabaikan untuk server ArcGIS bertile.
  const display = viewer.value.creditDisplay;
  if (activeCredit) display.removeStaticCredit(activeCredit);
  activeCredit = entry.def.kind === 'arcgis' && entry.def.credit ? new Cesium.Credit(entry.def.credit, true) : null;
  if (activeCredit) display.addStaticCredit(activeCredit);
  activeId = entry.def.id;
  requestRender();
};

/** Lepas pengamat dan catatan lapisan (lapisan itu sendiri ikut hancur bersama viewer). Idempoten. */
export const releaseLayers = () => {
  token++;
  scope?.stop();
  scope = null;
  entries.clear();
  activeCredit = null;
  activeId = null;
};

export function useLayers() {
  const themeStore = useThemeStore();

  /** Tampilkan basemap awal dan ikuti perubahan pilihan/tema. Aman dipanggil ulang. */
  const initBasemaps = async () => {
    if (!viewerAlive()) return;
    releaseLayers(); // sisa percobaan sebelumnya (viewer baru)
    scope = effectScope(true); // detached: tidak ikut berhenti bersama komponen pemanggil
    scope.run(() => {
      watch(
        () => themeStore.basemap,
        (id) => show(id)
      );
    });
    await show(themeStore.basemap);
  };

  return { initBasemaps, releaseLayers, activeBasemapId: () => activeId };
}

if (import.meta.hot) import.meta.hot.dispose(releaseLayers);
