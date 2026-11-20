import { ref } from 'vue';
import * as Cesium from 'cesium';
import { viewer, requestRender } from '@/composables/useCesium';
import { formatCoord, niceScale } from '@/utils/coords';

// State bacaan peta untuk overlay (kompas, skala, koordinat, mode kamera). Hanya angka/teks biasa;
// objek Cesium tidak disimpan di sini. Semua pembacaan memakai camera.changed + pickEllipsoid,
// tanpa scene.pick (AGENTS.md §4) dan tanpa requestRender().
export const headingDeg = ref(0);
export const pitchDeg = ref(-45);
export const scaleBar = ref(null); // { label, widthPx } atau null bila langit/di luar globe
export const cursorText = ref('');

const SCALE_MAX_PX = 100;
const ATAS_PITCH = -90;
const MIRING_PITCH = -45;
const DEG = Cesium.Math.toDegrees;

let teardown = null;

const canvasPoint = (v, x, y) => v.camera.pickEllipsoid(new Cesium.Cartesian2(x, y), v.scene.globe.ellipsoid);
const teks = (p) => {
  if (!p) return '';
  const c = Cesium.Cartographic.fromCartesian(p);
  return formatCoord(DEG(c.latitude), DEG(c.longitude));
};

/** Mulai membaca kamera. Panggil setelah viewer ada; lepas dengan releaseMapControls(). */
export function startMapControls() {
  releaseMapControls();
  const v = viewer.value;
  if (!v || v.isDestroyed()) return;
  const canvas = v.scene.canvas;
  const sentuh = window.matchMedia('(hover: none)').matches; // layar sentuh: tampilkan koordinat pusat peta

  const bacaKamera = () => {
    if (v.isDestroyed()) return;
    headingDeg.value = DEG(v.camera.heading);
    pitchDeg.value = DEG(v.camera.pitch);
    const { clientWidth: w, clientHeight: h } = canvas;
    const a = canvasPoint(v, w / 2 - SCALE_MAX_PX / 2, h - 40);
    const b = canvasPoint(v, w / 2 + SCALE_MAX_PX / 2, h - 40);
    const s = a && b ? niceScale(Cesium.Cartesian3.distance(a, b)) : null;
    scaleBar.value = s ? { label: s.label, widthPx: Math.round(SCALE_MAX_PX * s.fraction) } : null;
    if (sentuh) cursorText.value = teks(canvasPoint(v, w / 2, h / 2));
  };
  v.camera.changed.addEventListener(bacaKamera);
  v.camera.percentageChanged = 0.02;
  bacaKamera();

  // Koordinat kursor: pointermove DOM biasa, satu pembacaan per frame animasi.
  let raf = 0;
  let last = null;
  const onMove = (e) => {
    last = e;
    if (raf || sentuh) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      if (v.isDestroyed() || !last) return;
      const r = canvas.getBoundingClientRect();
      cursorText.value = teks(canvasPoint(v, last.clientX - r.left, last.clientY - r.top));
    });
  };
  const onLeave = () => { last = null; if (!sentuh) cursorText.value = ''; };
  canvas.addEventListener('pointermove', onMove);
  canvas.addEventListener('pointerleave', onLeave);

  teardown = () => {
    cancelAnimationFrame(raf);
    canvas.removeEventListener('pointermove', onMove);
    canvas.removeEventListener('pointerleave', onLeave);
    if (!v.isDestroyed()) v.camera.changed.removeEventListener(bacaKamera);
  };
}

export function releaseMapControls() {
  teardown?.();
  teardown = null;
  scaleBar.value = null;
  cursorText.value = '';
}

/** Putar/miringkan kamera mengelilingi titik di tengah layar (jarak tetap). */
const orbit = ({ heading, pitch }) => {
  const v = viewer.value;
  if (!v || v.isDestroyed()) return;
  const cam = v.camera;
  const target = canvasPoint(v, v.scene.canvas.clientWidth / 2, v.scene.canvas.clientHeight / 2);
  if (!target) return;
  cam.flyToBoundingSphere(new Cesium.BoundingSphere(target, 0), {
    duration: 0.8,
    offset: new Cesium.HeadingPitchRange(heading ?? cam.heading, pitch ?? cam.pitch, Cesium.Cartesian3.distance(cam.positionWC, target))
  });
};

export const useMapControls = () => ({
  zoomIn: () => {
    const v = viewer.value;
    if (!v || v.isDestroyed()) return;
    v.camera.zoomIn(Math.max(v.camera.positionCartographic.height * 0.4, 5));
    requestRender();
  },
  zoomOut: () => {
    const v = viewer.value;
    if (!v || v.isDestroyed()) return;
    v.camera.zoomOut(Math.max(v.camera.positionCartographic.height * 0.6, 5));
    requestRender();
  },
  resetNorth: () => orbit({ heading: 0 }),
  /** 'atas' = menghadap lurus ke bawah; '3d' = miring. */
  setViewMode: (mode) => orbit({ pitch: Cesium.Math.toRadians(mode === 'atas' ? ATAS_PITCH : MIRING_PITCH) })
});
