import * as Cesium from 'cesium';
import { requestRender, viewer } from './useCesium';
import { useSimulationStore } from '@/stores/simulationStore';
import { assertSimulationLayer } from '@/simulations/contract';
import { getSimulation } from '@/simulations';

// Layer hasil simulasi aktif: objek Cesium -> variabel modul biasa, BUKAN ref/Pinia.
let activeLayer = null;
let generation = 0; // membatalkan createLayer yang masih berjalan

/** Salinan polos parameter agar simulasi tidak memegang proxy reaktif Vue. */
const plain = (params) => ({ ...params });

/** Lepas layer aktif. Idempoten; dipanggil sebelum unload3DTiles()/destroyViewer(). */
export const releaseSimulation = () => {
  generation++;
  const layer = activeLayer;
  activeLayer = null;
  try {
    layer?.destroy();
  } catch (err) {
    console.warn('[useSimulation] Gagal melepas layer simulasi:', err);
  }
};

if (import.meta.hot) {
  import.meta.hot.dispose(releaseSimulation);
}

export function useSimulation() {
  const store = useSimulationStore();

  const deactivate = () => {
    releaseSimulation();
    store.reset();
    requestRender(); // hasil simulasi yang dilepas harus hilang dari frame
  };

  /** Aktifkan satu simulasi (hanya satu aktif pada satu waktu). */
  const activate = async (id) => {
    deactivate();
    const def = getSimulation(id);
    const v = viewer.value;
    if (!def || !v || v.isDestroyed()) return;

    const gen = generation;
    store.activeId = id;
    store.params = def.defaultParams();
    store.status = 'loading';
    try {
      const layer = assertSimulationLayer(
        await def.createLayer({ viewer: v, Cesium }, plain(store.params)),
        id
      );
      if (gen !== generation) {
        layer.destroy(); // dibatalkan selama pembuatan
        return;
      }
      activeLayer = layer;
      store.status = 'active';
      requestRender();
    } catch (err) {
      if (gen !== generation) return;
      console.warn(`[useSimulation] Simulasi ${id} gagal dijalankan:`, err);
      store.error = err?.message ?? String(err);
      store.status = 'error';
    }
  };

  /** Terapkan perubahan parameter (patch) ke store lalu ke layer. */
  const updateParams = async (patch) => {
    store.params = { ...store.params, ...patch };
    if (!activeLayer) return;
    const gen = generation;
    try {
      await activeLayer.update(plain(store.params));
      requestRender(); // update() boleh async; render ulang setelah selesai
    } catch (err) {
      if (gen !== generation) return;
      store.error = err?.message ?? String(err);
      store.status = 'error';
    }
  };

  const setVisible = (visible) => {
    store.visible = visible;
    activeLayer?.setVisible(visible);
    requestRender();
  };

  return { activate, deactivate, updateParams, setVisible };
}
