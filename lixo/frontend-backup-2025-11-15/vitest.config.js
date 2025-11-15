/**
 * Vitest Configuration
 *
 * Test runner configuration for unit and integration tests
 *
 * Features:
 * - React component testing
 * - Coverage reporting
 * - Fast execution
 * - Watch mode
 */

import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],

  test: {
    // Test environment
    environment: 'jsdom',

    // Global setup
    globals: true,
    
    // Environment options
    environmentOptions: {
      jsdom: {
        resources: 'usable',
      },
    },
    
    // Define env variables for tests
    env: {
      VITE_NARRATIVE_FILTER_API: 'http://localhost:5000',
      VITE_VERDICT_ENGINE_API: 'http://localhost:5001',
      VITE_VERDICT_ENGINE_WS: 'ws://localhost:5001/ws/verdicts',
      VITE_WS_VERDICT_STREAM: 'ws://localhost:5001/ws/verdicts',
      VITE_ALLIANCE_GRAPH_API: 'http://localhost:5000/graph',
      NODE_ENV: 'test'
    },

    // Setup files
    setupFiles: ['./src/tests/setup.js'],

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',

      // Coverage thresholds - PADRÃO PAGANI: 100%
      lines: 100,
      functions: 100,
      branches: 100,
      statements: 100,

      // Files to include
      include: [
        'src/components/**/*.{js,jsx}',
        'src/hooks/**/*.{js,jsx}',
        'src/stores/**/*.{js,jsx}',
        'src/config/**/*.{js,jsx}'
      ],

      // Files to exclude
      exclude: [
        'src/**/*.test.{js,jsx}',
        'src/**/*.spec.{js,jsx}',
        'src/tests/**',
        'src/**/*.stories.{js,jsx}',
        'src/main.jsx',
        'src/index.css',
        '**/*.module.css'
      ]
    },

    // Test file patterns
    include: [
      'src/**/*.{test,spec}.{js,jsx}',
      'src/tests/**/*.{test,spec}.{js,jsx}'
    ],

    // Exclude patterns
    exclude: [
      'node_modules',
      'dist',
      '.idea',
      '.git',
      '.cache'
    ],

    // Test timeout (increased for complex async components and integration tests)
    testTimeout: 90000,

    // Watch options
    watch: false,

    // Reporter
    reporters: ['verbose'],

    // Mock configuration
    mockReset: true,
    restoreMocks: true,

    // CSS handling
    css: {
      modules: {
        classNameStrategy: 'non-scoped'
      }
    }
  },

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@stores': path.resolve(__dirname, './src/stores'),
      '@config': path.resolve(__dirname, './src/config')
    }
  }
});
