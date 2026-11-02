// Kontrak simulasi — lihat docs/simulation-contract.md.
// Modul murni (tanpa Vue/Cesium) agar validasinya bisa diuji dengan `npm test`.

/**
 * @typedef {Object} SimulationDefinition
 * @property {string} id            kebab-case unik, mis. 'banjir-rob'
 * @property {string} name          nama tampilan, mis. 'Simulasi banjir'
 * @property {string} description   satu-dua kalimat untuk pengguna
 * @property {object|Function} ParameterPanel
 *   Komponen Vue. Props: { params: object, disabled: boolean }. Emit: 'update:params' (patch).
 * @property {() => Record<string, unknown>} defaultParams
 *   Parameter awal; HANYA nilai biasa (angka, string, boolean, array/objek polos).
 * @property {(params: object) => object[]} legend
 *   Bagian legenda untuk parameter saat ini (format sama dengan legenda layer, lihat useLegend.js).
 * @property {(ctx: { viewer: object, Cesium: object }, params: object) => Promise<SimulationLayer>} createLayer
 *   Membuat layer hasil di viewer. Dipanggil saat simulasi diaktifkan.
 */

/**
 * Layer hasil simulasi. Memegang objek Cesium-nya sendiri (primitive, entity, imagery):
 * objek itu TIDAK boleh disimpan di Pinia/ref (aturan AGENTS.md).
 * @typedef {Object} SimulationLayer
 * @property {(params: object) => void|Promise<void>} update   terapkan parameter baru
 * @property {(visible: boolean) => void} setVisible
 * @property {() => void} destroy   lepas SEMUA resource Cesium; dipanggil sekali
 */

const ID_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const REQUIRED_FUNCTIONS = ['defaultParams', 'legend', 'createLayer'];

/**
 * Validasi definisi lalu bekukan. Melempar Error berbahasa Indonesia bila tidak sesuai kontrak,
 * sehingga kesalahan ketahuan saat modul dimuat, bukan saat pengguna menekan tombol.
 * @param {SimulationDefinition} def
 * @returns {Readonly<SimulationDefinition>}
 */
export function defineSimulation(def) {
  if (!def || typeof def !== 'object') throw new Error('Definisi simulasi harus berupa objek.');
  const label = def.id ?? '(tanpa id)';
  if (typeof def.id !== 'string' || !ID_PATTERN.test(def.id)) {
    throw new Error(`Simulasi ${label}: id wajib kebab-case, mis. 'banjir-rob'.`);
  }
  for (const key of ['name', 'description']) {
    if (typeof def[key] !== 'string' || def[key].trim() === '') {
      throw new Error(`Simulasi ${label}: '${key}' wajib berupa teks.`);
    }
  }
  if (!def.ParameterPanel || !['object', 'function'].includes(typeof def.ParameterPanel)) {
    throw new Error(`Simulasi ${label}: 'ParameterPanel' wajib berupa komponen Vue.`);
  }
  for (const key of REQUIRED_FUNCTIONS) {
    if (typeof def[key] !== 'function') {
      throw new Error(`Simulasi ${label}: '${key}' wajib berupa fungsi.`);
    }
  }
  return Object.freeze({ ...def });
}

/** Pastikan id unik di registry. Mengembalikan daftar yang sama bila valid. */
export function validateRegistry(list) {
  const seen = new Set();
  for (const sim of list) {
    if (seen.has(sim.id)) throw new Error(`Id simulasi ganda di registry: '${sim.id}'.`);
    seen.add(sim.id);
  }
  return list;
}

/** Layer simulasi wajib punya update/setVisible/destroy; dicek setelah createLayer(). */
export function assertSimulationLayer(layer, id) {
  for (const key of ['update', 'setVisible', 'destroy']) {
    if (typeof layer?.[key] !== 'function') {
      throw new Error(`Simulasi ${id}: createLayer() harus mengembalikan objek dengan fungsi '${key}'.`);
    }
  }
  return layer;
}
