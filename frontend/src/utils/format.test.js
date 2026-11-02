// Jalankan: npm test (node --test, tanpa dependensi tambahan).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatDegrees, formatNumber, formatWithUnit } from './format.js';

test('formatNumber memakai koma desimal dan titik ribuan', () => {
  assert.equal(formatNumber(1234567.891), '1.234.567,89');
  assert.equal(formatNumber(0.5, { minDigits: 2 }), '0,50');
  assert.equal(formatNumber('12.5'), '12,5');
  assert.equal(formatNumber(0), '0');
});

test('formatNumber mengembalikan null untuk nilai bukan angka', () => {
  for (const v of [null, undefined, '', '-', NaN, Infinity, {}]) {
    assert.equal(formatNumber(v), null, `nilai: ${String(v)}`);
  }
});

test('formatDegrees & formatWithUnit', () => {
  assert.equal(formatDegrees(117.5169), '117,516900°');
  assert.equal(formatDegrees(undefined), null);
  assert.equal(formatWithUnit(12.345, 'm'), '12,35 m');
  assert.equal(formatWithUnit('x', 'm'), null);
});
