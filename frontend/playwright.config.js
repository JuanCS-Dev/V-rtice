/**
 * Playwright E2E Testing Configuration
 *
 * Configuração para testes end-to-end do Vértice Frontend.
 * Testa os 3 dashboards subordinados: PENELOPE, MABA, MVP.
 *
 * Constituição Vértice v3.0 - Artigo II, Seção 2:
 * "Teste de cobertura ≥90% obrigatório"
 *
 * Author: Vértice Platform Team
 * License: Proprietary
 */

import { defineConfig, devices } from '@playwright/test';

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',

  // Timeout para cada teste (30 segundos)
  timeout: 30 * 1000,

  // Retry em caso de falha (flaky tests)
  retries: process.env.CI ? 2 : 0,

  // Workers paralelos (1 em CI para estabilidade)
  workers: process.env.CI ? 1 : undefined,

  // Reporter (verbose localmente, github-actions em CI)
  reporter: process.env.CI ? 'github' : 'list',

  // Configurações compartilhadas para todos os projetos
  use: {
    // Base URL do frontend (Vite dev server)
    baseURL: 'http://localhost:5173',

    // Trace em falhas (para debug)
    trace: 'on-first-retry',

    // Screenshot em falhas
    screenshot: 'only-on-failure',

    // Video em falhas
    video: 'retain-on-failure',

    // Viewport padrão
    viewport: { width: 1280, height: 720 },
  },

  // Projetos de teste (browsers)
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // Teste mobile (opcional)
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
  ],

  // Dev server (iniciar Vite automaticamente)
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
