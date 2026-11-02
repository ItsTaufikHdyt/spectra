import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useMapStore = defineStore('map', () => {
  const activeBasemap = ref('arcgis'); // 'arcgis' | 'osm'
  const is3DTilesActive = ref(true);
  // Layer vektor (composables/useVectorLayers.js). RT mati default: 1,9 MB, dimuat saat dinyalakan.
  const isKelurahanActive = ref(true);
  const isRtActive = ref(false);
  const isSungaiActive = ref(true);

  const setBasemap = (type) => {
    activeBasemap.value = type;
  };

  return {
    activeBasemap,
    is3DTilesActive,
    isKelurahanActive,
    isRtActive,
    isSungaiActive,
    setBasemap
  };
});
