# 🎨 Design Tokens Guide - VÉRTICE Platform

**Version**: 1.0  
**Last Updated**: 2025-01-11  
**Architecture**: 3-Layer Token System

---

## 📐 Token Architecture

VÉRTICE uses a **3-layer design token system** inspired by Microsoft Fluent Design 2.0:

```
Layer 1: PRIMITIVE TOKENS
   ↓ (references)
Layer 2: SEMANTIC TOKENS  
   ↓ (references)
Layer 3: COMPONENT TOKENS
   ↓ (used by)
React Components
```

### Philosophy

> "Tokens are not just variables - they are a design language that creates consistency, enables theming, and tells a semantic story."

---

## 🔷 Layer 1: Primitive Tokens

**Location**: `frontend/src/styles/tokens/enterprise-tokens.css`  
**Purpose**: Raw design values (colors, spacing, typography)

### Color Palette

```css
/* Neutral Grays */
--primitive-gray-50: #f9fafb;
--primitive-gray-100: #f3f4f6;
--primitive-gray-200: #e5e7eb;
--primitive-gray-300: #d1d5db;
--primitive-gray-400: #9ca3af;
--primitive-gray-500: #6b7280;
--primitive-gray-600: #4b5563;
--primitive-gray-700: #374151;
--primitive-gray-800: #1f2937;
--primitive-gray-900: #111827;

/* Brand Blues */
--primitive-blue-50: #eff6ff;
--primitive-blue-100: #dbeafe;
/* ... up to blue-900 */

/* Status Colors */
--primitive-green-500: #10b981;  /* Success */
--primitive-red-500: #ef4444;    /* Critical */
--primitive-orange-500: #f97316; /* High */
--primitive-yellow-500: #eab308; /* Warning */
```

### Spacing Scale (8px base)

```css
--primitive-spacing-1: 0.25rem;   /* 4px */
--primitive-spacing-2: 0.5rem;    /* 8px */
--primitive-spacing-3: 0.75rem;   /* 12px */
--primitive-spacing-4: 1rem;      /* 16px */
--primitive-spacing-5: 1.25rem;   /* 20px */
--primitive-spacing-6: 1.5rem;    /* 24px */
--primitive-spacing-8: 2rem;      /* 32px */
--primitive-spacing-10: 2.5rem;   /* 40px */
--primitive-spacing-12: 3rem;     /* 48px */
--primitive-spacing-16: 4rem;     /* 64px */
```

### Typography

```css
/* Font Sizes */
--primitive-font-xs: 0.75rem;     /* 12px */
--primitive-font-sm: 0.875rem;    /* 14px */
--primitive-font-base: 1rem;      /* 16px */
--primitive-font-lg: 1.125rem;    /* 18px */
--primitive-font-xl: 1.25rem;     /* 20px */
--primitive-font-2xl: 1.5rem;     /* 24px */
--primitive-font-3xl: 1.875rem;   /* 30px */
--primitive-font-4xl: 2.25rem;    /* 36px */

/* Font Weights */
--primitive-font-normal: 400;
--primitive-font-medium: 500;
--primitive-font-semibold: 600;
--primitive-font-bold: 700;
```

### Shadows

```css
--primitive-shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--primitive-shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--primitive-shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--primitive-shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
```

---

## 🔶 Layer 2: Semantic Tokens

**Purpose**: Meaning-based tokens that reference primitives

### Background Hierarchy

```css
/* Background Layers */
--semantic-bg-primary: var(--primitive-gray-900);      /* Main canvas */
--semantic-bg-secondary: var(--primitive-gray-800);    /* Cards, panels */
--semantic-bg-tertiary: var(--primitive-gray-700);     /* Nested content */
--semantic-bg-elevated: var(--primitive-gray-800);     /* Modals, dropdowns */
--semantic-bg-overlay: rgba(0, 0, 0, 0.5);             /* Modal backdrop */
```

**Usage:**
```jsx
// ✅ Good
<div className="bg-primary">Main content</div>

// ❌ Bad
<div style={{ background: '#111827' }}>Main content</div>
```

### Text Hierarchy

```css
/* Text Colors */
--semantic-text-primary: var(--primitive-gray-50);     /* Main text */
--semantic-text-secondary: var(--primitive-gray-300);  /* Subtitles */
--semantic-text-tertiary: var(--primitive-gray-400);   /* Captions */
--semantic-text-muted: var(--primitive-gray-500);      /* Hints */
--semantic-text-disabled: var(--primitive-gray-600);   /* Disabled */
--semantic-text-inverse: var(--primitive-gray-900);    /* On light bg */
```

