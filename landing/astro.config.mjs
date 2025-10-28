// @ts-check
import { defineConfig } from 'astro/config';

import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://vertice-maximus.com',

  integrations: [react()],

  vite: {
    plugins: [tailwindcss()],
    build: {
      // Chunk splitting strategy for better caching
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            // Separate vendor libraries
            if (id.includes('node_modules')) {
              // GSAP in separate chunk
              if (id.includes('gsap')) {
                return 'gsap';
              }
              // D3 in separate chunk
              if (id.includes('d3-')) {
                return 'd3';
              }
              // React in separate chunk
              if (id.includes('react')) {
                return 'react-vendor';
              }
              // Other vendor code
              return 'vendor';
            }
          }
        }
      },
      // Minification settings
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: true, // Remove console.logs in production
          drop_debugger: true,
          pure_funcs: ['console.log', 'console.info', 'console.debug']
        }
      }
    }
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