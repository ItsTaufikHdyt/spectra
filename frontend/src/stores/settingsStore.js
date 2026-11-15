import { defineStore } from 'pinia';
import { ref } from 'vue';
import { DEFAULT_LEVEL, DISPLAY_MODES, isDisplayLevel } from '@/utils/displayModes';
import { classifyRenderer, readRendererName } from '@/utils/gpuInfo';

const STORAGE_KEY = 'spectra.displayMode';

// localStorage bisa melempar error (jendela privat, data situs diblokir): selalu dibungkus.
const readSaved = () => {
  try {
    const v = window.localStorage.getItem(STORAGE_KEY);
    return isDisplayLevel(v) ? v : null;
  } catch {
    return null;
  }
};
const save = (level) => {
  try {
    window.localStorage.setItem(STORAGE_KEY, level);
  } catch {
    // Tidak tersimpan; mode tetap berlaku selama sesi ini.
  }
};

/**
 * Pengaturan tampilan. Urutan penentuan level awal:
 *  1. `?mode=hemat|seimbang|kualitas` di URL (untuk uji; tidak disimpan),
 *  2. pilihan tersimpan pengguna,
 *  3. perangkat tampak lemah (GPU terintegrasi / renderer software) -> Hemat + pemberitahuan,
 *  4. Seimbang.
 */
export const useSettingsStore = defineStore('settings', () => {
  const level = ref(DEFAULT_LEVEL);
  /** Teks pemberitahuan bila Hemat dipilih otomatis; kosong bila tidak ada. */
  const autoNotice = ref('');

  const fromQuery = new URLSearchParams(window.location.search).get('mode');
  const saved = readSaved();
  if (isDisplayLevel(fromQuery)) {
    level.value = fromQuery;
  } else if (saved) {
    level.value = saved;
  } else {
    const name = readRendererName();
    const { weak, reason } = classifyRenderer(name);
    if (weak) {
      level.value = 'hemat';
      autoNotice.value = `Perangkat ini memakai ${reason}${name ? ` (${name.replace(/^ANGLE \(|\)$/g, '')})` : ''}, jadi mode Hemat dipakai agar peta tetap lancar. Ubah kapan saja di Mode tampilan.`;
    }
  }

  const setLevel = (next) => {
    if (!isDisplayLevel(next)) return;
    level.value = next;
    autoNotice.value = '';
    save(next);
  };
  const dismissNotice = () => {
    autoNotice.value = '';
  };

  return { level, autoNotice, modes: DISPLAY_MODES, setLevel, dismissNotice };
});