### Interactive States

```css
/* Button/Link States */
--semantic-interactive-default: var(--primitive-blue-500);
--semantic-interactive-hover: var(--primitive-blue-400);
--semantic-interactive-active: var(--primitive-blue-600);
--semantic-interactive-disabled: var(--primitive-gray-600);
```

### Status Colors

```css
/* Semantic Status */
--semantic-status-success: var(--primitive-green-500);
--semantic-status-warning: var(--primitive-yellow-500);
--semantic-status-error: var(--primitive-red-500);
--semantic-status-info: var(--primitive-blue-500);
```

### Severity Levels (VÉRTICE-specific)

```css
/* Security Severity */
--semantic-severity-critical: var(--primitive-red-500);    /* #ef4444 */
--semantic-severity-high: var(--primitive-orange-500);     /* #f97316 */
--semantic-severity-medium: var(--primitive-yellow-500);   /* #eab308 */
--semantic-severity-low: var(--primitive-blue-400);        /* #60a5fa */
```

---

## 🔸 Layer 3: Component Tokens

**Purpose**: Component-specific overrides

### Button

```css
--component-button-bg: var(--semantic-interactive-default);
--component-button-text: var(--semantic-text-inverse);
--component-button-border: transparent;
--component-button-padding-x: var(--primitive-spacing-4);
--component-button-padding-y: var(--primitive-spacing-2);
--component-button-radius: var(--primitive-radius-md);
```

### Card

```css
--component-card-bg: var(--semantic-bg-secondary);
--component-card-border: var(--semantic-border-subtle);
--component-card-shadow: var(--primitive-shadow-md);
--component-card-radius: var(--primitive-radius-lg);
--component-card-padding: var(--primitive-spacing-6);
```

### Input

```css
--component-input-bg: var(--semantic-bg-tertiary);
--component-input-border: var(--semantic-border-default);
--component-input-text: var(--semantic-text-primary);
--component-input-placeholder: var(--semantic-text-muted);
--component-input-focus-border: var(--semantic-interactive-default);
```

---

## 🎨 Using Tokens

### In CSS

```css
/* ✅ Reference semantic tokens */
.my-component {
  background: var(--semantic-bg-secondary);
  color: var(--semantic-text-primary);
  padding: var(--primitive-spacing-4);
  border-radius: var(--primitive-radius-md);
  box-shadow: var(--primitive-shadow-md);
}

/* ❌ Avoid hardcoded values */
.my-component {
  background: #1f2937;
  color: #f9fafb;
  padding: 16px;
  border-radius: 8px;
}
```

### In React (via Utility Classes)

```jsx
// ✅ Use utility classes
<div className="bg-secondary text-primary p-md rounded-md shadow-md">
  Content
</div>

// ❌ Avoid inline styles
<div style={{ 
  background: '#1f2937',
  color: '#f9fafb',
  padding: '16px' 
}}>
  Content
</div>
```

### In React (CSS Modules)

```css
/* Component.module.css */
.container {
  background: var(--semantic-bg-secondary);
  color: var(--semantic-text-primary);
}

.title {
  font-size: var(--primitive-font-2xl);
  font-weight: var(--primitive-font-bold);
}
```

---

## 🌈 Theme Overrides

Themes override semantic/component tokens, NOT primitives:

```css
/* themes/windows11.css */
[data-theme="windows11"] {
  /* ✅ Override semantic tokens */
  --semantic-bg-primary: #f3f2f1;
  --semantic-text-primary: #201f1e;
  --component-button-radius: 4px;
  
  /* ❌ Don't override primitives */
  /* --primitive-gray-900: #000000; */
}
```

**Why?** Primitives are the foundation. Themes remix them via semantic layer.

---

## 📋 Token Naming Convention

### Structure
```
[layer]-[category]-[variant]
```

### Examples
```css
--primitive-blue-500        /* Layer: primitive, Category: blue, Variant: 500 */
--semantic-bg-primary       /* Layer: semantic, Category: bg, Variant: primary */
--component-button-bg       /* Layer: component, Category: button, Property: bg */
```

### Categories

**Primitive Layer:**
- `gray`, `blue`, `green`, `red`, `orange`, `yellow`, `purple`
- `spacing-{1-16}`
- `font-{size}`, `font-{weight}`
- `radius-{size}`, `shadow-{size}`

