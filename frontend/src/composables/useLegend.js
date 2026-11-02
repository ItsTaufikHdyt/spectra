import { computed } from 'vue';
import { useMapStore } from '@/stores/mapStore';
import { MAP_COLORS } from '@/utils/mapColors';

/**
 * Bagian legenda (data biasa, dipakai bersama oleh layer dan simulasi):
 *  - Kategorikal: { id, title, type: 'categorical', items: [{ label, color, shape }] }
 *      shape: 'fill' | 'outline' | 'dot'
 *  - Skala warna: { id, title, type: 'gradient', unit, stops: [{ value, color }] }
 *      stops urut naik; label min/maks diformat id-ID.
 */
export function useLegend() {
  const mapStore = useMapStore();

  const layerSections = computed(() => {
    if (!mapStore.is3DTilesActive) return [];
    return [
      {
        id: 'bangunan',
        title: 'Bangunan',
        type: 'categorical',
        items: [
          { label: 'Bangunan 3D (LOD2)', color: MAP_COLORS.building, shape: 'fill' },
          { label: 'Kelurahan, saat kamera jauh', color: MAP_COLORS.overview, shape: 'outline' },
          { label: 'Titik terpilih', color: MAP_COLORS.selection, shape: 'dot' }
        ]
      }
    ];
  });

  const sections = computed(() => [...layerSections.value]);

  return { sections };
}
