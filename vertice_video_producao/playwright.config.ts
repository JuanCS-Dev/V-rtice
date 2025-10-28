import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration for Vértice Video Production
 * 
 * Official docs: https://playwright.dev/docs/test-configuration
 * Video recording: https://playwright.dev/docs/videos
 */

export default defineConfig({
  testDir: './',
  
  // Timeout para testes longos (tour de 3 minutos)
  timeout: 240_000, // 4 minutos (margem de segurança)
  
  // Executar testes em sequência (não paralelo)
  fullyParallel: false,
  workers: 1,
  
  // Reporter
  reporter: [
    ['list'],
    ['html', { open: 'never' }]
  ],
  
  use: {
    // Base URL
    baseURL: 'http://localhost:5173',
    
    // Video recording (conforme docs oficiais)
    // Ref: https://playwright.dev/docs/videos
    video: {
      mode: 'on', // Sempre gravar ('on' | 'off' | 'retain-on-failure' | 'on-first-retry')
      size: { width: 1920, height: 1080 } // Full HD
    },
    
    // Screenshot apenas em falhas
    screenshot: 'only-on-failure',
    
    // Trace para debug
    trace: 'retain-on-failure',
    
    // Navegação
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },

  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
    },
  ],
  
  // Servidor web NÃO é iniciado automaticamente
  // (deve estar rodando externamente: npm run dev)
  webServer: undefined,
});

