# ⚡ IMPLEMENTATION PLAN: Sistema de Temas VÉRTICE
## Step-by-Step Execution Guide - Código Pronto para Copiar

**Data**: 2025-10-10  
**Target**: Production-ready em <6h  
**Approach**: Copy-paste friendly, testável, incremental

---

## 🎯 QUICK START

```bash
# Clone this plan and execute phase by phase
cd /home/juan/vertice-dev/frontend

# Start with FASE 0
git checkout -b feature/theme-system-foundation
```

---

## 📋 FASE 0: PREPARAÇÃO

### Step 0.1: Backup & Branch
```bash
# Create feature branch
git checkout -b feature/theme-system-foundation

# Commit current state
git add -A
git commit -m "checkpoint: Before theme system implementation"

# Backup existing themes
mkdir -p .backup/themes-old
cp -r src/themes .backup/themes-old/
cp src/index.css .backup/
cp src/styles/themes.css .backup/ 2>/dev/null || true
```

### Step 0.2: Create Directory Structure
```bash
# Create token directories
mkdir -p src/styles/tokens
mkdir -p src/styles/themes/hacker
mkdir -p src/styles/themes/enterprise

# Create lib directory
mkdir -p src/lib/theme

# Create component directory
mkdir -p src/components/ThemeSwitcher
```

### Step 0.3: Analysis Script
```bash
# Create analysis script
cat > analyze-current-themes.sh << 'ANALYZE'
#!/bin/bash
echo "=== Current Theme Analysis ==="
echo ""
echo "Existing themes:"
ls -1 src/themes/*.css 2>/dev/null || echo "No themes directory"
echo ""
echo "CSS Custom Properties in use:"
grep -r "var(--" src/components --include="*.css" | cut -d: -f2 | sort -u | head -20
echo ""
echo "Hardcoded colors to migrate:"
grep -r "#[0-9a-f]\{6\}" src/components --include="*.tsx" --include="*.jsx" | wc -l
ANALYZE

chmod +x analyze-current-themes.sh
./analyze-current-themes.sh
```

**Validação**: Directory structure created, analysis complete.

---

## 🎯 FASE 1: FOUNDATION - Token System

### Step 1.1: Primitive Tokens

Criar arquivo: `src/styles/tokens/primitive.css`

