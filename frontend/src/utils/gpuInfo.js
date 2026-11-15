// Deteksi perangkat grafis yang tampak lemah (renderer software atau GPU terintegrasi).
// Fungsi murni + satu pembaca WebGL, agar bagian regex bisa diuji dengan `npm test`.

const SOFTWARE = /swiftshader|llvmpipe|softpipe|software|basic render|microsoft basic|lavapipe/i;
// GPU terintegrasi / seluler umum. "Radeon Graphics" tanpa seri (RX/Pro) = APU AMD.
const INTEGRATED = /intel|\buhd\b|\biris\b|mali|adreno|powervr|videocore|vega|radeon\(tm\) graphics|radeon graphics/i;

/** @returns {{ weak: boolean, reason: string }} reason = '' bila tidak lemah. */
export function classifyRenderer(name) {
  const text = String(name ?? '');
  if (SOFTWARE.test(text)) return { weak: true, reason: 'renderer software' };
  if (INTEGRATED.test(text)) return { weak: true, reason: 'GPU terintegrasi' };
  return { weak: false, reason: '' };
}

/** Nama renderer WebGL, atau null bila tidak bisa dibaca. Konteks sementara langsung dilepas. */
export function readRendererName() {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl2') ?? canvas.getContext('webgl');
    if (!gl) return null;
    const info = gl.getExtension('WEBGL_debug_renderer_info');
    const name = info ? gl.getParameter(info.UNMASKED_RENDERER_WEBGL) : null;
    gl.getExtension('WEBGL_lose_context')?.loseContext();
    return name;
  } catch {
    return null;
  }
}
