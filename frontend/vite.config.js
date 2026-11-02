import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import cesium from 'vite-plugin-cesium';
import path from 'path';

export default defineConfig({
  plugins: [
    vue(),
    cesium()
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 3000,
    open: true,
    // Backend FastAPI (backend/). Browser hanya memanggil /api; backend yang mengakses geoportal.
    proxy: {
      '/api': process.env.SPECTRA_API_URL || 'http://127.0.0.1:8100'
    }
  }
});
