# 🎨 BLUEPRINT: Sistema de Temas VÉRTICE
## From Hacker Dream to Enterprise Reality

**Data**: 2025-10-10  
**Status**: 🎯 Blueprint Final  
**Base**: Whitepaper de Arquitetura de Temas  
**Objetivo**: Dual-theme system (Hacker + Enterprise)

---

## 🎯 VISÃO ESTRATÉGICA

### Problema
```
ATUAL:  Front-end = "Hacker Adolescent Dream" (Matrix vibes 💚)
NEED:   Enterprise-ready themes for corporate clients
MUST:   Manter identidade hacker + adicionar corporate boring
```

### Solução
**Sistema de Tokens em 3 Camadas** baseado em CSS Custom Properties:
1. **Primitivo** - Valores brutos (cores hex, tamanhos px)
2. **Semântico** - Decisões de design (primary, surface, interactive)
3. **Componente** - Aplicação contextual (button, card, sidebar)

### Arquitetura Recomendada
```
Tokens Hierarchy (Atlassian Model)
  ├─ [foundation].[property].[modifier]
  ├─ color.text.subtle
  ├─ elevation.surface.raised
  └─ spacing.layout.medium
```

---

## 🏗️ ARQUITETURA TÉCNICA

### Estrutura de Arquivos
```
frontend/src/
├── styles/
│   ├── tokens/
│   │   ├── primitive.css         # Camada 1: Raw values
│   │   ├── semantic.css          # Camada 2: Design decisions
│   │   └── component.css         # Camada 3: Component tokens
│   │
│   ├── themes/
│   │   ├── hacker/               # 💚 Original identity
│   │   │   ├── cyber-blue.css
│   │   │   ├── purple-haze.css
│   │   │   ├── red-alert.css
│   │   │   └── stealth-mode.css
│   │   │
│   │   ├── enterprise/           # 💼 Corporate themes
│   │   │   ├── corporate-light.css
│   │   │   ├── corporate-dark.css
│   │   │   ├── minimal-modern.css
│   │   │   └── professional-blue.css
│   │   │
│   │   └── index.css             # Theme loader
│   │
│   ├── base.css                  # Global resets + base
│   └── themes.css                # Main theme orchestrator
│
├── lib/
│   └── theme/
│       ├── ThemeProvider.tsx     # React context
│       ├── theme-manager.ts      # Core logic
│       ├── theme-storage.ts      # LocalStorage persist
│       └── types.ts              # TypeScript definitions
│
└── components/
    └── ThemeSwitcher/
        ├── ThemeSwitcher.tsx     # UI component
        ├── ThemePreview.tsx      # Live preview
        └── ThemeSwitcher.module.css
```

### Token System - 3 Layers

#### Layer 1: Primitive Tokens (Raw Values)
```css
/* styles/tokens/primitive.css */
:root {
  /* Colors - Raw Palette */
  --primitive-green-500: #00ff41;
  --primitive-green-900: #003d10;
  --primitive-blue-500: #00d4ff;
  --primitive-gray-50: #fafafa;
  --primitive-gray-900: #0a0a0a;
  
  /* Spacing Scale */
  --primitive-space-1: 0.25rem;
  --primitive-space-2: 0.5rem;
  --primitive-space-4: 1rem;
  --primitive-space-8: 2rem;
  
  /* Typography Scale */
  --primitive-font-size-xs: 0.75rem;
  --primitive-font-size-sm: 0.875rem;
  --primitive-font-size-base: 1rem;
  --primitive-font-size-lg: 1.125rem;
  
  /* Elevation/Shadows */
  --primitive-shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --primitive-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --primitive-shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  
  /* Border Radius */
  --primitive-radius-sm: 0.25rem;
  --primitive-radius-md: 0.375rem;
  --primitive-radius-lg: 0.5rem;
  
  /* Transitions */
  --primitive-duration-fast: 150ms;
  --primitive-duration-normal: 300ms;
  --primitive-duration-slow: 500ms;
}
```

