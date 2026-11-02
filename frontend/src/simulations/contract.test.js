import { test } from 'node:test';
import assert from 'node:assert/strict';
import { assertSimulationLayer, defineSimulation, validateRegistry } from './contract.js';

const valid = () => ({
  id: 'banjir-rob',
  name: 'Simulasi banjir',
  description: 'Genangan berdasarkan ketinggian muka air.',
  ParameterPanel: { name: 'PanelUji' },
  defaultParams: () => ({ mukaAir: 1 }),
  legend: () => [],
  createLayer: async () => ({ update() {}, setVisible() {}, destroy() {} })
});

test('defineSimulation menerima definisi valid dan membekukannya', () => {
  const sim = defineSimulation(valid());
  assert.equal(sim.id, 'banjir-rob');
  assert.ok(Object.isFrozen(sim));
});

test('defineSimulation menolak definisi yang melanggar kontrak', () => {
  const cases = [
    [{ id: 'Banjir Rob' }, /kebab-case/],
    [{ name: '' }, /'name'/],
    [{ description: undefined }, /'description'/],
    [{ ParameterPanel: null }, /ParameterPanel/],
    [{ createLayer: 'bukan fungsi' }, /'createLayer'/],
    [{ legend: undefined }, /'legend'/]
  ];
  for (const [patch, pattern] of cases) {
    assert.throws(() => defineSimulation({ ...valid(), ...patch }), pattern);
  }
  assert.throws(() => defineSimulation(null), /objek/);
});

test('validateRegistry menolak id ganda', () => {
  const a = defineSimulation(valid());
  assert.deepEqual(validateRegistry([a]), [a]);
  assert.throws(() => validateRegistry([a, a]), /ganda/);
});

test('assertSimulationLayer memeriksa fungsi wajib', () => {
  assert.doesNotThrow(() => assertSimulationLayer({ update() {}, setVisible() {}, destroy() {} }, 'x'));
  assert.throws(() => assertSimulationLayer({ update() {} }, 'x'), /setVisible/);
  assert.throws(() => assertSimulationLayer(null, 'x'), /update/);
});
