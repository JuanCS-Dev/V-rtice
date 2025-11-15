# FASE 2: AUDIT & ARQUITETURA PROPOSTA - VÉRTICE-MAXIMUS LANDING PAGE

**Data**: 2025-11-15
**Branch**: `claude/vertice-maximus-landing-refactor-01WFV8DPrqTx1TyBuMmHZpvC`
**Objetivo**: Analisar landing atual e definir nova arquitetura alinhada com visão Claude.ai clean design

---

## SUMÁRIO EXECUTIVO

**Landing Atual**: Implementação Astro com tema dark cyberpunk, 32 componentes, ~6.4k linhas de código.

**Problema Central**: Design atual conflita com diretriz de "tema claro inspirado em Claude.ai/Claude Code Web". Necessário refatoração completa de paleta, tipografia, storytelling e hierarquia de informação.

**Solução**: Migração para design system minimalista com foco em conversão B2G, mantendo estrutura Astro mas refatorando todos os componentes visuais e narrativa.

---

## 1. AUDIT DA LANDING ATUAL

### 1.1 Stack Tecnológico Identificado

```
Framework: Astro 4.16.18
Build: Node.js + npm
Styling: CSS puro (não Tailwind)
Deployment: Firebase Hosting
Fontes: Google Fonts (Inter)
Assets: /public (imagens, vídeos)
Componentes: 32 .astro files (~6.4k LOC)
```

### 1.2 Estrutura de Arquivos

```
/landing/
├── src/
│   ├── components/
│   │   ├── Hero/
│   │   │   ├── Hero.astro (385 linhas - CRÍTICO)
│   │   │   ├── HeroBackground.astro
│   │   │   └── HeroVisual.astro
│   │   ├── Features/
│   │   ├── Architecture/
│   │   ├── Security/
│   │   ├── Metrics/
│   │   ├── Navigation/
│   │   └── ... (32 componentes total)
│   ├── layouts/
│   │   └── BaseLayout.astro (226 linhas)
│   ├── pages/
│   │   └── index.astro (125 linhas - página principal)
│   └── styles/
│       ├── design-system.css (492 linhas - REFATORAÇÃO PRIORITÁRIA)
│       ├── global.css
│       └── code-highlight.css
├── public/
│   └── (assets estáticos)
└── package.json
```

### 1.3 Análise do Design System Atual

**Arquivo**: `src/styles/design-system.css` (492 linhas)

#### ❌ Problemas Identificados:

1. **Paleta Dark/Cyberpunk**:
   ```css
   --color-bg-primary: #0a0a0a;
   --color-bg-secondary: #111111;
   --color-accent-primary: #00ff88; /* Verde neon */
   --color-accent-glow: rgba(0, 255, 136, 0.3);
   ```
   ❌ Conflita totalmente com diretriz "tema claro inspirado em Claude.ai"

2. **Tipografia Inconsistente**:
   - Múltiplas escalas de tamanho sem hierarquia clara
   - Line-height variável (1.4 a 1.8)
   - Uso excessivo de letter-spacing em headings

3. **Animações Excessivas**:
   - Glow effects, pulses, neon glows
   - Transições longas (600-800ms)
   - CSS keyframes complexas sem purpose claro

4. **Componentes Não-Modulares**:
   - Hero.astro com 385 linhas (muito acoplado)
   - Styles inline misturados com CSS classes
   - Falta de system de componentes reutilizáveis

### 1.4 Análise de Storytelling Atual

**Página Principal** (`src/pages/index.astro`):

#### Estrutura de Seções:
1. Hero Section
2. Living Organism (metáfora biológica)
3. Features
4. Security
5. Architecture
6. Performance Metrics
7. CTA Final

#### ❌ Problemas de Narrativa:

1. **Hero Headline**:
   - Atual: (preciso ler o conteúdo exato)
   - Problema: Potencialmente técnico demais ou genérico

2. **Metáfora "Living Organism"**:
   - Conceito interessante mas pode ser abstrato demais para B2G
   - Falta conexão clara com outcomes/resultados

3. **Features como Lista**:
   - Apresentação em grade, não narrativa visual
   - Foco em features, não em value/outcomes