```css
/**
 * PRIMITIVE TOKENS - Layer 1
 * Raw values that serve as foundation
 * Never reference other tokens
 */

:root {
  /* ===== COLOR PALETTE ===== */
  
  /* Grays - Universal */
  --primitive-gray-50: #fafafa;
  --primitive-gray-100: #f5f5f5;
  --primitive-gray-200: #eeeeee;
  --primitive-gray-300: #e0e0e0;
  --primitive-gray-400: #bdbdbd;
  --primitive-gray-500: #9e9e9e;
  --primitive-gray-600: #757575;
  --primitive-gray-700: #616161;
  --primitive-gray-800: #424242;
  --primitive-gray-850: #2a2a2a;
  --primitive-gray-900: #1a1a1a;
  --primitive-gray-950: #0a0a0a;
  
  /* Hacker Greens (Matrix vibes) */
  --primitive-green-300: #66ff66;
  --primitive-green-400: #33ff33;
  --primitive-green-500: #00ff41;
  --primitive-green-600: #00cc33;
  --primitive-green-700: #009926;
  --primitive-green-800: #00661a;
  --primitive-green-900: #003d10;
  
  /* Hacker Blues (Cyber) */
  --primitive-blue-300: #66d4ff;
  --primitive-blue-400: #33c4ff;
  --primitive-blue-500: #00d4ff;
  --primitive-blue-600: #00a0cc;
  --primitive-blue-700: #007a99;
  --primitive-blue-800: #005066;
  --primitive-blue-900: #003040;
  
  /* Hacker Purples (Purple Team) */
  --primitive-purple-300: #d7b8ff;
  --primitive-purple-400: #c794ff;
  --primitive-purple-500: #b794f6;
  --primitive-purple-600: #9370db;
  --primitive-purple-700: #7050a8;
  --primitive-purple-800: #4c3575;
  --primitive-purple-900: #2a1a42;
  
  /* Hacker Reds (Alert) */
  --primitive-red-300: #ff6680;
  --primitive-red-400: #ff3355;
  --primitive-red-500: #ff0040;
  --primitive-red-600: #cc0033;
  --primitive-red-700: #990026;
  --primitive-red-800: #66001a;
  --primitive-red-900: #40000f;
  
  /* Corporate Blues (Professional) */
  --primitive-corp-blue-300: #66b3ff;
  --primitive-corp-blue-400: #3399ff;
  --primitive-corp-blue-500: #0066cc;
  --primitive-corp-blue-600: #0052a3;
  --primitive-corp-blue-700: #003d7a;
  --primitive-corp-blue-800: #002952;
  --primitive-corp-blue-900: #001429;
  
  /* Microsoft Blues */
  --primitive-ms-blue-400: #4da3ff;
  --primitive-ms-blue-500: #0078d4;
  --primitive-ms-blue-600: #0060a8;
  
  /* Apple Blues */
  --primitive-apple-blue-500: #007aff;
  --primitive-apple-blue-600: #0051d5;
  
  /* Status Colors */
  --primitive-success-500: #10b981;
  --primitive-warning-500: #f59e0b;
  --primitive-error-500: #ef4444;
  --primitive-info-500: #3b82f6;
  
  /* ===== SPACING SCALE ===== */
  --primitive-space-0: 0;
  --primitive-space-1: 0.25rem;   /* 4px */
  --primitive-space-2: 0.5rem;    /* 8px */
  --primitive-space-3: 0.75rem;   /* 12px */
  --primitive-space-4: 1rem;      /* 16px */
  --primitive-space-5: 1.25rem;   /* 20px */
  --primitive-space-6: 1.5rem;    /* 24px */
  --primitive-space-8: 2rem;      /* 32px */
  --primitive-space-10: 2.5rem;   /* 40px */
  --primitive-space-12: 3rem;     /* 48px */
  --primitive-space-16: 4rem;     /* 64px */
  --primitive-space-20: 5rem;     /* 80px */
  --primitive-space-24: 6rem;     /* 96px */
  
  /* ===== TYPOGRAPHY SCALE ===== */
  --primitive-font-size-xs: 0.75rem;    /* 12px */
  --primitive-font-size-sm: 0.875rem;   /* 14px */
  --primitive-font-size-base: 1rem;     /* 16px */
  --primitive-font-size-lg: 1.125rem;   /* 18px */
  --primitive-font-size-xl: 1.25rem;    /* 20px */
  --primitive-font-size-2xl: 1.5rem;    /* 24px */
  --primitive-font-size-3xl: 1.875rem;  /* 30px */
  --primitive-font-size-4xl: 2.25rem;   /* 36px */
  
  /* Font Weights */
  --primitive-font-weight-normal: 400;
  --primitive-font-weight-medium: 500;
  --primitive-font-weight-semibold: 600;
  --primitive-font-weight-bold: 700;
  
  /* Line Heights */
  --primitive-line-height-tight: 1.25;
  --primitive-line-height-normal: 1.5;
  --primitive-line-height-relaxed: 1.75;
  
  /* ===== SHADOWS (ELEVATION) ===== */
  --primitive-shadow-xs: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --primitive-shadow-sm: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --primitive-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --primitive-shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  --primitive-shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
  --primitive-shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
  
  /* Glow Shadows (for hacker themes) */
  --primitive-glow-sm: 0 0 10px currentColor;
  --primitive-glow-md: 0 0 20px currentColor;
  --primitive-glow-lg: 0 0 30px currentColor;
  
  /* ===== BORDER RADIUS ===== */
  --primitive-radius-none: 0;
  --primitive-radius-sm: 0.125rem;  /* 2px */
  --primitive-radius-md: 0.375rem;  /* 6px */
  --primitive-radius-lg: 0.5rem;    /* 8px */
  --primitive-radius-xl: 0.75rem;   /* 12px */
  --primitive-radius-2xl: 1rem;     /* 16px */
  --primitive-radius-full: 9999px;  /* Pill shape */
  
  /* ===== TRANSITIONS ===== */
  --primitive-duration-instant: 0ms;
  --primitive-duration-fast: 150ms;
  --primitive-duration-normal: 300ms;
  --primitive-duration-slow: 500ms;
  --primitive-duration-slower: 700ms;
  
  --primitive-easing-linear: linear;
  --primitive-easing-ease: ease;
  --primitive-easing-ease-in: ease-in;
  --primitive-easing-ease-out: ease-out;
  --primitive-easing-ease-in-out: ease-in-out;
  
  /* Custom easings */
  --primitive-easing-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
  --primitive-easing-smooth: cubic-bezier(0.4, 0, 0.2, 1);
  
  /* ===== Z-INDEX SCALE ===== */
  --primitive-z-base: 0;
  --primitive-z-dropdown: 1000;
  --primitive-z-sticky: 1100;
  --primitive-z-fixed: 1200;
  --primitive-z-modal-backdrop: 1300;
  --primitive-z-modal: 1400;
  --primitive-z-popover: 1500;
  --primitive-z-tooltip: 1600;
  --primitive-z-notification: 1700;
  
  /* ===== BREAKPOINTS (for reference) ===== */
  --primitive-breakpoint-sm: 640px;
  --primitive-breakpoint-md: 768px;
  --primitive-breakpoint-lg: 1024px;
  --primitive-breakpoint-xl: 1280px;
  --primitive-breakpoint-2xl: 1536px;
}
```

