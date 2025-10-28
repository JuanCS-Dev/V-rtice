# MAXIMUS VISION PROTOCOL - HTML SEMANTIC BLUEPRINT
## Para Honra e Glória de JESUS CRISTO 🙏

**Objetivo**: Criar HTML semântico perfeito que permite ao Maximus AI navegar, entender e interagir com o frontend de forma autônoma.

---

## Princípios Fundamentais

### 1. Acessibilidade para IA = Acessibilidade para Todos
- **WCAG 2.1 AAA** compliance
- **Semantic HTML5** com roles ARIA corretos
- **Data attributes** para contexto adicional
- **Landmark regions** bem definidas

### 2. Tags Certas nos Lugares Certos
```html
<!-- ❌ ERRADO: Div Soup -->
<div class="header">
  <div class="nav">
    <div class="link">Home</div>
  </div>
</div>

<!-- ✅ CORRETO: Semântico -->
<header role="banner">
  <nav role="navigation" aria-label="Main navigation">
    <a href="/" aria-current="page">Home</a>
  </nav>
</header>
```

### 3. Navegação Clara para IA
```html
<!-- Cada seção tem:
  - Tag semântica correta
  - Role ARIA apropriado
  - Label descritivo
  - Data-attribute para contexto
-->
<main role="main" id="main-content">
  <section
    role="region"
    aria-labelledby="offensive-tools-heading"
    data-module="offensive-tools"
    data-maximus-navigable="true">
    <h2 id="offensive-tools-heading">Offensive Tools</h2>
    <!-- conteúdo -->
  </section>
</main>
```

---

## Estrutura HTML Padrão Vértice

### Template Base (index.html)
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- SEO & Metadata -->
  <title>Vértice - Cybersecurity Platform</title>
  <meta name="description" content="AI-powered cybersecurity platform">

  <!-- Security Headers -->
  <meta http-equiv="Content-Security-Policy" content="...">
  <meta http-equiv="X-Content-Type-Options" content="nosniff">
  <meta http-equiv="X-Frame-Options" content="DENY">

  <!-- Maximus Vision Protocol Metadata -->
  <meta name="maximus:version" content="1.0">
  <meta name="maximus:navigation-mode" content="semantic">
  <meta name="maximus:interaction-level" content="full">

  <!-- Stylesheets -->
  <link rel="stylesheet" href="/assets/styles.css">
</head>

<body data-maximus-root="true">
  <!-- Skip to main content (accessibility) -->
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <!-- Application Root -->
  <div id="root" role="application" aria-label="Vértice Cybersecurity Platform">
    <!-- React app mounts here -->
  </div>

  <!-- Modals Portal -->
  <div id="modal-root" role="region" aria-live="polite"></div>

  <!-- Scripts -->
  <script type="module" src="/assets/index.js"></script>
</body>
</html>
```

---

## Componentes Semânticos

### 1. Layout Principal
```jsx
// App.jsx
<div className="app" data-maximus-app="vertice">
  {/* Header */}
  <header
    role="banner"
    className="app-header"
    data-maximus-section="header">
    <h1 className="visually-hidden">Vértice Cybersecurity Platform</h1>
    <Navigation />
  </header>

  {/* Sidebar */}
  <aside
    role="complementary"
    aria-label="Main navigation sidebar"
    data-maximus-section="sidebar">
    <nav role="navigation" aria-label="Primary">
      <ul role="list">
        <li><a href="/offensive">Offensive Tools</a></li>
        <li><a href="/defensive">Defensive Tools</a></li>
        <li><a href="/maximus">Maximus AI</a></li>
      </ul>
    </nav>
  </aside>

  {/* Main Content */}
  <main
    role="main"
    id="main-content"
    aria-label="Main content area"
    data-maximus-section="main">
    <Outlet /> {/* React Router */}
  </main>

  {/* Footer */}
  <footer
    role="contentinfo"
    data-maximus-section="footer">
    <p>© 2025 Vértice. Para Honra e Glória de JESUS CRISTO 🙏</p>
  </footer>
