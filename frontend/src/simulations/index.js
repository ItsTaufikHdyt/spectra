// Registry simulasi. Menambah simulasi = buat folder baru + daftarkan di SIMULATIONS.
// Inti aplikasi (store, composable, panel, legenda) tidak perlu diubah.
import { validateRegistry } from './contract.js';

// Contoh pendaftaran (setelah simulasi banjir dibuat):
//   import banjir from './banjir/index.js';
//   export const SIMULATIONS = validateRegistry([banjir]);
export const SIMULATIONS = validateRegistry([]);

/** Simulasi yang direncanakan, ditampilkan sebagai "Segera hadir" di panel kiri. */
export const PLANNED_SIMULATIONS = Object.freeze([
  {
    id: 'banjir',
    name: 'Simulasi banjir',
    note: 'Genangan banjir dan rob berdasarkan ketinggian muka air.'
  }
]);

export const getSimulation = (id) => SIMULATIONS.find((s) => s.id === id) ?? null;
