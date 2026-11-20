import * as Cesium from 'cesium';
import { requestRender, viewer } from './useCesium';
import { HIGHLIGHT_HEX } from '@/utils/mapColors';
import { buildStyleSpec } from '@/utils/tilesetStyleSpec';

/**
 * PENYUSUN STYLE TILESET — satu-satunya tempat yang mengatur gaya warna tileset bangunan.
 * Fitur lain (picking, tema, simulasi) TIDAK boleh menyentuh `tileset.style` atau `feature.color`;
 * mereka memanggil API di bawah. Prioritas tampilan: sorotan > simulasi > tema.
 *  - tema      : warna bangunan per tema (utils/tilesetStyleSpec.js)
 *  - simulasi  : slot untuk hasil simulasi per bangunan (ADR-006); kondisi gaya Cesium berbasis properti `id`
 *  - sorotan   : satu fitur terpilih, `feature.color` per fitur (murah; tanpa menyusun ulang gaya seluruh tileset)
 * Objek Cesium disimpan di variabel biasa (BUKAN ref/reactive).
 */
let tileset = null;
let theme = 'gelap';
let simulation = null; // { conditions: [[ekspresi, warna], ...] } | null
let highlighted = null; // Cesium3DTileFeature | null
let removePostRender = null;
const scratch = new Cesium.Color();
const HIGHLIGHT_COLOR = Cesium.Color.fromCssColorString(HIGHLIGHT_HEX).withAlpha(0.85);

const tilesetAlive = () => !!tileset && !tileset.isDestroyed();
const viewerAlive = () => !!viewer.value && !viewer.value.isDestroyed();

const paintHighlight = () => {
  if (!highlighted) return;
  try {
    highlighted.color = HIGHLIGHT_COLOR;
  } catch {
    highlighted = null; // tile sudah di-unload dari cache
  }
};

/** Warna fitur menurut gaya yang berlaku (putih = tanpa perubahan bila tidak ada gaya). */
const styledColor = (feature) => {
  const color = tileset?.style?.color;
  return color ? color.evaluateColor(feature, scratch) : Cesium.Color.WHITE;
};

/** Gaya baru diterapkan Cesium pada frame berikutnya dan menimpa warna fitur; cat ulang sorotan sesudahnya. */
const repaintHighlightAfterRestyle = () => {
  if (!highlighted || !viewerAlive()) return;
  removePostRender?.();
  removePostRender = viewer.value.scene.postRender.addEventListener(() => {
    removePostRender?.(); // satu kali
    removePostRender = null;
    paintHighlight();
    requestRender();
  });
};

const apply = () => {
  if (!tilesetAlive()) return;
  const spec = buildStyleSpec({ theme, simulation });
  tileset.style = spec ? new Cesium.Cesium3DTileStyle(spec) : undefined;
  repaintHighlightAfterRestyle();
  requestRender();
};

/** Hubungkan tileset (dipanggil use3DTiles setelah tileset ditambahkan ke scene). */
export const attachTileset = (ts, initialTheme = theme) => {
  tileset = ts;
  theme = initialTheme;
  apply();
};

/** Lepas referensi (dipanggil sebelum tileset di-destroy). Idempoten. */
export const detachTileset = () => {
  removePostRender?.();
  removePostRender = null;
  highlighted = null;
  tileset = null;
};

export const setTheme = (next) => {
  if (next === theme) return;
  theme = next;
  apply();
};

/** Slot simulasi (ADR-006). Argumen: { conditions: [[ekspresi, warna], ...] } atau null untuk menghapus. */
export const setSimulationStyle = (spec) => {
  simulation = spec ?? null;
  apply();
};

export const clearHighlight = () => {
  const feature = highlighted;
  highlighted = null;
  if (!feature) return;
  try {
    feature.color = styledColor(feature);
  } catch {
    // Tile sudah di-unload dari cache; tidak ada yang perlu dipulihkan.
  }
  requestRender();
};

export const highlightFeature = (feature) => {
  clearHighlight();
  if (!feature) return;
  highlighted = feature;
  paintHighlight();
  requestRender();
};