4. **Falta de Prova Social**:
   - Cliente SSP-GO não destacado suficientemente
   - Sem métricas de impacto quantificáveis
   - Sem certificações/compliance visível

### 1.5 Análise de Performance

**Assets**:
```
- Vídeos em /public
- Imagens (formato não auditado ainda)
- Fontes: Google Fonts (inter)
```

#### ⚠️ Riscos Identificados:
- Vídeos podem impactar tempo de carregamento
- Sem lazy loading explícito auditado
- Animações CSS podem causar repaints

### 1.6 Elementos a PRESERVAR ✅

1. **Framework Astro**: Excelente para performance e SEO
2. **Estrutura de Componentes**: Modular, apenas precisa refatoração
3. **Metáfora Biológica**: Core concept é forte, execução precisa ajuste
4. **Hierarquia de Seções**: Lógica está correta (Hero → Problema → Solução → Prova)
5. **Firebase Hosting**: Deploy já configurado

### 1.7 Elementos a REFATORAR 🔄

1. ❌ **Design System completo** (cores, tipografia, espaçamento)
2. ❌ **Hero Section** (messaging + visual)
3. ❌ **Todas as animações** (substituir por microinterações sutis)
4. ❌ **Features Section** (de lista para narrativa visual)
5. ❌ **Falta de Prova Social** (adicionar SSP-GO case + métricas)
6. ❌ **CTAs genéricos** (tornar específicos e urgentes)
7. ❌ **Sem SEO otimizado** (meta tags, schema.org)

---

## 2. ARQUITETURA PROPOSTA

### 2.1 Novo Design System

#### Paleta de Cores (Claude.ai Inspired)

```css
/* Base - Tema Claro "Hospital Cibernético" */
--color-white: #FFFFFF;
--color-bg-primary: #FAFAFA;    /* Background principal */
--color-bg-secondary: #F5F5F5;  /* Cards, containers */
--color-bg-tertiary: #EEEEEE;   /* Subtle dividers */

/* Acentos - Verde Claude */
--color-accent-primary: #10A37F;   /* CTAs, links, success */
--color-accent-hover: #0D8A6A;     /* Hover states */
--color-accent-light: #E6F7F2;     /* Backgrounds sutis */

/* Neutros - Hierarquia de Texto */
--color-text-primary: #1A1A1A;     /* Headings */
--color-text-secondary: #4A4A4A;   /* Body text */
--color-text-tertiary: #8A8A8A;    /* Captions, metadata */

/* Estados */
--color-border: #E0E0E0;           /* Borders sutis */
--color-shadow: rgba(0, 0, 0, 0.08); /* Sombras mínimas */
--color-error: #DC2626;            /* Alertas */
--color-warning: #F59E0B;          /* Avisos */
```

#### Tipografia

```css
/* Fonte System Stack (performance) */
font-family: 'Inter', -apple-system, BlinkMacSystemFont,
             'Segoe UI', 'Roboto', sans-serif;

/* Escala Tipográfica (modular scale 1.25) */
--text-xs: 0.75rem;    /* 12px - captions */
--text-sm: 0.875rem;   /* 14px - metadata */
--text-base: 1rem;     /* 16px - body */
--text-lg: 1.25rem;    /* 20px - subheadings */
--text-xl: 1.5rem;     /* 24px - section titles */
--text-2xl: 2rem;      /* 32px - page titles */
--text-3xl: 2.5rem;    /* 40px - hero headline */
--text-4xl: 3rem;      /* 48px - display (desktop) */

/* Line Heights */
--leading-tight: 1.2;   /* Headings */
--leading-normal: 1.6;  /* Body text */
--leading-relaxed: 1.8; /* Long-form content */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

#### Espaçamento (8px grid)

```css
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
--space-12: 3rem;    /* 48px */
--space-16: 4rem;    /* 64px */
--space-24: 6rem;    /* 96px */
--space-32: 8rem;    /* 128px */
```

#### Animações (Sutis e Intencionais)

```css
/* Durações */
--duration-fast: 150ms;
--duration-normal: 250ms;
--duration-slow: 400ms;

