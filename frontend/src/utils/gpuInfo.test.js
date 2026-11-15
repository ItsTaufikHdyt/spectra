import test from 'node:test';
import assert from 'node:assert/strict';
import { classifyRenderer } from './gpuInfo.js';

test('renderer software dianggap lemah', () => {
  for (const n of ['ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero)), SwiftShader driver)', 'llvmpipe (LLVM 15)', 'Microsoft Basic Render Driver']) {
    assert.deepEqual(classifyRenderer(n), { weak: true, reason: 'renderer software' }, n);
  }
});

test('GPU terintegrasi dianggap lemah', () => {
  for (const n of ['ANGLE (Intel, Intel(R) UHD Graphics 620, OpenGL 4.6)', 'ANGLE (AMD, AMD Radeon Graphics (radeonsi renoir ACO), OpenGL 4.6)', 'Mali-G78', 'Adreno (TM) 650']) {
    assert.deepEqual(classifyRenderer(n), { weak: true, reason: 'GPU terintegrasi' }, n);
  }
});

test('GPU diskrit tidak dianggap lemah; nama kosong aman', () => {
  for (const n of ['ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 Ti Laptop GPU, OpenGL 4.6)', 'ANGLE (AMD, AMD Radeon RX 6800 XT, OpenGL 4.6)', 'Apple M2', null, undefined, '']) {
    assert.equal(classifyRenderer(n).weak, false, String(n));
  }
});
