import { computed } from 'vue';
import { useMapStore } from '@/stores/mapStore';
import { getMapColors } from '@/utils/mapColors';
import { useThemeStore } from '@/stores/themeStore';
import { useSimulationStore } from '@/stores/simulationStore';
import { getSimulation } from '@/simulations';
import { useRemoteLayerStore } from '@/stores/remoteLayerStore';

/**
 * Bagian legenda (data biasa, dipakai bersama oleh layer dan simulasi):
 *  - Kategorikal: { id, title, type: 'categorical', items: [{ label, color, shape }] }
 *      shape: 'fill' | 'outline' | 'dot' | 'line' | 'line-thin'
 *  - Skala warna: { id, title, type: 'gradient', unit, stops: [{ value, color }] }
 *      stops urut naik; label min/maks diformat id-ID.
 */
export function useLegend() {
  const mapStore = useMapStore();
  const themeStore = useThemeStore();
  // Warna legenda = warna peta untuk tema aktif (satu sumber: utils/mapColors.js).
  const colors = computed(() => getMapColors(themeStore.theme));

  const vectorSections = computed(() => {
    const out = [];
    const boundaries = [
      mapStore.isKelurahanActive && { label: 'Batas kelurahan', color: colors.value.kelurahan, shape: 'line' },
      mapStore.isRtActive && { label: 'Batas RT', color: colors.value.rt, shape: 'line-thin' }
    ].filter(Boolean);
    if (boundaries.length) out.push({ id: 'batas-wilayah', title: 'Batas wilayah', type: 'categorical', items: boundaries });
    if (mapStore.isSungaiActive) {
      out.push({
        id: 'hidrologi',
        title: 'Hidrologi',
        type: 'categorical',
        items: [
          { label: 'Sungai', color: colors.value.sungai, shape: 'line' },
          { label: 'Drainase', color: colors.value.drainase, shape: 'line' }
        ]
      });
    }
    return out;
  });

  const layerSections = computed(() => {
    if (!mapStore.is3DTilesActive) return vectorSections.value;
    return [
      ...vectorSections.value,
      {
        id: 'bangunan',
        title: 'Bangunan',
        type: 'categorical',
        items: [
          { label: 'Bangunan 3D (LOD2)', color: colors.value.building, shape: 'fill' },
          { label: 'Kelurahan, saat kamera jauh', color: colors.value.overview, shape: 'outline' },
          { label: 'Titik terpilih', color: colors.value.selection, shape: 'dot' }
        ]
      }
    ];
  });

  // Legenda simulasi aktif: disediakan oleh definisi simulasi (kontrak `legend(params)`).
  const simulationStore = useSimulationStore();
  const simulationSections = computed(() => {
    const def = simulationStore.status === 'active' ? getSimulation(simulationStore.activeId) : null;
    if (!def || !simulationStore.visible) return [];
    try {
      return def.legend({ ...simulationStore.params }) ?? [];
    } catch (err) {
      console.warn(`[useLegend] Legenda simulasi ${def.id} gagal dibuat:`, err);
      return [];
    }
  });

  // Layer geoportal aktif: warna dari registry; WMS digambar server, jadi hanya tanda kotak.
  const remoteStore = useRemoteLayerStore();
  const remoteSections = computed(() => {
    const items = remoteStore.layers
      .filter((l) => l.aktif)
      .map((l) => (l.mode === 'wms'
        ? { label: `${l.judul} (WMS)`, color: '#9DB2BE', shape: 'outline' }
        : { label: l.judul, color: l.warna, shape: 'fill' }));
    return items.length ? [{ id: 'geoportal', title: 'Data geoportal', type: 'categorical', items }] : [];
  });

  const sections = computed(() => [...simulationSections.value, ...remoteSections.value, ...layerSections.value]);

  return { sections };
}