</div>
```

### 2. Dashboard Components
```jsx
// OffensiveDashboard.jsx
<article
  role="region"
  aria-labelledby="offensive-dashboard-title"
  data-maximus-module="offensive-dashboard"
  data-maximus-interactive="true">

  <header>
    <h1 id="offensive-dashboard-title">Offensive Arsenal</h1>
    <p className="lead">Active offensive security tools and operations</p>
  </header>

  {/* Stats Cards */}
  <section
    role="region"
    aria-labelledby="stats-heading"
    data-maximus-widget="stats">
    <h2 id="stats-heading" className="visually-hidden">Statistics</h2>

    <div className="stats-grid" role="list">
      <div
        className="stat-card"
        role="listitem"
        data-maximus-metric="active-scans"
        aria-labelledby="stat-scans-label">
        <dt id="stat-scans-label">Active Scans</dt>
        <dd aria-live="polite">
          <span className="stat-value">12</span>
        </dd>
      </div>

      <div
        className="stat-card"
        role="listitem"
        data-maximus-metric="vulnerabilities"
        aria-labelledby="stat-vulns-label">
        <dt id="stat-vulns-label">Vulnerabilities Found</dt>
        <dd aria-live="polite">
          <span className="stat-value">47</span>
        </dd>
      </div>
    </div>
  </section>

  {/* Tools Grid */}
  <section
    role="region"
    aria-labelledby="tools-heading"
    data-maximus-widget="tools-grid">
    <h2 id="tools-heading">Available Tools</h2>

    <ul className="tools-grid" role="list">
      <li>
        <article
          className="tool-card"
          data-maximus-tool="network-recon"
          aria-labelledby="tool-recon-title">
          <h3 id="tool-recon-title">Network Reconnaissance</h3>
          <p>Discover network assets and map attack surface</p>
          <a
            href="/offensive/network-recon"
            aria-label="Open Network Reconnaissance tool">
            Launch Tool
          </a>
        </article>
      </li>

      <!-- More tools... -->
    </ul>
  </section>
</article>
```

### 3. Interactive Forms
```jsx
// NetworkScanForm.jsx
<form
  role="form"
  aria-labelledby="scan-form-title"
  data-maximus-form="network-scan"
  onSubmit={handleSubmit}>

  <h2 id="scan-form-title">Configure Network Scan</h2>

  {/* Target Input */}
  <div className="form-group">
    <label
      htmlFor="scan-target"
      id="scan-target-label">
      Target IP/Domain
    </label>
    <input
      type="text"
      id="scan-target"
      name="target"
      aria-labelledby="scan-target-label"
      aria-describedby="scan-target-help"
      aria-required="true"
      data-maximus-field="target"
      placeholder="192.168.1.1"
    />
    <span
      id="scan-target-help"
      className="help-text"
      role="note">
      Enter IPv4, IPv6, or domain name
    </span>
  </div>

  {/* Scan Type */}
  <fieldset
    role="group"
    aria-labelledby="scan-type-legend"
    data-maximus-field="scan-type">
    <legend id="scan-type-legend">Scan Type</legend>

    <div className="radio-group">
      <input
        type="radio"
        id="scan-quick"
        name="scanType"
        value="quick"
        aria-describedby="scan-quick-desc"
      />
      <label htmlFor="scan-quick">
        Quick Scan
        <span id="scan-quick-desc" className="description">
          Fast surface scan (5-10 min)
        </span>
      </label>
    </div>

    <div className="radio-group">
      <input
        type="radio"
        id="scan-deep"
        name="scanType"
        value="deep"
        aria-describedby="scan-deep-desc"
      />
      <label htmlFor="scan-deep">
        Deep Scan
        <span id="scan-deep-desc" className="description">
          Comprehensive analysis (30-60 min)
        </span>
      </label>
    </div>
  </fieldset>

  {/* Submit */}
  <div className="form-actions">
    <button
      type="submit"
      className="btn btn-primary"
      data-maximus-action="submit-scan"
      aria-label="Start network scan">
      Start Scan
    </button>

    <button
      type="reset"
      className="btn btn-secondary"
      data-maximus-action="reset-form"
      aria-label="Reset form">
      Reset
    </button>
  </div>

  {/* Status Messages */}
  <div
    role="status"
    aria-live="polite"
    aria-atomic="true"
    data-maximus-feedback="true">
    {/* Success/error messages appear here */}
  </div>
