import { test } from 'node:test';
import assert from 'node:assert/strict';
import { BASEMAP_AUTO, isBasemapMode, isThemePref, readStored, resolveBasemap, resolveTheme, writeStored } from './theme.js';

test('resolveTheme: pilihan eksplisit menang, sistem mengikuti prefers-color-scheme', () => {
  assert.equal(resolveTheme('terang', true), 'terang');
  assert.equal(resolveTheme('gelap', false), 'gelap');
  assert.equal(resolveTheme('sistem', true), 'gelap');
  assert.equal(resolveTheme('sistem', false), 'terang');
  assert.equal(resolveTheme('tidak-dikenal', false), 'terang');
});

test('isThemePref hanya menerima sistem/terang/gelap', () => {
  assert.ok(isThemePref('sistem') && isThemePref('terang') && isThemePref('gelap'));
  assert.ok(!isThemePref('light') && !isThemePref(null) && !isThemePref(''));
});

test('resolveBasemap: otomatis mengikuti tema, pilihan manual tidak tertimpa saat tema berganti', () => {
  assert.equal(resolveBasemap(BASEMAP_AUTO, 'terang'), 'terang');
  assert.equal(resolveBasemap(BASEMAP_AUTO, 'gelap'), 'gelap');
  for (const manual of ['terang', 'gelap', 'satelit', 'osm']) {
    assert.equal(resolveBasemap(manual, 'terang'), manual);
    assert.equal(resolveBasemap(manual, 'gelap'), manual);
  }
});

test('isBasemapMode memvalidasi terhadap daftar id', () => {
  const ids = ['terang', 'gelap', 'satelit', 'osm'];
  assert.ok(isBasemapMode('otomatis', ids) && isBasemapMode('satelit', ids));
  assert.ok(!isBasemapMode('carto', ids) && !isBasemapMode(null, ids));
});

test('akses localStorage dibungkus try/catch (tanpa window / diblokir tidak melempar)', () => {
  assert.equal(readStored('spectra.theme'), null); // Node: window tidak ada
  assert.doesNotThrow(() => writeStored('spectra.theme', 'gelap'));
});
