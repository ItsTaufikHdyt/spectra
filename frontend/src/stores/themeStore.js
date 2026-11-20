import { defineStore } from 'pinia';
import { computed, ref, watch } from 'vue';
import { BASEMAP_IDS } from '@/config/basemaps';
import {
  BASEMAP_AUTO,
  BASEMAP_STORAGE_KEY,
  THEME_PREFS,
  THEME_STORAGE_KEY,
  isBasemapMode,
  isThemePref,
  readStored,
  resolveBasemap,
  resolveTheme,
  writeStored
} from '@/utils/theme';

/**
 * Tema tampilan dan pilihan peta dasar.
 *  - preference: 'sistem' (bawaan, ikut prefers-color-scheme) | 'terang' | 'gelap'; tersimpan di localStorage.
 *  - basemapMode: 'otomatis' (bawaan, ikut tema) | id basemap manual; tersimpan terpisah dan
 *    TIDAK tertimpa saat tema berganti.
 * Penerapan ke DOM (data-theme, color-scheme) ada di sini agar toggle tema tetap bekerja walau viewer gagal;
 * efek ke peta Cesium ada di composables/useTheme.js.
 */
export const useThemeStore = defineStore('theme', () => {
  const saved = readStored(THEME_STORAGE_KEY);
  const preference = ref(isThemePref(saved) ? saved : 'sistem');

  const media = typeof window !== 'undefined' && window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  const systemDark = ref(!!media?.matches);
  media?.addEventListener?.('change', (e) => {
    systemDark.value = e.matches;
  });

  const theme = computed(() => resolveTheme(preference.value, systemDark.value));

  const savedBasemap = readStored(BASEMAP_STORAGE_KEY);
  const basemapMode = ref(isBasemapMode(savedBasemap, BASEMAP_IDS) ? savedBasemap : BASEMAP_AUTO);
  const basemap = computed(() => resolveBasemap(basemapMode.value, theme.value));

  const setPreference = (next) => {
    if (!isThemePref(next)) return;
    preference.value = next;
    writeStored(THEME_STORAGE_KEY, next);
  };
  const setBasemapMode = (next) => {
    if (!isBasemapMode(next, BASEMAP_IDS)) return;
    basemapMode.value = next;
    writeStored(BASEMAP_STORAGE_KEY, next);
  };

  // DOM: atribut tema + color-scheme (kontrol bawaan browser ikut terang/gelap).
  watch(
    theme,
    (t) => {
      const root = document.documentElement;
      root.setAttribute('data-theme', t);
      root.style.colorScheme = t === 'terang' ? 'light' : 'dark';
    },
    { immediate: true }
  );

  return { preference, theme, basemapMode, basemap, prefs: THEME_PREFS, setPreference, setBasemapMode };
});