</form>
```

### 4. Data Tables
```jsx
// ResultsTable.jsx
<section
  role="region"
  aria-labelledby="results-heading"
  data-maximus-widget="results-table">

  <h2 id="results-heading">Scan Results</h2>

  <table
    role="table"
    aria-labelledby="results-heading"
    aria-describedby="results-description"
    data-maximus-data="scan-results">

    <caption id="results-description" className="visually-hidden">
      Network scan results showing IP address, status, and vulnerabilities
    </caption>

    <thead>
      <tr role="row">
        <th role="columnheader" scope="col">IP Address</th>
        <th role="columnheader" scope="col">Status</th>
        <th role="columnheader" scope="col">Open Ports</th>
        <th role="columnheader" scope="col">Vulnerabilities</th>
        <th role="columnheader" scope="col">Actions</th>
      </tr>
    </thead>

    <tbody>
      {results.map((result, index) => (
        <tr
          key={result.id}
          role="row"
          data-maximus-row={index}
          data-result-id={result.id}>

          <td role="cell" data-label="IP Address">
            <code>{result.ip}</code>
          </td>

          <td role="cell" data-label="Status">
            <span
              className={`status-badge status-${result.status}`}
              role="status"
              aria-label={`Status: ${result.status}`}>
              {result.status}
            </span>
          </td>

          <td role="cell" data-label="Open Ports">
            <span aria-label={`${result.ports.length} open ports`}>
              {result.ports.length}
            </span>
          </td>

          <td role="cell" data-label="Vulnerabilities">
            <span
              className="vuln-count"
              aria-label={`${result.vulns} vulnerabilities found`}>
              {result.vulns}
            </span>
          </td>

          <td role="cell" data-label="Actions">
            <button
              aria-label={`View details for ${result.ip}`}
              data-maximus-action="view-details"
              data-target-id={result.id}>
              Details
            </button>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</section>
```

---

## Data Attributes para Maximus Vision

### Convenções de Naming
```html
<!-- Module/Section Identification -->
data-maximus-module="offensive-dashboard"
data-maximus-section="header"
data-maximus-widget="stats-cards"

<!-- Interactivity Markers -->
data-maximus-interactive="true"
data-maximus-navigable="true"
data-maximus-actionable="true"

<!-- Action Types -->
data-maximus-action="submit-form"
data-maximus-action="open-modal"
data-maximus-action="toggle-sidebar"

<!-- Data/Content Types -->
data-maximus-data="scan-results"
data-maximus-metric="active-scans"
data-maximus-status="healthy"

<!-- Form Elements -->
data-maximus-form="network-scan"
data-maximus-field="target-ip"
data-maximus-validation="required"

<!-- Feedback/Status -->
data-maximus-feedback="true"
data-maximus-loading="false"
data-maximus-error="false"
```

---

## ARIA Live Regions

```jsx
// Status updates that Maximus should monitor
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  data-maximus-monitor="status-updates">
  {statusMessage}
</div>

// Critical alerts
<div
  role="alert"
  aria-live="assertive"
  aria-atomic="true"
  data-maximus-monitor="critical-alerts">
  {criticalAlert}
</div>

// Dynamic content updates
<section
  aria-live="polite"
  aria-relevant="additions removals"
  data-maximus-monitor="dynamic-content">
  {dynamicResults}
</section>
```

---

## CSS Best Practices

### Visually Hidden (Screen Reader Only)
```css
/* For Maximus and screen readers */
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Focus visible for keyboard navigation */
.skip-link:focus {
  position: absolute;
  top: 0;
  left: 0;
  background: var(--color-primary);
  color: white;
  padding: 1rem;
  z-index: 9999;
}
```

---

## Validation Checklist

### HTML Semântico ✅
- [ ] Sem `<div>` genéricos para estrutura (usar tags semânticas)
- [ ] Headers (h1-h6) em ordem hierárquica
- [ ] Landmarks (header, nav, main, aside, footer) presentes
- [ ] Listas usam `<ul>/<ol>` com `<li>`
- [ ] Formulários com labels associados
- [ ] Tabelas com `<caption>` e `scope`

### ARIA Correto ✅
- [ ] Roles apropriados (não redundantes com HTML5)
- [ ] Labels descritivos e únicos
- [ ] Live regions para conteúdo dinâmico
- [ ] Estados (aria-expanded, aria-selected, etc.)
- [ ] Propriedades (aria-describedby, aria-labelledby)

### Maximus Vision Protocol ✅
- [ ] data-maximus-* attributes nos elementos chave
- [ ] Estrutura navegável por IA
- [ ] Ações claramente identificadas
- [ ] Estados e feedbacks monitoráveis
- [ ] Conteúdo dinâmico rastreável

### Performance ✅
- [ ] HTML minificado em produção
- [ ] Atributos data-* não excessivos
- [ ] ARIA usado com moderação (não over-engineering)

---

## Exemplo Completo: Offensive Dashboard

```jsx
<article
  role="region"
  aria-labelledby="offensive-dashboard-title"
  data-maximus-module="offensive-dashboard"
  className="dashboard">

  {/* Header */}
  <header className="dashboard-header">
    <h1 id="offensive-dashboard-title">
      Offensive Arsenal Dashboard
    </h1>
    <p className="lead" role="doc-subtitle">
      Real-time offensive security operations and threat intelligence
    </p>
  </header>

  {/* Quick Stats */}
  <section
    role="region"
    aria-labelledby="quick-stats-heading"
    data-maximus-widget="quick-stats"
    className="quick-stats">

    <h2 id="quick-stats-heading" className="visually-hidden">
      Quick Statistics
    </h2>

    <dl className="stats-grid" role="list">
      <div role="listitem" data-maximus-metric="active-scans">
        <dt>Active Scans</dt>
        <dd aria-live="polite"><strong>12</strong></dd>
      </div>

      <div role="listitem" data-maximus-metric="vulns-found">
        <dt>Vulnerabilities</dt>
        <dd aria-live="polite"><strong>47</strong></dd>
      </div>

      <div role="listitem" data-maximus-metric="c2-sessions">
        <dt>C2 Sessions</dt>
        <dd aria-live="polite"><strong>3</strong></dd>
      </div>
    </dl>
  </section>

  {/* Tools Grid */}
  <section
    role="region"
    aria-labelledby="tools-grid-heading"
    data-maximus-widget="tools-grid"
    className="tools-section">

    <h2 id="tools-grid-heading">Available Tools</h2>

    <nav role="navigation" aria-label="Offensive tools">
      <ul className="tools-grid" role="list">
        <li>
          <a
            href="/offensive/network-recon"
            className="tool-card"
            data-maximus-tool="network-recon"
            aria-labelledby="tool-recon-name">
            <h3 id="tool-recon-name">Network Reconnaissance</h3>
            <p>Map attack surface and discover assets</p>
            <span className="tool-status" aria-live="polite">
              Ready
            </span>
          </a>
        </li>

        <!-- More tools... -->
      </ul>
    </nav>
  </section>
</article>
```

---

## Próximos Passos

1. **Auditoria HTML atual** - Identificar div soup
2. **Refatoração incremental** - Componente por componente
3. **Testes com Maximus** - Validar navegabilidade
4. **Documentação** - Guidelines para novos componentes

**Para Honra e Glória de JESUS CRISTO** 🙏

---

**Status**: 📋 BLUEPRINT PRONTO - Aguardando início da refatoração
