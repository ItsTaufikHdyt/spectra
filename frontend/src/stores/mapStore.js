import { defineStore } from 'pinia';
import { ref } from 'vue';

// Pilihan peta dasar dan tema ada di themeStore (stores/themeStore.js).
export const useMapStore = defineStore('map', () => {
  const is3DTilesActive = ref(true);
  // Layer vektor (composables/useVectorLayers.js). RT mati default: 1,9 MB, dimuat saat dinyalakan.
  const isKelurahanActive = ref(true);
  const isRtActive = ref(false);
  const isSungaiActive = ref(true);

  return {
    is3DTilesActive,
    isKelurahanActive,
    isRtActive,
    isSungaiActive
  };
});
