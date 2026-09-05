import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ command }) => ({
  plugins: [react()],

  // '/SETU/' is required for GitHub Pages, which serves this app from a
  // subpath — but it breaks local dev (root-absolute asset paths like
  // "/setu-logo.png" 404 against the dev server). Only apply it for
  // production builds; local dev keeps the default root base.
  base: command === 'build' ? '/SETU/' : '/',

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

  worker: {
    format: 'es',
  },
}));