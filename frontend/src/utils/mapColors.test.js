import { test } from 'node:test';
import assert from 'node:assert/strict';
import { getMapColors, HIGHLIGHT_HEX, MAP_COLORS_BY_THEME } from './mapColors.js';

test('kedua tema punya kunci yang sama dan semuanya hex 6 digit', () => {
  const keys = Object.keys(MAP_COLORS_BY_THEME.gelap).sort();
  assert.deepEqual(Object.keys(MAP_COLORS_BY_THEME.terang).sort(), keys);
  for (const set of Object.values(MAP_COLORS_BY_THEME)) {
    for (const [k, v] of Object.entries(set)) assert.match(v, /^#[0-9A-F]{6}$/i, k);
  }
});

test('sorotan tetap amber di kedua tema; tema tak dikenal jatuh ke gelap', () => {
  assert.equal(getMapColors('terang').selection, HIGHLIGHT_HEX);
  assert.equal(getMapColors('gelap').selection, HIGHLIGHT_HEX);
  assert.equal(getMapColors('x'), MAP_COLORS_BY_THEME.gelap);
});

test('warna garis berbeda per tema (tidak ada garis putih di peta terang)', () => {
  assert.notEqual(getMapColors('terang').kelurahan, getMapColors('gelap').kelurahan);
  assert.notEqual(getMapColors('terang').kelurahan.toUpperCase(), '#FFFFFF');
});