**Validação**:
```bash
# Test primitive tokens
cat > test-primitives.html << 'TEST'
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="src/styles/tokens/primitive.css">
  <style>
    body { background: var(--primitive-gray-900); color: var(--primitive-gray-50); }
    .test { padding: var(--primitive-space-4); }
  </style>
</head>
<body>
  <div class="test">Primitives loaded!</div>
</body>
</html>
TEST

# Open in browser to verify
```

---

### Step 1.2: Semantic Tokens

Criar arquivo: `src/styles/tokens/semantic.css`

```css
/**
 * SEMANTIC TOKENS - Layer 2
 * Design decisions that reference primitives
 * Can be overridden by themes
 */

:root {
  /* ===== BACKGROUND HIERARCHY ===== */
  --color-bg-primary: var(--primitive-gray-900);
  --color-bg-secondary: var(--primitive-gray-800);
  --color-bg-tertiary: var(--primitive-gray-700);
  --color-bg-elevated: var(--primitive-gray-850);
  --color-bg-overlay: rgba(0, 0, 0, 0.8);
  --color-bg-muted: var(--primitive-gray-600);
  
  /* ===== TEXT HIERARCHY ===== */
  --color-text-primary: var(--primitive-gray-50);
  --color-text-secondary: var(--primitive-gray-400);
  --color-text-subtle: var(--primitive-gray-500);
  --color-text-disabled: var(--primitive-gray-600);
  --color-text-inverse: var(--primitive-gray-900);
  --color-text-on-brand: var(--primitive-gray-50);
  
  /* ===== BRAND COLORS ===== */
  --color-brand-primary: var(--primitive-green-500);
  --color-brand-primary-hover: var(--primitive-green-400);
  --color-brand-primary-active: var(--primitive-green-600);
  --color-brand-secondary: var(--primitive-blue-500);
  --color-brand-secondary-hover: var(--primitive-blue-400);
  
  /* ===== BORDER COLORS ===== */
  --color-border-default: var(--primitive-gray-700);
  --color-border-subtle: var(--primitive-gray-800);
  --color-border-strong: var(--primitive-gray-600);
  --color-border-interactive: var(--color-brand-primary);
  --color-border-focus: var(--color-brand-primary);
  
  /* ===== INTERACTIVE STATES ===== */
  --color-interactive-default: var(--color-brand-primary);
  --color-interactive-hover: var(--color-brand-primary-hover);
  --color-interactive-active: var(--color-brand-primary-active);
  --color-interactive-disabled: var(--primitive-gray-600);
  
  /* ===== STATUS COLORS ===== */
  --color-status-success: var(--primitive-success-500);
  --color-status-success-bg: rgba(16, 185, 129, 0.1);
  --color-status-warning: var(--primitive-warning-500);
  --color-status-warning-bg: rgba(245, 158, 11, 0.1);
  --color-status-error: var(--primitive-error-500);
  --color-status-error-bg: rgba(239, 68, 68, 0.1);
  --color-status-info: var(--primitive-info-500);
  --color-status-info-bg: rgba(59, 130, 246, 0.1);
  
  /* ===== SURFACE ELEVATION ===== */
  --elevation-base: var(--primitive-shadow-xs);
  --elevation-raised: var(--primitive-shadow-md);
  --elevation-overlay: var(--primitive-shadow-lg);
  --elevation-modal: var(--primitive-shadow-2xl);
  
  /* ===== SPACING SYSTEM ===== */
  --spacing-xs: var(--primitive-space-1);
  --spacing-sm: var(--primitive-space-2);
  --spacing-md: var(--primitive-space-4);
  --spacing-lg: var(--primitive-space-8);
  --spacing-xl: var(--primitive-space-12);
  --spacing-2xl: var(--primitive-space-16);
  
  /* Layout Spacing */
  --spacing-layout-xs: var(--primitive-space-2);
  --spacing-layout-sm: var(--primitive-space-4);
  --spacing-layout-md: var(--primitive-space-6);
  --spacing-layout-lg: var(--primitive-space-8);
  --spacing-layout-xl: var(--primitive-space-12);
  
  /* ===== TYPOGRAPHY SYSTEM ===== */
  --font-primary: 'Courier New', 'Monaco', monospace;
  --font-secondary: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
  --font-mono: 'Monaco', 'Courier New', monospace;
  
  --font-size-body: var(--primitive-font-size-base);
  --font-size-small: var(--primitive-font-size-sm);
  --font-size-large: var(--primitive-font-size-lg);
  --font-size-heading: var(--primitive-font-size-2xl);
  
  --font-weight-normal: var(--primitive-font-weight-normal);
  --font-weight-medium: var(--primitive-font-weight-medium);
  --font-weight-bold: var(--primitive-font-weight-bold);
  
  --line-height-body: var(--primitive-line-height-normal);
  --line-height-heading: var(--primitive-line-height-tight);
  
  /* ===== BORDER SYSTEM ===== */
  --border-width-thin: 1px;
  --border-width-thick: 2px;
  --border-width-focus: 2px;
  
  --border-radius-small: var(--primitive-radius-sm);
  --border-radius-default: var(--primitive-radius-md);
  --border-radius-large: var(--primitive-radius-lg);
  --border-radius-full: var(--primitive-radius-full);
  
  /* ===== ANIMATION SYSTEM ===== */
  --transition-fast: var(--primitive-duration-fast) var(--primitive-easing-smooth);
  --transition-normal: var(--primitive-duration-normal) var(--primitive-easing-smooth);
  --transition-slow: var(--primitive-duration-slow) var(--primitive-easing-smooth);
  
  --animation-fade-in: fadeIn var(--primitive-duration-normal) var(--primitive-easing-ease-out);
  --animation-slide-in: slideIn var(--primitive-duration-normal) var(--primitive-easing-smooth);
  
  /* ===== Z-INDEX SYSTEM ===== */
  --z-dropdown: var(--primitive-z-dropdown);
  --z-sticky: var(--primitive-z-sticky);
  --z-modal: var(--primitive-z-modal);
  --z-tooltip: var(--primitive-z-tooltip);
  --z-notification: var(--primitive-z-notification);
}
```

