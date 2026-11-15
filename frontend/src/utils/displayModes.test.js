import test from 'node:test';
import assert from 'node:assert/strict';
import { DEFAULT_LEVEL, DISPLAY_LEVELS, DISPLAY_MODES, isDisplayLevel } from './displayModes.js';

test('tiga level, default Seimbang', () => {
  assert.deepEqual(DISPLAY_LEVELS, ['hemat', 'seimbang', 'kualitas']);
  assert.equal(DEFAULT_LEVEL, 'seimbang');
});

test('isDisplayLevel menolak nilai asing (termasuk kunci prototipe)', () => {
  assert.equal(isDisplayLevel('hemat'), true);
  for (const v of ['ultra', '', null, undefined, 3, 'toString', '__proto__']) assert.equal(isDisplayLevel(v), false, String(v));
});

test('Hemat <= Seimbang <= Kualitas: detail naik, SSE turun', () => {
  const [h, s, k] = DISPLAY_LEVELS.map((l) => DISPLAY_MODES[l]);
  assert.ok(h.tilesetSSE > s.tilesetSSE && s.tilesetSSE > k.tilesetSSE);
  assert.ok(h.globeSSE > s.globeSSE && s.globeSSE > k.globeSSE);
  assert.ok(h.resolutionScale(2) < s.resolutionScale(2) && s.resolutionScale(2) <= k.resolutionScale(2));
});

test('MSAA dan FXAA tidak dipakai bersamaan; resolusi Kualitas dibatasi 2x', () => {
  for (const m of Object.values(DISPLAY_MODES)) assert.ok(!(m.msaa > 1 && m.fxaa));
  assert.equal(DISPLAY_MODES.kualitas.resolutionScale(3), 2);
  assert.equal(DISPLAY_MODES.kualitas.resolutionScale(1), 1);
  assert.equal(DISPLAY_MODES.kualitas.resolutionScale(undefined), 1);
});
