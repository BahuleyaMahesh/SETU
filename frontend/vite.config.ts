import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  // maplibre-gl ships its tile-processing code as a Web Worker (.mjs).
  // Vite's dependency pre-bundler mangles that worker's module exports,
  // so it silently fails to load and tiles never render (markers/attribution
  // still show since those are plain DOM, not routed through the worker).
  // Excluding it from pre-bundling serves it natively and fixes this.
  optimizeDeps: {
    exclude: ['maplibre-gl'],
  },
  worker: {
    format: 'es',
  },
});
