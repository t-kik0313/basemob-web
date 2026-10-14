import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';
const apiTarget = process.env.BASEMOB_API_TARGET || 'http://127.0.0.1:5000';

export default defineConfig(({ command }) => ({
  plugins: [vue()],
  base: command === 'build' ? '/static/spa/' : '/',
  build: {
    outDir: fileURLToPath(new URL('../static/spa', import.meta.url)),
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '^/t/[^/]+/api(?:/|$)': apiTarget,
      '/api': apiTarget,
      '/static': { target: apiTarget },
    },
  },
  test: { environment: 'jsdom', include: ['tests/**/*.test.js'] },
}));