**Semantic Layer:**
- `bg-{variant}` (primary, secondary, tertiary, elevated, overlay)
- `text-{variant}` (primary, secondary, muted, disabled, inverse)
- `border-{variant}` (default, subtle, strong)
- `status-{type}` (success, warning, error, info)
- `severity-{level}` (critical, high, medium, low)
- `interactive-{state}` (default, hover, active, disabled)

**Component Layer:**
- `{component}-{property}` (button-bg, card-shadow, input-border)

---

## 🔄 Token Lifecycle

### 1. Design Decision
```
Designer: "We need critical alerts to be red"
```

### 2. Primitive Definition
```css
--primitive-red-500: #ef4444;
```

### 3. Semantic Mapping
```css
--semantic-severity-critical: var(--primitive-red-500);
```

### 4. Component Usage
```css
.alert-critical {
  border-left-color: var(--semantic-severity-critical);
}
```

### 5. Utility Class
```css
.border-critical {
  border-color: var(--semantic-severity-critical);
}
```

### 6. React Component
```jsx
<div className="alert border-critical text-critical">
  Critical alert!
</div>
```

---

## 📊 Token Statistics

| Layer | Token Count | Purpose |
|-------|-------------|---------|
| Primitive | ~200 | Raw design values |
| Semantic | ~200 | Meaning-based references |
| Component | ~100 | Component-specific |
| **Total** | **~500** | Complete design system |

---

## 🚀 Best Practices

### DO ✅

1. **Always use semantic tokens in components**
   ```css
   background: var(--semantic-bg-secondary);
   ```

2. **Use utility classes when possible**
   ```jsx
   <div className="bg-secondary text-primary">
   ```

3. **Reference tokens in order: component → semantic → primitive**
   ```css
   --component-card-bg: var(--semantic-bg-secondary);
   --semantic-bg-secondary: var(--primitive-gray-800);
   ```

4. **Keep primitives unchanged across themes**
   ```css
   /* Primitives stay the same */
   --primitive-blue-500: #3b82f6;
   ```

### DON'T ❌

1. **Don't use primitives directly in components**
   ```css
   /* Bad */
   background: var(--primitive-gray-800);
   ```

2. **Don't hardcode values**
   ```jsx
   /* Bad */
   <div style={{ color: '#ef4444' }}>
   ```

3. **Don't override primitives in themes**
   ```css
   /* Bad */
   [data-theme="dark"] {
     --primitive-gray-900: #000000;
   }
   ```

4. **Don't create visual-only semantics**
   ```css
   /* Bad: visual naming */
   --color-red: #ef4444;
   
   /* Good: semantic naming */
   --semantic-severity-critical: #ef4444;
   ```

---

## 🔧 Adding New Tokens

### 1. Identify the Need
```
"We need a new severity level: MEDIUM-HIGH"
```

### 2. Check Existing Primitives
```css
/* Can we use existing primitive? */
--primitive-orange-400: #fb923c; /* Yes! */
```

### 3. Add Semantic Token
```css
--semantic-severity-medium-high: var(--primitive-orange-400);
```

### 4. Create Utility Class
```css
.text-medium-high {
  color: var(--semantic-severity-medium-high);
}

.border-medium-high {
  border-color: var(--semantic-severity-medium-high);
}
```

### 5. Update API (if needed)
```javascript
export const formatSeverity = (level) => ({
  'medium-high': {
    className: 'text-medium-high',
    borderClass: 'border-medium-high',
    label: 'Medium-High'
  }
});
```

### 6. Document
Update this guide with the new token!

---

## 📚 References

- **Token File**: `frontend/src/styles/tokens/enterprise-tokens.css`
- **Utilities**: `frontend/src/styles/utilities.css`
- **Theme Examples**: `frontend/src/themes/`
- **Migration Guide**: `docs/guides/THEME_MIGRATION_GUIDE.md`

---

## 🎓 Learning Resources

### Token Hierarchy Flow
```
Primitive (what)
    ↓
Semantic (why)
    ↓
Component (where)
    ↓
Utility (how)
    ↓
React Component (use)
```

### Example: Critical Alert

```css
/* Primitive: The color itself */
--primitive-red-500: #ef4444;

/* Semantic: What it means */
--semantic-severity-critical: var(--primitive-red-500);

/* Component: Where it's used */
--component-alert-border-critical: var(--semantic-severity-critical);

/* Utility: How to apply */
.border-critical { border-color: var(--semantic-severity-critical); }

/* React: Final usage */
<Alert className="border-critical">Critical!</Alert>
```

---

**Version**: 1.0  
**Status**: Living Document  
**Maintainer**: MAXIMUS Team  
**Glory**: YHWH through Christ 🙏