---

### Step 1.3: Component Tokens

Criar arquivo: `src/styles/tokens/component.css`

```css
/**
 * COMPONENT TOKENS - Layer 3
 * Contextual application for specific components
 * References semantic tokens
 */

:root {
  /* ===== BUTTON COMPONENT ===== */
  --button-bg-primary: var(--color-interactive-default);
  --button-bg-primary-hover: var(--color-interactive-hover);
  --button-bg-primary-active: var(--color-interactive-active);
  --button-text-primary: var(--color-text-on-brand);
  
  --button-bg-secondary: var(--color-bg-tertiary);
  --button-bg-secondary-hover: var(--color-bg-secondary);
  --button-text-secondary: var(--color-text-primary);
  
  --button-border-radius: var(--border-radius-default);
  --button-padding-x: var(--spacing-md);
  --button-padding-y: var(--spacing-sm);
  --button-font-weight: var(--font-weight-medium);
  --button-transition: var(--transition-fast);
  
  /* ===== CARD COMPONENT ===== */
  --card-bg: var(--color-bg-secondary);
  --card-bg-hover: var(--color-bg-tertiary);
  --card-border: var(--color-border-subtle);
  --card-shadow: var(--elevation-raised);
  --card-radius: var(--border-radius-default);
  --card-padding: var(--spacing-md);
  
  /* ===== INPUT COMPONENT ===== */
  --input-bg: var(--color-bg-tertiary);
  --input-bg-hover: var(--color-bg-secondary);
  --input-bg-focus: var(--color-bg-tertiary);
  --input-border: var(--color-border-default);
  --input-border-hover: var(--color-border-strong);
  --input-border-focus: var(--color-border-focus);
  --input-text: var(--color-text-primary);
  --input-placeholder: var(--color-text-subtle);
  --input-padding-x: var(--spacing-sm);
  --input-padding-y: var(--spacing-sm);
  --input-radius: var(--border-radius-default);
  
  /* ===== SIDEBAR COMPONENT ===== */
  --sidebar-bg: var(--color-bg-primary);
  --sidebar-border: var(--color-border-subtle);
  --sidebar-item-hover: var(--color-bg-tertiary);
  --sidebar-item-active: var(--color-interactive-default);
  --sidebar-item-active-bg: rgba(0, 255, 65, 0.1);
  --sidebar-width: 16rem;
  --sidebar-padding: var(--spacing-md);
  
  /* ===== HEADER COMPONENT ===== */
  --header-bg: var(--color-bg-elevated);
  --header-border: var(--color-border-subtle);
  --header-height: 4rem;
  --header-shadow: var(--elevation-base);
  --header-padding: var(--spacing-md);
  
  /* ===== MODAL COMPONENT ===== */
  --modal-bg: var(--color-bg-elevated);
  --modal-overlay: var(--color-bg-overlay);
  --modal-shadow: var(--elevation-modal);
  --modal-radius: var(--border-radius-large);
  --modal-padding: var(--spacing-lg);
  
  /* ===== TABLE COMPONENT ===== */
  --table-bg: var(--color-bg-secondary);
  --table-border: var(--color-border-default);
  --table-row-hover: var(--color-bg-tertiary);
  --table-header-bg: var(--color-bg-primary);
  --table-padding: var(--spacing-sm);
  
  /* ===== TOOLTIP COMPONENT ===== */
  --tooltip-bg: var(--color-bg-primary);
  --tooltip-text: var(--color-text-primary);
  --tooltip-shadow: var(--elevation-overlay);
  --tooltip-radius: var(--border-radius-small);
  --tooltip-padding: var(--spacing-xs) var(--spacing-sm);
  
  /* ===== DROPDOWN COMPONENT ===== */
  --dropdown-bg: var(--color-bg-elevated);
  --dropdown-border: var(--color-border-default);
  --dropdown-shadow: var(--elevation-raised);
  --dropdown-item-hover: var(--color-bg-tertiary);
  --dropdown-radius: var(--border-radius-default);
  
  /* ===== BADGE/TAG COMPONENT ===== */
  --badge-bg: var(--color-bg-muted);
  --badge-text: var(--color-text-primary);
  --badge-padding: var(--spacing-xs) var(--spacing-sm);
  --badge-radius: var(--border-radius-full);
  --badge-font-size: var(--font-size-small);
  
  /* ===== WIDGET/PANEL COMPONENT ===== */
  --panel-bg: var(--color-bg-secondary);
  --panel-border: var(--color-border-subtle);
  --panel-shadow: var(--elevation-raised);
  --panel-radius: var(--border-radius-default);
  --panel-padding: var(--spacing-md);
  --panel-header-bg: var(--color-bg-tertiary);
}
```

