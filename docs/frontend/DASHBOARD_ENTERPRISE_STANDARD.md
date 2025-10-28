# 🏢 VÉRTICE DASHBOARD ENTERPRISE STANDARD

## 📋 OBJETIVO

Unificar TODAS as 9 dashboards do sistema sob um padrão Enterprise consistente, modular e tema-agnóstico.

---

## 🎯 PADRÃO ENTERPRISE UNIFICADO

### **Estrutura Obrigatória**

```jsx
<div className={styles.dashboard}>
  {/* Skip Link (acessibilidade) */}
  <SkipLink href="#main-content">{t('accessibility.skipToMain')}</SkipLink>

  {/* HEADER: Logo, Status, Clock, Nav, Actions */}
  <Header
    currentTime={currentTime}
    onBack={() => setCurrentView('main')}
    activeModule={activeModule}
    modules={modules}
    onModuleChange={setActiveModule}
  />

  {/* MAIN CONTENT */}
  <main id="main-content" className={styles.mainContent}>
    {/* Conteúdo específico da dashboard */}
  </main>

  {/* FOOTER (opcional): Status bar com métricas */}
  <Footer metrics={metrics} />
</div>
```

### **CSS Module Obrigatório**

**Arquivo:** `[Dashboard]Name.module.css`

```css
.dashboard {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--dashboard-bg);
  color: var(--color-text-primary);
}

.mainContent {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
}
```

### **Variáveis CSS Tema-Agnósticas**

**PROIBIDO:**
```jsx
❌ className="bg-gradient-to-br from-gray-900 via-black to-gray-800 text-yellow-400"
❌ className="text-purple-400 bg-purple-900"
```

**OBRIGATÓRIO:**
```jsx
✅ className={styles.dashboard}
✅ className={styles.header}
✅ className={styles.statusCard}
```

```css
/* CSS Module */
.dashboard {
  background: var(--dashboard-bg);
  color: var(--dashboard-text-color);
}

.header {
  background: var(--header-bg-gradient);
  border-bottom: var(--header-border-bottom);
}
```

---

## 📐 COMPONENTES REUTILIZÁVEIS

### **1. Header Pattern**

Cada dashboard deve ter um Header específico mas seguindo o mesmo layout:

**Exemplo:** `MaximusHeader.jsx` (já implementado como referência)

```jsx
<header className={styles.header}>
  <div className={styles.topBar}>
    {/* Logo & Branding */}
    <div className={styles.branding}>
      <div className={styles.logoContainer}>{icon}</div>
      <div className={styles.logoText}>
        <h1 className={styles.logoTitle}>{title}</h1>
        <p className={styles.logoSubtitle}>{subtitle}</p>
      </div>
    </div>

    {/* Status Indicators (opcional) */}
    <div className={styles.statusIndicators}>
      {/* Status cards */}
    </div>

    {/* Actions: Clock, Theme, Language, Back */}
    <div className={styles.actions}>
      <Clock time={currentTime} />
      <CompactLanguageSelector />
      <CompactThemeSelector />
      <BackButton onClick={onBack} />
    </div>
  </div>

  {/* Navigation Bar (se houver módulos) */}
  <div className={styles.navBar}>
    {modules.map(module => (
      <button
        key={module.id}
        className={`${styles.navButton} ${isActive ? styles.active : styles.inactive}`}
        onClick={() => onModuleChange(module.id)}
      >
        <span className={styles.navIcon}>{module.icon}</span>
        <span className={styles.navLabel}>{module.name}</span>
      </button>
    ))}
  </div>
</header>
```

### **2. Footer Pattern**

```jsx
<footer className={styles.footer}>
  <div className={styles.footerStatus}>
    <StatusItem label="System" value="ONLINE" />
    <StatusItem label="Metrics" value={metrics.count} />
  </div>
  <div className={styles.footerBrand}>
    {brandText}
  </div>
</footer>
```

---

## 🎨 TEMA ENTERPRISE

### **Variáveis Obrigatórias**

Todas as dashboards devem usar estas variáveis (já definidas em `enterprise.css` e `default.css`):

```css
/* Dashboard */
--dashboard-bg
--dashboard-text-color

/* Header */
--header-bg-gradient
--header-border-bottom
--header-shadow
--logo-gradient
--logo-shadow
--title-gradient

/* Status */
--status-bg
--status-border
--status-online-color
--status-offline-color
--status-idle-color

/* Navigation */
--nav-bg
--nav-button-active-bg
--nav-button-active-border
--nav-button-inactive-bg
--nav-button-hover-bg

/* Footer */
--footer-bg
--footer-border

/* Colors */
--color-text-primary
--color-text-secondary
--color-text-muted
--color-accent-primary
```

### **Cores Específicas por Dashboard**

Cada dashboard pode ter suas próprias cores, mas devem ser definidas como variáveis:

**AdminDashboard:**
```css
:root[data-dashboard="admin"] {
  --dashboard-primary: #ffb900;  /* Amarelo */
  --dashboard-accent: #f59e0b;
}
```

**OSINTDashboard:**
```css
:root[data-dashboard="osint"] {
  --dashboard-primary: #8B5CF6;  /* Roxo */
  --dashboard-accent: #a78bfa;
}
```

---

## ✅ CHECKLIST DE PADRONIZAÇÃO

Para cada dashboard, verificar:

- [ ] CSS Module criado (`[Dashboard].module.css`)
- [ ] Tailwind hardcoded removido
- [ ] Variáveis CSS usadas (não valores fixos)
- [ ] Header componentizado
- [ ] Footer componentizado (se aplicável)
- [ ] Skip Link implementado
- [ ] i18n completo
- [ ] Acessibilidade (ARIA labels)
- [ ] Responsivo (mobile-first)
- [ ] Tema Enterprise funcional
- [ ] Tema Matrix funcional

---

## 🚀 PLANO DE AÇÃO

### **Fase 1: AdminDashboard**
1. Criar `AdminDashboard.module.css`
2. Criar `AdminHeader.jsx` + `.module.css`
3. Remover Tailwind hardcoded
4. Aplicar variáveis CSS

### **Fase 2: OSINTDashboard**
1. Criar `OSINTDashboard.module.css`
2. Criar `OSINTHeader.jsx` + `.module.css`
3. Remover Tailwind hardcoded
4. Aplicar variáveis CSS

### **Fase 3: MaximusDashboard**
1. Converter `MaximusDashboard.css` → `.module.css`
2. Aplicar variáveis CSS
3. Garantir tema Enterprise

### **Fase 4: DefensiveDashboard**
1. Converter `dashboards.css` → `DefensiveDashboard.module.css`
2. Aplicar variáveis CSS
3. Garantir tema Enterprise

### **Fase 5-7: CyberDashboard, TerminalDashboard (verificar)**
1. Analisar estado atual
2. Aplicar padrão se necessário

### **Fase 8: Validação Final**
1. Build test
2. Teste visual em Matrix theme
3. Teste visual em Enterprise theme
4. Teste responsividade
5. Teste acessibilidade

---

## 📊 MÉTRICAS DE SUCESSO

- ✅ 9/9 dashboards usando CSS Modules
- ✅ 0 Tailwind hardcoded
- ✅ 100% variáveis CSS
- ✅ 2 temas funcionais (Matrix + Enterprise)
- ✅ Build sem erros
- ✅ Consistência visual total

---

**Status:** DOCUMENTO CRIADO - AGUARDANDO IMPLEMENTAÇÃO
**Prioridade:** ALTA
**Estimativa:** ~3-4 horas de trabalho