#### Layer 2: Semantic Tokens (Design Decisions)
```css
/* styles/tokens/semantic.css */
:root {
  /* Background Hierarchy */
  --color-bg-primary: var(--primitive-gray-900);
  --color-bg-secondary: var(--primitive-gray-800);
  --color-bg-tertiary: var(--primitive-gray-700);
  --color-bg-elevated: var(--primitive-gray-850);
  --color-bg-overlay: rgba(0, 0, 0, 0.8);
  
  /* Text Hierarchy */
  --color-text-primary: var(--primitive-gray-50);
  --color-text-secondary: var(--primitive-gray-400);
  --color-text-subtle: var(--primitive-gray-500);
  --color-text-disabled: var(--primitive-gray-600);
  
  /* Brand Colors */
  --color-brand-primary: var(--primitive-green-500);
  --color-brand-secondary: var(--primitive-blue-500);
  
  /* Interactive States */
  --color-interactive-default: var(--color-brand-primary);
  --color-interactive-hover: var(--primitive-green-400);
  --color-interactive-active: var(--primitive-green-600);
  --color-interactive-disabled: var(--primitive-gray-600);
  
  /* Semantic Status */
  --color-status-success: var(--primitive-green-500);
  --color-status-warning: var(--primitive-yellow-500);
  --color-status-error: var(--primitive-red-500);
  --color-status-info: var(--primitive-blue-500);
  
  /* Surface Elevation */
  --elevation-base: 0;
  --elevation-raised: var(--primitive-shadow-md);
  --elevation-overlay: var(--primitive-shadow-lg);
  
  /* Spacing System */
  --spacing-xs: var(--primitive-space-1);
  --spacing-sm: var(--primitive-space-2);
  --spacing-md: var(--primitive-space-4);
  --spacing-lg: var(--primitive-space-8);
  
  /* Typography System */
  --font-primary: 'Courier New', monospace;
  --font-secondary: 'Arial', sans-serif;
  --font-size-body: var(--primitive-font-size-base);
  --font-size-heading: var(--primitive-font-size-lg);
  
  /* Border System */
  --border-width-thin: 1px;
  --border-width-thick: 2px;
  --border-radius-default: var(--primitive-radius-md);
  
  /* Animation */
  --transition-fast: var(--primitive-duration-fast) ease;
  --transition-normal: var(--primitive-duration-normal) ease;
  --transition-slow: var(--primitive-duration-slow) ease;
}
```

#### Layer 3: Component Tokens (Contextual Application)
```css
/* styles/tokens/component.css */
:root {
  /* Button Component */
  --button-bg-primary: var(--color-interactive-default);
  --button-bg-primary-hover: var(--color-interactive-hover);
  --button-text-primary: var(--color-text-primary);
  --button-border-radius: var(--border-radius-default);
  --button-padding-x: var(--spacing-md);
  --button-padding-y: var(--spacing-sm);
  
  /* Card Component */
  --card-bg: var(--color-bg-secondary);
  --card-border: var(--color-bg-tertiary);
  --card-shadow: var(--elevation-raised);
  --card-radius: var(--border-radius-default);
  --card-padding: var(--spacing-md);
  
  /* Sidebar Component */
  --sidebar-bg: var(--color-bg-primary);
  --sidebar-item-hover: var(--color-bg-tertiary);
  --sidebar-item-active: var(--color-interactive-default);
  --sidebar-width: 16rem;
  
  /* Header Component */
  --header-bg: var(--color-bg-elevated);
  --header-height: 4rem;
  --header-shadow: var(--elevation-raised);
  
  /* Input Component */
  --input-bg: var(--color-bg-tertiary);
  --input-border: var(--color-bg-secondary);
  --input-border-focus: var(--color-interactive-default);
  --input-text: var(--color-text-primary);
  --input-placeholder: var(--color-text-subtle);
}
```

---

## 🎭 TEMAS DEFINIDOS

### Theme Family: Hacker (Original Identity)
```css
/* cyber-blue.css - Cyberpunk Matrix vibes */
[data-theme="cyber-blue"] {
  --color-brand-primary: #00d4ff;
  --color-bg-primary: #0a0e14;
  --font-primary: 'Courier New', monospace;
  /* Electric blue accents, dark backgrounds */
}

/* purple-haze.css - Purple team vibes */
[data-theme="purple-haze"] {
  --color-brand-primary: #b794f6;
  --color-bg-primary: #1a0f2e;
  /* Purple gradients, mystical feel */
}

/* red-alert.css - High alert cyber */
[data-theme="red-alert"] {
  --color-brand-primary: #ff0040;
  --color-bg-primary: #1a0505;
  /* Red warning tones, urgent feel */
}

/* stealth-mode.css - Dark ops */
[data-theme="stealth-mode"] {
  --color-brand-primary: #2d3748;
  --color-bg-primary: #000000;
  /* Pure black, minimal accents */
}
```

