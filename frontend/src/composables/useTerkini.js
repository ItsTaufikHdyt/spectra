import { SUMBER_TERKINI, TTL_DETIK, useTerkiniStore } from '@/stores/terkiniStore';
import { umurDetik } from '@/utils/terkini';

// Polling "Kondisi Terkini": interval mengikuti TTL backend, berhenti saat tab browser tersembunyi, dan TIDAK
// menyentuh Cesium (tidak ada requestRender; yang berubah hanya teks DOM di panel).
let timers = [];
let aktif = false;
let store = null;

const hentikanTimer = () => { timers.forEach(clearInterval); timers = []; };
const mulaiTimer = () => {
  hentikanTimer();
  timers = SUMBER_TERKINI.map((s) => setInterval(() => store.muat(s), TTL_DETIK[s] * 1000));
};
const segarkanYangBasi = () =>
  SUMBER_TERKINI.forEach((s) => {
    const umur = umurDetik(store.sumber[s].data?.diambil_pada);
    if (!store.sumber[s].data || umur === null || umur >= TTL_DETIK[s]) store.muat(s);
  });

const onVisibility = () => {
  if (!aktif) return;
  if (document.hidden) hentikanTimer();
  else { segarkanYangBasi(); mulaiTimer(); }
};

/** Mulai (idempoten). Dipanggil saat panel Kondisi Terkini terlihat. */
export function startTerkini() {
  if (aktif) return;
  store = useTerkiniStore();
  aktif = true;
  document.addEventListener('visibilitychange', onVisibility);
  if (!document.hidden) { segarkanYangBasi(); mulaiTimer(); }
}

/** Hentikan polling dan lepas listener. */
export function stopTerkini() {
  aktif = false;
  hentikanTimer();
  document.removeEventListener('visibilitychange', onVisibility);
}
