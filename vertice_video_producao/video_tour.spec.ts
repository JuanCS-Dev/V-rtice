import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * VÉRTICE - Playwright Video Tour (v4.0 FINAL - Constitution Compliant)
 * 
 * Baseado em:
 * - roteiro_FINAL.json (alinhado com VERTICE_ARCHITECTURE_POSTER.pdf)
 * - Frontend real: ModuleGrid.jsx com data-testid="nav-{module}-dashboard"
 * - Documentação oficial Playwright: https://playwright.dev/docs/videos
 */

test('Vértice Frontend Tour - Production Recording (180s)', async ({ page }) => {
  console.log('🎬 VÉRTICE VIDEO PRODUCTION - START\n');
  
  const roteiro = JSON.parse(
    fs.readFileSync(path.join(__dirname, 'roteiro_v4_english_final.json'), 'utf-8')
  );
  
  await page.setViewportSize({ width: 1920, height: 1080 });
  
  // Helper: Wait exact scene duration
  const waitScene = (duration: number) => page.waitForTimeout(duration * 1000);
  
  // Helper: Navigate like a real user - simple clicks
  const navigateToModule = async (moduleId: string) => {
    try {
      console.log(`🔄 Clicking ${moduleId} module...`);
      
      // Simple approach: find ANY clickable element with the module name
      const moduleText = moduleId.toUpperCase();
      
      // Try multiple selectors in order of preference
      const selectors = [
        `[data-testid="nav-${moduleId}-dashboard"]`,
        `.module-card:has-text("${moduleText}")`,
        `text=${moduleText}`,
        `text="${moduleId}"`,
        `*:has-text("${moduleText}")`
      ];
      
      for (const selector of selectors) {
        try {
          const element = page.locator(selector).first();
          if (await element.count() > 0) {
            await element.click({ timeout: 3000 });
            await page.waitForTimeout(2000);
            console.log(`✅ Clicked ${moduleId} using: ${selector}`);
            return;
          }
        } catch (e) {
          // Try next selector
        }
      }
      
      console.warn(`⚠️  Could not find ${moduleId}, continuing...`);
      
    } catch (error) {
      console.warn(`⚠️  Navigation failed: ${error.message}`);
    }
  };
  
  // Helper: Return to homepage
  const goHome = async () => {
    if (page.url() !== 'http://localhost:5173/') {
      await page.goto('http://localhost:5173', { waitUntil: 'networkidle', timeout: 10000 });
    }
  };
  
  try {
    // ====================================================================
    // CENA 1: Landing Page Intro (18s)
    // ====================================================================
    console.log('📍 Scene 1: Landing Page (18s)');
    await page.goto('http://localhost:5173', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    // Wait for page to load - ANY content
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    await page.waitForTimeout(3000); // Let React fully render
    
    console.log('✅ Page loaded, starting navigation tour');
    
    // Smooth scroll to showcase modules
    await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
    await waitScene(6);
    await page.evaluate(() => window.scrollTo({ top: 800, behavior: 'smooth' }));
    await waitScene(6);
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await waitScene(6);
    
    // ====================================================================
    // CENA 2: MAXIMUS Dashboard (18s)
    // ====================================================================
    console.log('📍 Scene 2: MAXIMUS AI (18s)');
    await navigateToModule('maximus');
    
    // Explore MAXIMUS dashboard content
    await page.evaluate(() => window.scrollTo({ top: 300, behavior: 'smooth' }));
    await waitScene(9);
    await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'smooth' }));
    await waitScene(9);
    
    // ====================================================================
    // CENA 3: MAXIMUS Features Exploration (17s)
    // ====================================================================
    console.log('📍 Scene 3: MAXIMUS Features (17s)');
    await page.evaluate(() => window.scrollTo({ top: 500, behavior: 'smooth' }));
    await waitScene(8);
    await page.evaluate(() => window.scrollTo({ top: 1000, behavior: 'smooth' }));
    await waitScene(9);
    
    // ====================================================================
    // CENA 4: Offensive Dashboard (16s)
    // ====================================================================
    console.log('📍 Scene 4: Offensive Intelligence (16s)');
    await navigateToModule('offensive');
    
    // Show offensive dashboard content
    await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
    await waitScene(8);
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await waitScene(8);
    
    // ====================================================================
    // CENA 5: Offensive Modules Exploration (16s)
    // ====================================================================
    console.log('📍 Scene 5: Offensive Operations (16s)');
    await page.evaluate(() => window.scrollTo({ top: 800, behavior: 'smooth' }));
    await waitScene(8);
    await page.evaluate(() => window.scrollTo({ top: 1200, behavior: 'smooth' }));
    await waitScene(8);
    
    // ====================================================================
    // CENA 6: Defensive Dashboard (15s)
    // ====================================================================
    console.log('📍 Scene 6: Defensive Intelligence (15s)');
    await navigateToModule('defensive');
    
    // Show defensive capabilities
    await page.evaluate(() => window.scrollTo({ top: 500, behavior: 'smooth' }));
    await waitScene(15);
    
    // ====================================================================
    // CENA 7: Defensive Metrics Exploration (16s)
    // ====================================================================
    console.log('📍 Scene 7: Defensive Metrics (16s)');
    await page.evaluate(() => window.scrollTo({ top: 500, behavior: 'smooth' }));
    await waitScene(8);
    await page.evaluate(() => window.scrollTo({ top: 1000, behavior: 'smooth' }));
    await waitScene(8);
    
    // ====================================================================
    // CENA 8: Purple Team Dashboard (15s)
    // ====================================================================
    console.log('📍 Scene 8: Purple Team Operations (15s)');
    await navigateToModule('purple');
    await waitScene(15);
    
    // ====================================================================
    // CENA 9: Cockpit Soberano (16s)
    // ====================================================================
    console.log('📍 Scene 9: Cockpit Soberano (16s)');
    await navigateToModule('cockpit');
    await waitScene(16);
    
    // ====================================================================
    // CENA 10: OSINT Dashboard (16s)
    // ====================================================================
    console.log('📍 Scene 10: OSINT Intelligence (16s)');
    await navigateToModule('osint');
    await waitScene(16);
    
    // ====================================================================
    // CENA 11: Finale - Return Home (17s)
    // ====================================================================
    console.log('📍 Scene 11: Finale (17s)');
    await goHome();
    
    // Epic finale scroll
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await waitScene(4);
    await page.evaluate(() => window.scrollTo({ top: 1000, behavior: 'smooth' }));
    await waitScene(4);
    await page.evaluate(() => window.scrollTo({ top: 2000, behavior: 'smooth' }));
    await waitScene(4);
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await waitScene(5);
    
    console.log('\n✅ VIDEO RECORDING COMPLETE - 180s captured');
    
  } catch (error) {
    console.error('❌ RECORDING FAILED:', error);
    await page.screenshot({ 
      path: 'test-results/error-screenshot.png',
      fullPage: true
    });
    throw error;
  }
});