### Theme Family: Enterprise (Corporate Professional)
```css
/* corporate-light.css - Standard corporate */
[data-theme="corporate-light"] {
  --color-brand-primary: #0066cc;
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f5f5f5;
  --color-text-primary: #1a1a1a;
  --font-primary: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  /* Clean, professional, boring */
}

/* corporate-dark.css - Dark mode professional */
[data-theme="corporate-dark"] {
  --color-brand-primary: #4da3ff;
  --color-bg-primary: #1a1a1a;
  --color-bg-secondary: #2a2a2a;
  --color-text-primary: #e0e0e0;
  /* Professional dark, not cyberpunk */
}

/* minimal-modern.css - Apple-esque minimal */
[data-theme="minimal-modern"] {
  --color-brand-primary: #007aff;
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #fafafa;
  --border-radius-default: 0.75rem;
  /* Generous whitespace, subtle */
}

/* professional-blue.css - IBM/Microsoft vibes */
[data-theme="professional-blue"] {
  --color-brand-primary: #0078d4;
  --color-bg-primary: #f3f2f1;
  --color-bg-secondary: #ffffff;
  /* Corporate blue, safe */
}
```

---

## 🔧 IMPLEMENTAÇÃO TÉCNICA

### Theme Manager (Core Logic)
```typescript
// lib/theme/theme-manager.ts
export type ThemeCategory = 'hacker' | 'enterprise';
export type HackerTheme = 'cyber-blue' | 'purple-haze' | 'red-alert' | 'stealth-mode';
export type EnterpriseTheme = 'corporate-light' | 'corporate-dark' | 'minimal-modern' | 'professional-blue';
export type Theme = HackerTheme | EnterpriseTheme;

export interface ThemeConfig {
  id: Theme;
  name: string;
  category: ThemeCategory;
  description: string;
  preview: {
    primary: string;
    background: string;
    text: string;
  };
}

export const THEME_CONFIGS: Record<Theme, ThemeConfig> = {
  'cyber-blue': {
    id: 'cyber-blue',
    name: 'Cyber Blue',
    category: 'hacker',
    description: 'Matrix-inspired cyberpunk aesthetic',
    preview: { primary: '#00d4ff', background: '#0a0e14', text: '#e0e0e0' }
  },
  // ... outros temas
};

export class ThemeManager {
  private currentTheme: Theme = 'cyber-blue';
  private listeners: Set<(theme: Theme) => void> = new Set();
  
  constructor() {
    this.loadSavedTheme();
    this.setupMediaQuery();
  }
  
  setTheme(theme: Theme): void {
    this.currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    this.saveTheme(theme);
    this.notifyListeners();
  }
  
  getTheme(): Theme {
    return this.currentTheme;
  }
  
  getCategory(): ThemeCategory {
    return THEME_CONFIGS[this.currentTheme].category;
  }
  
  private loadSavedTheme(): void {
    const saved = localStorage.getItem('vertice-theme') as Theme;
    if (saved && THEME_CONFIGS[saved]) {
      this.setTheme(saved);
    }
  }
  
  private saveTheme(theme: Theme): void {
    localStorage.setItem('vertice-theme', theme);
  }
  
  private setupMediaQuery(): void {
    // Respect system preference as fallback
    const darkMode = window.matchMedia('(prefers-color-scheme: dark)');
    darkMode.addEventListener('change', (e) => {
      if (!localStorage.getItem('vertice-theme')) {
        // Only auto-switch if user hasn't set preference
        const fallback = e.matches ? 'stealth-mode' : 'corporate-light';
        this.setTheme(fallback);
      }
    });
  }
  
  subscribe(listener: (theme: Theme) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
  
  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.currentTheme));
  }
}

export const themeManager = new ThemeManager();
```

### FOUC Prevention (Critical!)
```html
<!-- index.html - Must be in <head> BEFORE any styles -->
<script>
  (function() {
    // Blocking script to prevent FOUC
    const theme = localStorage.getItem('vertice-theme') || 'cyber-blue';
    document.documentElement.setAttribute('data-theme', theme);
    
    // Also set data-theme-category for additional flexibility
    const hackerThemes = ['cyber-blue', 'purple-haze', 'red-alert', 'stealth-mode'];
    const category = hackerThemes.includes(theme) ? 'hacker' : 'enterprise';
    document.documentElement.setAttribute('data-theme-category', category);
  })();
</script>
```

