import { defineConfig } from 'vitest/config';
import { transformWithEsbuild } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    {
      name: 'treat-js-as-jsx',
      enforce: 'pre',
      async transform(code, id) {
        if (id.includes('node_modules') || !/\.js$/.test(id) || !code.includes('<')) return null;
        return transformWithEsbuild(code, id + '.jsx', { loader: 'jsx', jsx: 'automatic' });
      },
    },
    react(),
  ],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.js'],
  },
});