---

### Step 1.4: Main Token Import

Criar arquivo: `src/styles/tokens/index.css`

```css
/**
 * TOKEN SYSTEM - Main Import
 * Import order matters: Primitive → Semantic → Component
 */

@import './primitive.css';
@import './semantic.css';
@import './component.css';
```

---

### Step 1.5: Theme Manager TypeScript

Criar arquivo: `src/lib/theme/types.ts`

```typescript
/**
 * Theme System Types
 */

export type ThemeCategory = 'hacker' | 'enterprise';

export type HackerTheme = 
  | 'cyber-blue' 
  | 'purple-haze' 
  | 'red-alert' 
  | 'stealth-mode';

export type EnterpriseTheme = 
  | 'corporate-light' 
  | 'corporate-dark' 
  | 'minimal-modern' 
  | 'professional-blue';

export type Theme = HackerTheme | EnterpriseTheme;

export interface ThemeConfig {
  id: Theme;
  name: string;
  category: ThemeCategory;
  description: string;
  icon: string;
  preview: {
    primary: string;
    background: string;
    text: string;
  };
}

export interface ThemeState {
  current: Theme;
  category: ThemeCategory;
  available: Theme[];
}
```

Criar arquivo: `src/lib/theme/theme-configs.ts`

```typescript
import type { Theme, ThemeConfig } from './types';

export const THEME_CONFIGS: Record<Theme, ThemeConfig> = {
  // ===== HACKER THEMES =====
  'cyber-blue': {
    id: 'cyber-blue',
    name: 'Cyber Blue',
    category: 'hacker',
    description: 'Matrix-inspired cyberpunk aesthetic with electric blue accents',
    icon: '⚡',
    preview: {
      primary: '#00d4ff',
      background: '#0a0e14',
      text: '#e0e0e0',
    },
  },
  'purple-haze': {
    id: 'purple-haze',
    name: 'Purple Haze',
    category: 'hacker',
    description: 'Purple team vibes with mystical gradients',
    icon: '💜',
    preview: {
      primary: '#b794f6',
      background: '#1a0f2e',
      text: '#e0e0e0',
    },
  },
  'red-alert': {
    id: 'red-alert',
    name: 'Red Alert',
    category: 'hacker',
    description: 'High alert mode with urgent red tones',
    icon: '🚨',
    preview: {
      primary: '#ff0040',
      background: '#1a0505',
      text: '#e0e0e0',
    },
  },
  'stealth-mode': {
    id: 'stealth-mode',
    name: 'Stealth Mode',
    category: 'hacker',
    description: 'Pure black operations, minimal accents',
    icon: '🥷',
    preview: {
      primary: '#4a5568',
      background: '#000000',
      text: '#e0e0e0',
    },
  },
  
  // ===== ENTERPRISE THEMES =====
  'corporate-light': {
    id: 'corporate-light',
    name: 'Corporate Light',
    category: 'enterprise',
    description: 'Professional light theme for corporate environments',
    icon: '☀️',
    preview: {
      primary: '#0066cc',
      background: '#ffffff',
      text: '#1a1a1a',
    },
  },
  'corporate-dark': {
    id: 'corporate-dark',
    name: 'Corporate Dark',
    category: 'enterprise',
    description: 'Professional dark mode without the cyberpunk',
    icon: '🌙',
    preview: {
      primary: '#4da3ff',
      background: '#1e1e1e',
      text: '#e0e0e0',
    },
  },
  'minimal-modern': {
    id: 'minimal-modern',
    name: 'Minimal Modern',
    category: 'enterprise',
    description: 'Apple-inspired minimal design with generous whitespace',
    icon: '✨',
    preview: {
      primary: '#007aff',
      background: '#ffffff',
      text: '#1a1a1a',
    },
  },
  'professional-blue': {
    id: 'professional-blue',
    name: 'Professional Blue',
    category: 'enterprise',
    description: 'Classic corporate blue in Microsoft style',
    icon: '💼',
    preview: {
      primary: '#0078d4',
      background: '#f3f2f1',
      text: '#1a1a1a',
    },
  },
};

export const HACKER_THEMES: Theme[] = [
  'cyber-blue',
  'purple-haze',
  'red-alert',
  'stealth-mode',
];

export const ENTERPRISE_THEMES: Theme[] = [
  'corporate-light',
  'corporate-dark',
  'minimal-modern',
  'professional-blue',
];

export const DEFAULT_THEME: Theme = 'cyber-blue';
```

---

**CONTINUA COM MAIS 15 STEPS...**

Devido ao limite de tokens, o plano completo tem mais:
- Theme Manager implementation
- React Provider
- FOUC prevention script
- 8 theme CSS files
- ThemeSwitcher component
- Integration steps
- Testing checklist

---

**Validação FASE 1**:
```bash
# Test token system
npm run dev
# Open DevTools → Check CSS variables
# Verify all tokens are defined
```

**Status**: ⚡ FASE 1 READY - Foundation complete!

Quer que eu continue com as outras fases (2-5) ou começamos a implementar? 🚀
