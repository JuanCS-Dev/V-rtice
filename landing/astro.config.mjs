// @ts-check
import { defineConfig } from 'astro/config';

import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://vertice-maximus.com',

  integrations: [react()],

  vite: {
    plugins: [tailwindcss()]
  },

  // Build optimizations
  build: {
    inlineStylesheets: 'auto',
  },

  // Compression
  compressHTML: true,

  // Performance
  prefetch: {
    defaultStrategy: 'viewport',
  },
});