### React Theme Provider
```typescript
// lib/theme/ThemeProvider.tsx
import { createContext, useContext, useEffect, useState } from 'react';
import { themeManager, Theme, ThemeCategory } from './theme-manager';

interface ThemeContextValue {
  theme: Theme;
  category: ThemeCategory;
  setTheme: (theme: Theme) => void;
  availableThemes: Theme[];
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(themeManager.getTheme());
  const [category, setCategoryState] = useState<ThemeCategory>(themeManager.getCategory());
  
  useEffect(() => {
    const unsubscribe = themeManager.subscribe((newTheme) => {
      setThemeState(newTheme);
      setCategoryState(themeManager.getCategory());
    });
    
    return unsubscribe;
  }, []);
  
  const setTheme = (newTheme: Theme) => {
    themeManager.setTheme(newTheme);
  };
  
  const availableThemes = Object.keys(THEME_CONFIGS) as Theme[];
  
  return (
    <ThemeContext.Provider value={{ theme, category, setTheme, availableThemes }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
```

---

## 🎨 COMPONENTE UI: Theme Switcher

### ThemeSwitcher Component
```tsx
// components/ThemeSwitcher/ThemeSwitcher.tsx
import { useState } from 'react';
import { useTheme } from '@/lib/theme/ThemeProvider';
import { THEME_CONFIGS } from '@/lib/theme/theme-manager';
import styles from './ThemeSwitcher.module.css';

export function ThemeSwitcher() {
  const { theme, category, setTheme, availableThemes } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  
  // Group themes by category
  const hackerThemes = availableThemes.filter(t => THEME_CONFIGS[t].category === 'hacker');
  const enterpriseThemes = availableThemes.filter(t => THEME_CONFIGS[t].category === 'enterprise');
  
  return (
    <div className={styles.themeSwitcher}>
      <button 
        className={styles.trigger}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Switch theme"
      >
        🎨 {THEME_CONFIGS[theme].name}
      </button>
      
      {isOpen && (
        <div className={styles.dropdown}>
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>💚 Hacker Themes</h3>
            <div className={styles.grid}>
              {hackerThemes.map(t => (
                <ThemeCard
                  key={t}
                  theme={t}
                  isActive={t === theme}
                  onClick={() => {
                    setTheme(t);
                    setIsOpen(false);
                  }}
                />
              ))}
            </div>
          </div>
          
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>💼 Enterprise Themes</h3>
            <div className={styles.grid}>
              {enterpriseThemes.map(t => (
                <ThemeCard
                  key={t}
                  theme={t}
                  isActive={t === theme}
                  onClick={() => {
                    setTheme(t);
                    setIsOpen(false);
                  }}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ThemeCard({ theme, isActive, onClick }) {
  const config = THEME_CONFIGS[theme];
  
  return (
    <button
      className={`${styles.card} ${isActive ? styles.active : ''}`}
      onClick={onClick}
      style={{
        '--preview-primary': config.preview.primary,
        '--preview-bg': config.preview.background,
        '--preview-text': config.preview.text,
      }}
    >
      <div className={styles.preview}>
        <div className={styles.previewBar} />
        <div className={styles.previewContent} />
      </div>
      <div className={styles.info}>
        <div className={styles.name}>{config.name}</div>
        <div className={styles.description}>{config.description}</div>
      </div>
    </button>
  );
}
```

---

## 📊 MÉTRICAS DE SUCESSO

### Technical Metrics
- ✅ **FOUC**: 0ms (eliminated via blocking script)
- ✅ **Theme Switch**: <50ms (CSS custom properties)
- ✅ **Bundle Size**: +15KB max (8 themes)
- ✅ **Token Count**: ~100 tokens across 3 layers
- ✅ **Component Coverage**: 100% using tokens

### UX Metrics
- ✅ **Hacker Identity**: Preserved in 4 themes
- ✅ **Enterprise Appeal**: 4 professional themes
- ✅ **User Choice**: 8 total themes
- ✅ **Instant Switch**: No page reload
- ✅ **Persistence**: Remembers user choice

### Business Metrics
- 🎯 **Corporate Adoption**: Enable enterprise clients
- 🎯 **Brand Flexibility**: Multi-brand capable
- 🎯 **Accessibility**: WCAG AA compliance ready
- 🎯 **Maintenance**: Single token source of truth

---

## 🚀 PRÓXIMOS PASSOS

Ver ROADMAP e IMPLEMENTATION PLAN para execução completa.

---

**Status**: ✅ BLUEPRINT COMPLETE  
**Base**: Whitepaper de Arquitetura de Temas  
**Alignment**: 100% com recomendações (3-layer tokens, CSS Custom Properties)  
**Philosophy**: From hacker dream to enterprise reality, mantendo alma 💚

"Dual identity. One codebase. Zero compromise." 🎨