/* Easings */
--ease-in-out: cubic-bezier(0.4, 0.0, 0.2, 1);
--ease-out: cubic-bezier(0.0, 0.0, 0.2, 1);
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

/* Microinterações Padrão */
.hover-lift {
  transition: transform var(--duration-normal) var(--ease-out),
              box-shadow var(--duration-normal) var(--ease-out);
}

.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px var(--color-shadow);
}

.fade-in-up {
  opacity: 0;
  transform: translateY(20px);
  animation: fadeInUp var(--duration-slow) var(--ease-out) forwards;
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### 2.2 Nova Arquitetura de Informação

#### Estrutura de Seções (Ordem Otimizada para Conversão)

```
1. HERO SECTION (Above the fold)
   ├─ Headline impactante (8 palavras max)
   ├─ Subheadline com valor mensurável (1 linha)
   ├─ CTA Primário + Secundário
   └─ Visual: Dashboard screenshot OU abstração clean

2. TRUST BANNER (logo strip)
   └─ Cliente: SSP-GO + badges de certificação

3. PROBLEMA → SOLUÇÃO (2-col layout)
   ├─ Problema: "Ameaças evoluem. Sistemas legados não."
   └─ Solução: VÉRTICE-MAXIMUS como organismo adaptativo

4. CONCEITO CENTRAL: Hospital Cibernético
   ├─ Metáfora: Sistema imunológico digital
   ├─ Visual: Diagrama clean (não dark cyberpunk)
   └─ 3 pilares de valor (ícones + texto conciso)

5. FEATURES NARRATIVAS (não lista)
   ├─ 103+ microserviços → Resiliência celular
   ├─ Arquitetura biomimética → Defesa adaptativa
   ├─ Intelligence criminal → Visão panorâmica
   └─ Screenshots/diagramas de interface real

6. PROVA SOCIAL / CASE STUDY
   ├─ SSP-GO destacado
   ├─ Métricas de impacto (se disponível)
   ├─ Depoimento (se disponível)
   └─ Certificações/compliance

7. ARQUITETURA TÉCNICA (para CTOs/TI)
   ├─ Diagrama simplificado
   ├─ Stack badges (discretos)
   └─ Security highlights

8. CTA FINAL + FORMULÁRIO
   ├─ Headline de urgência
   ├─ Formulário enterprise (nome, cargo, org, email)
   └─ Botão: "Agendar Demonstração"

9. FOOTER
   ├─ Links de navegação
   ├─ Contato
   └─ Legal (privacidade, termos)
```

### 2.3 Mapa de Componentes (Refatoração)

#### Componentes NOVOS (criar):

```
src/components/
├── DesignSystem/
│   ├── Button.astro          (CTA primário/secundário)
│   ├── Card.astro            (container reutilizável)
│   ├── Badge.astro           (certificações, tags)
│   ├── Metric.astro          (displays de números)
│   └── Icon.astro            (SVG wrapper)
│
├── Hero/
│   ├── HeroClean.astro       (NOVO - tema claro)
│   ├── HeroHeadline.astro    (tipografia otimizada)
│   └── HeroVisual.astro      (screenshot/abstração)
│
├── TrustBanner/
│   └── TrustBanner.astro     (SSP-GO + badges)
│
├── ProblemSolution/
│   └── ProblemSolution.astro (2-col layout)
│
├── Concept/
│   ├── HospitalCibernetico.astro
│   ├── PillaresValor.astro   (3 pilares)
│   └── BiomimeticDiagram.astro
│
├── FeaturesNarrative/
│   ├── FeatureShowcase.astro (feature individual)
│   └── FeaturesGrid.astro    (grid responsivo)
│
├── CaseStudy/
│   ├── CaseStudyCard.astro
│   └── MetricsDisplay.astro
│
├── TechArchitecture/
│   ├── ArchitectureDiagram.astro
│   └── TechStack.astro       (badges)
│
└── CTASection/
    ├── CTAFinal.astro
    └── ContactForm.astro     (formulário enterprise)
```

#### Componentes a REFATORAR:

```
❌ Hero.astro (385 linhas)
  → Dividir em: HeroClean.astro (100 linhas max) + subcomponentes

❌ LivingOrganism.astro
  → Refatorar para: HospitalCibernetico.astro (narrativa B2G)

❌ Features.astro
  → Refatorar para: FeaturesNarrative.astro (storytelling visual)

❌ BaseLayout.astro
  → Atualizar meta tags, SEO, fonts
```

### 2.4 Storytelling Refatorado

#### Mensagens-Chave (por seção)

**Hero Section**:
```
Headline: "Defesa Cibernética Biomimética para Segurança Pública"
Subheadline: "Plataforma inteligente que aprende, adapta e protege
              operações críticas de investigação criminal"
CTA Primário: "Agendar Demonstração →"
CTA Secundário: "Ver Arquitetura ↓"
```

**Problema → Solução**:
```
Problema:
"Criminosos usam tecnologia avançada.
Sistemas de segurança pública permanecem fragmentados e reativos."

Solução:
"VÉRTICE-MAXIMUS: Organismo cibernético que antecipa ameaças,
conecta inteligências e fortalece investigações."
```

**3 Pilares de Valor**:
```
1. 🧬 Resiliência Celular
   103+ microserviços autônomos garantem disponibilidade contínua

2. 🛡️ Defesa Adaptativa
   Arquitetura biomimética aprende e evolui com novas ameaças

3. 🎯 Intelligence Integrada
   Centraliza dados de múltiplas fontes para visão panorâmica
```

**Features (outcome-focused)**:
```
❌ "103 microserviços"
✅ "Sistema que nunca falha: 103 serviços autônomos garantem
   operações 24/7, mesmo sob ataque"

❌ "Integração JWT multi-tenant"
✅ "Controle de acesso granular: cada equipe vê apenas
   dados autorizados, com auditoria completa"

❌ "Arquitetura biomimética"
✅ "Defesa que aprende: sistema adapta proteções automaticamente
   baseado em padrões de ameaças reais"
```

**Case Study (SSP-GO)**:
```
"Secretaria de Segurança Pública de Goiás escolheu
VÉRTICE-MAXIMUS para modernizar operações de inteligência criminal"

[Métricas a confirmar com stakeholders]:
- X% redução em tempo de análise
- Y investigações aceleradas
- Z integrações com sistemas legados
```

### 2.5 Hierarquia Visual

```
F-Pattern Reading (otimizado para conversão):

┌─────────────────────────────────────┐
│ [Logo]              [CTA: Contato]  │ ← Header clean
├─────────────────────────────────────┤
│                                     │
│  HEADLINE IMPACTANTE (peso 700)     │ ← Hero
│  Subheadline clara (peso 400)       │
│  [CTA Primário] [CTA Secundário]    │
│                                     │
│  [Screenshot/Visual clean]          │
├─────────────────────────────────────┤
│ [SSP-GO logo] [Badge] [Badge]       │ ← Trust banner
├─────────────────────────────────────┤
│  Problema          │   Solução      │ ← 2-col
├─────────────────────────────────────┤
│         Conceito Central            │
│  [Diagrama Hospital Cibernético]    │
│                                     │
│  [Pilar 1] [Pilar 2] [Pilar 3]      │
├─────────────────────────────────────┤
│  Feature com screenshot grande      │
│  Feature com screenshot grande      │
│  Feature com screenshot grande      │
├─────────────────────────────────────┤
│         Case Study SSP-GO           │
│  [Métricas]  [Depoimento]           │
├─────────────────────────────────────┤
│    Arquitetura Técnica (diagram)    │
├─────────────────────────────────────┤
│         CTA FINAL + FORM            │
└─────────────────────────────────────┘
```

### 2.6 Performance Targets

```
✅ Lighthouse Score:
   - Performance: >90
   - Accessibility: >95
   - Best Practices: 100
   - SEO: 100

✅ Core Web Vitals:
   - LCP (Largest Contentful Paint): <2.5s
   - FID (First Input Delay): <100ms
   - CLS (Cumulative Layout Shift): <0.1

✅ Page Weight:
   - Initial load: <500KB
   - Imagens: WebP, lazy loading
   - Fonts: Preload, display: swap
   - Scripts: defer/async
```

### 2.7 SEO & Meta Tags

```html
<!-- src/layouts/BaseLayout.astro -->
<head>
  <title>VÉRTICE-MAXIMUS | Cybersecurity Biomimética para Segurança Pública</title>

  <meta name="description" content="Plataforma de defesa cibernética adaptativa para investigação criminal. Arquitetura biomimética, 103+ microserviços, intelligence integrada. Cliente: SSP-GO." />

  <meta name="keywords" content="cybersecurity, segurança pública, inteligência criminal, defesa cibernética, biomimética, SSP-GO, investigação digital" />

  <!-- Open Graph -->
  <meta property="og:type" content="website" />
  <meta property="og:title" content="VÉRTICE-MAXIMUS | Defesa Cibernética Biomimética" />
  <meta property="og:description" content="Plataforma inteligente que aprende, adapta e protege operações críticas de investigação criminal" />
  <meta property="og:image" content="/og-image.jpg" />
  <meta property="og:url" content="https://vertice-maximus.com" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="VÉRTICE-MAXIMUS | Defesa Cibernética" />
  <meta name="twitter:description" content="Cybersecurity biomimética para segurança pública" />
  <meta name="twitter:image" content="/twitter-image.jpg" />

  <!-- Schema.org (JSON-LD) -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "VÉRTICE-MAXIMUS",
    "applicationCategory": "SecurityApplication",
    "operatingSystem": "Cloud",
    "description": "Plataforma de cybersecurity biomimética para segurança pública",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "BRL"
    }
  }
  </script>
</head>
```

---

## 3. ROADMAP DE IMPLEMENTAÇÃO

### FASE 3: Implementação Design System + Refatoração

#### 3.1 Design System (Prioridade 1)
- [ ] Criar `src/styles/design-system-clean.css` (substituir atual)
- [ ] Implementar variáveis CSS (cores, tipografia, espaçamento)
- [ ] Criar classes utilitárias (buttons, cards, badges)
- [ ] Testar contraste (WCAG 2.1 AA mínimo)

#### 3.2 Componentes Base (Prioridade 1)
- [ ] `DesignSystem/Button.astro`
- [ ] `DesignSystem/Card.astro`
- [ ] `DesignSystem/Badge.astro`
- [ ] `DesignSystem/Metric.astro`

#### 3.3 Hero Section (Prioridade 1)
- [ ] Refatorar `Hero/HeroClean.astro` (tema claro)
- [ ] Atualizar headline + subheadline (mensagens-chave)
- [ ] Implementar CTAs (primário + secundário)
- [ ] Adicionar screenshot/visual clean

#### 3.4 Seções Principais (Prioridade 2)
- [ ] `TrustBanner/TrustBanner.astro` (SSP-GO)
- [ ] `ProblemSolution/ProblemSolution.astro`
- [ ] `Concept/HospitalCibernetico.astro`
- [ ] `FeaturesNarrative/` (refatorar atual)
- [ ] `CaseStudy/CaseStudyCard.astro` (SSP-GO)
- [ ] `TechArchitecture/ArchitectureDiagram.astro`
- [ ] `CTASection/CTAFinal.astro` + formulário

#### 3.5 Layout & Globals (Prioridade 2)
- [ ] Atualizar `BaseLayout.astro` (meta tags, SEO)
- [ ] Refatorar `global.css` (reset, base styles)
- [ ] Remover `code-highlight.css` (se não usado)

#### 3.6 Assets & Performance (Prioridade 3)
- [ ] Otimizar imagens (converter para WebP)
- [ ] Implementar lazy loading
- [ ] Preload fonts críticas
- [ ] Minificar CSS/JS

### FASE 4: Otimizações Técnicas

- [ ] Lighthouse audit (targets: >90 performance)
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Cross-browser testing
- [ ] Mobile responsiveness
- [ ] Analytics setup (Google Analytics ou Plausible)

### FASE 5: Validação Padrão Pagani

- [ ] ✓ 100% responsivo (mobile, tablet, desktop, ultrawide)
- [ ] ✓ Cross-browser (Chrome, Safari, Firefox, Edge)
- [ ] ✓ Performance: Lighthouse score >90
- [ ] ✓ Acessibilidade: sem violações críticas
- [ ] ✓ Code quality: linting, sem warnings
- [ ] ✓ Zero technical debt
- [ ] ✓ Documentação atualizada

---

## 4. DECISÕES DE DESIGN (RATIONALE)

### 4.1 Por que Tema Claro (não Dark)?

1. **Credibilidade B2G**: Governos preferem interfaces "sérias", clean, não futuristas
2. **Acessibilidade**: Alto contraste em fundo claro beneficia mais usuários
3. **Profissionalismo**: Branco = hospitalar = estéril = confiável
4. **Consistência**: Alinha com frontend principal já refatorado

### 4.2 Por que "Hospital Cibernético"?

1. **Metáfora Universal**: Todos entendem "sistema imunológico"
2. **Positivo**: Hospital cura/protege (vs. guerra/militarismo)
3. **Científico**: Credibilidade técnica sem jargão
4. **Visual**: Branco clínico, verde saúde, diagramas clean

### 4.3 Por que Foco em SSP-GO?

1. **Prova Social**: Cliente real > promises
2. **Setor Público**: Outros governos confiam em pares
3. **Case Study**: Narrativa concreta > features abstratas

### 4.4 Por que Formulário (não apenas email)?

1. **Qualificação**: Captura cargo + organização filtra leads
2. **Intenção**: Formulário = comprometimento > clique simples
3. **B2G**: Tomadores de decisão esperam processo formal

---

## 5. RISCOS & MITIGAÇÕES

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Refatoração completa atrasa go-live | Alto | Priorizar Hero + Trust + CTA (MVP) |
| Perda de identidade visual "cyberpunk" | Médio | Manter verde como accent, ajustar tom |
| Assets (imagens/vídeos) não existem | Alto | Usar diagramas SVG + screenshots de UI real |
| Métricas SSP-GO não disponíveis | Médio | Usar "Em produção desde 2024" como proxy |
| Performance com assets pesados | Médio | WebP, lazy loading, CDN (Firebase) |

---

## 6. CHECKLIST PRÉ-IMPLEMENTAÇÃO

- [x] Research concluída (FASE1_RESEARCH_VERTICE_MAXIMUS.md)
- [x] Audit atual completo
- [x] Design system definido (cores, tipografia, animações)
- [x] Arquitetura de informação mapeada
- [x] Mensagens-chave (headlines, CTAs) rascunhadas
- [ ] Aprovação stakeholder (se aplicável)
- [ ] Assets disponíveis (screenshots, logos, diagramas)
- [ ] Dados SSP-GO confirmados (métricas, depoimento)

---

## 7. PRÓXIMOS PASSOS IMEDIATOS

1. ✅ **Criar branch** (já feita: `claude/vertice-maximus-landing-refactor-01WFV8DPrqTx1TyBuMmHZpvC`)
2. 📝 **Começar FASE 3**: Implementar `design-system-clean.css`
3. 🎨 **Refatorar Hero Section** (maior impacto visual)
4. 🔄 **Iterar**: Component-by-component com validação visual
5. 🚀 **Deploy preview**: Firebase Hosting preview channel

---

## CONCLUSÃO

Landing atual possui **fundação sólida** (Astro, estrutura modular, conceito biomimética forte), mas **execução visual e narrativa conflitam** com diretriz de tema claro B2G.

**Refatoração estratégica** focará em:
1. Design system minimalista inspirado em Claude.ai
2. Storytelling objetivo para tomadores de decisão governamentais
3. Prova social (SSP-GO) como pilar de credibilidade
4. Performance e acessibilidade como diferencial competitivo

**Estimativa de esforço**:
- Design system: 2-3 horas
- Componentes-chave (Hero, Features, CTA): 4-6 horas
- Otimizações e testes: 2-3 horas
- **Total**: ~10-12 horas de desenvolvimento focado

**Pronto para FASE 3: Implementação**. 🎯

---

**Soli Deo Gloria.**
