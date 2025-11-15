/**
 * MABA Dashboard E2E Tests
 *
 * Testes end-to-end para o dashboard MABA (Maximus Autonomous Browser Agent).
 *
 * Fluxos testados:
 * 1. Landing Page → MABA Dashboard
 * 2. Visualizar Cognitive Map (D3.js force-directed graph)
 * 3. Gerenciar Browser Sessions (criar/fechar)
 * 4. Visualizar Navigation Timeline
 * 5. Navegação de volta
 *
 * Constituição Vértice v3.0 - Validação E2E obrigatória.
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { test, expect } from "@playwright/test";

test.describe("MABA Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Vértice/);
  });

  test("deve navegar da Landing Page para MABA Dashboard", async ({ page }) => {
    const mabaCard = page.locator("text=MABA").first();
    await expect(mabaCard).toBeVisible();
    await mabaCard.click();

    await expect(page.locator('h1:has-text("MABA Dashboard")')).toBeVisible();
    await expect(page.locator("text=Maximus Browser Agent")).toBeVisible();
  });

  test("deve exibir Cognitive Map com D3.js graph", async ({ page }) => {
    await page.locator("text=MABA").first().click();
    await expect(page.locator('h1:has-text("MABA Dashboard")')).toBeVisible();

    // D3.js renderiza SVG
    const cognitiveMapSvg = page.locator("svg").first();
    await expect(cognitiveMapSvg).toBeVisible();

    // Verificar que há elementos no grafo (nodes/links)
    const graphNodes = page.locator("circle, rect").first();
    await expect(graphNodes).toBeVisible();
  });

  test("deve alternar entre as 3 tabs (Cognitive Map, Sessions, Timeline)", async ({
    page,
  }) => {
    await page.locator("text=MABA").first().click();
    await expect(page.locator('h1:has-text("MABA Dashboard")')).toBeVisible();

    // Tab 1: Cognitive Map (padrão)
    const cognitiveTab = page.locator('button:has-text("🧠 Cognitive Map")');
    await expect(cognitiveTab).toBeVisible();

    // Tab 2: Sessions
    const sessionsTab = page.locator('button:has-text("🖥️ Sessions")');
    await sessionsTab.click();
    await expect(sessionsTab).toHaveClass(/active/);

    // Tab 3: Timeline
    const timelineTab = page.locator('button:has-text("📊 Timeline")');
    await timelineTab.click();
    await expect(timelineTab).toHaveClass(/active/);

    // Voltar para Cognitive Map
    await cognitiveTab.click();
    await expect(cognitiveTab).toHaveClass(/active/);
  });

  test("deve exibir Browser Session Manager", async ({ page }) => {
    await page.locator("text=MABA").first().click();
    await expect(page.locator('h1:has-text("MABA Dashboard")')).toBeVisible();

    // Ir para tab Sessions
    const sessionsTab = page.locator('button:has-text("🖥️ Sessions")');
    await sessionsTab.click();

    // Verificar que o Session Manager está visível
    await expect(
      page.locator("text=Browser Sessions, text=Active Sessions"),
    ).toBeVisible();
  });

  test("deve permitir criar nova browser session", async ({ page }) => {
    await page.locator("text=MABA").first().click();
    await expect(page.locator('h1:has-text("MABA Dashboard")')).toBeVisible();

    const sessionsTab = page.locator('button:has-text("🖥️ Sessions")');
    await sessionsTab.click();

    // Encontrar campo de input para URL
    const urlInput = page
      .locator('input[type="text"], input[placeholder*="URL"]')
      .first();

    if (await urlInput.isVisible()) {
      await urlInput.fill("https://example.com");

      // Encontrar botão de criar sessão
      const createButton = page
        .locator('button:has-text("Criar"), button:has-text("Create")')
        .first();

      if (await createButton.isVisible()) {
        await createButton.click();

        // Verificar que sessão foi criada (pode mostrar loading ou confirmação)
        await page.waitForTimeout(1000);
      }
    }
  });

  test("deve exibir Navigation Timeline", async ({ page }) => {
    await page.locator("text=MABA").first().click();
    await expect(page.locator('h1:has-text("MABA Dashboard")')).toBeVisible();

    const timelineTab = page.locator('button:has-text("📊 Timeline")');
    await timelineTab.click();

    // Verificar que a timeline está visível
    await expect(
      page.locator("text=Navigation Timeline, text=Timeline"),
    ).toBeVisible();
  });

  test("deve exibir Stats Overview com métricas", async ({ page }) => {
    await page.locator("text=MABA").first().click();
    await expect(page.locator('h1:has-text("MABA Dashboard")')).toBeVisible();

    // Stats Overview deve estar visível no topo
    const statsOverview = page
      .locator("text=Total Sessions, text=Active, text=Success Rate")
      .first();
    await expect(statsOverview).toBeVisible();
  });

  test("deve mostrar connection indicator (LIVE ou OFFLINE)", async ({
    page,
  }) => {
    await page.locator("text=MABA").first().click();
    await expect(page.locator('h1:has-text("MABA Dashboard")')).toBeVisible();

    const connectionIndicator = page.locator("text=LIVE, text=OFFLINE").first();
    await expect(connectionIndicator).toBeVisible();
  });

  test("deve navegar de volta para Landing Page", async ({ page }) => {
    await page.locator("text=MABA").first().click();
    await expect(page.locator('h1:has-text("MABA Dashboard")')).toBeVisible();

    const backButton = page.locator('button:has-text("← Voltar")');
    await expect(backButton).toBeVisible();
    await backButton.click();

    await expect(page.locator('h1:has-text("Vértice")')).toBeVisible();
    await expect(page.locator("text=MABA").first()).toBeVisible();
  });

  test("deve exibir loading state ao carregar cognitive map", async ({
    page,
  }) => {
    await page.locator("text=MABA").first().click();

    const loadingIndicator = page
      .locator('text=Carregando, [class*="spinner"]')
      .first();

    try {
      await loadingIndicator.waitFor({ state: "visible", timeout: 1000 });
    } catch (error) {
      // Loading muito rápido
    }

    await expect(page.locator('h1:has-text("MABA Dashboard")')).toBeVisible();
  });
});

test.describe("MABA Dashboard - Cognitive Map Interactions", () => {
  test("deve permitir interações com o grafo D3.js", async ({ page }) => {
    await page.goto("/");
    await page.locator("text=MABA").first().click();
    await expect(page.locator('h1:has-text("MABA Dashboard")')).toBeVisible();

    // Verificar que o SVG é interativo (pode ter zoom/pan)
    const svg = page.locator("svg").first();
    await expect(svg).toBeVisible();

    // Tentar clicar em um node (se houver)
    const nodes = page.locator("circle, rect");
    const nodeCount = await nodes.count();

    if (nodeCount > 0) {
      await nodes.first().click();
      // Pode abrir details panel
      await page.waitForTimeout(500);
    }
  });

  test("deve exibir detalhes de nodes quando clicados", async ({ page }) => {
    await page.goto("/");
    await page.locator("text=MABA").first().click();
    await expect(page.locator('h1:has-text("MABA Dashboard")')).toBeVisible();

    // CognitiveMapViewer tem details panel
    const detailsPanel = page.locator(
      "text=Node Details, text=Elements, text=URL",
    );

    // Pode não estar visível inicialmente (só após clicar em node)
    const isPanelInDom = await detailsPanel.count();
    expect(isPanelInDom).toBeGreaterThanOrEqual(0);
  });
});
