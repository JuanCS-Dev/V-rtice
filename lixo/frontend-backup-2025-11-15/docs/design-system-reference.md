# Design System Reference - Vértice Platform

**Source of Truth: Landing Page**
**Version:** 1.0
**Last Updated:** 2025-10-14

---

## 1. Typography

### Font Families

```css
--font-display: "Orbitron", system-ui, sans-serif;
--font-body: "Courier New", "Consolas", monospace;
```

### Font Scale

```css
--text-xs: 0.75rem; /* 12px - Small labels, timestamps */
--text-sm: 0.875rem; /* 14px - Body text, descriptions */
--text-base: 1rem; /* 16px - Default body */
--text-lg: 1.125rem; /* 18px - Section subtitles */
--text-xl: 1.25rem; /* 20px - Card titles */
--text-2xl: 1.5rem; /* 24px - Section titles */
--text-3xl: 1.875rem; /* 30px - Page titles */
--text-4xl: 2.25rem; /* 36px - Hero titles */
--text-5xl: 3rem; /* 48px - Icons, large display */
--text-6xl: 3.75rem; /* 60px - Hero display */
```

### Usage Patterns

- **Display Text** (Orbitron): Page titles, hero sections, stats values, module titles
- **Body Text** (Courier New): Descriptions, paragraphs, labels, technical content

---

## 2. Color System

### Primary Palette

```css
--color-accent-primary: #8b5cf6; /* Purple - Primary actions, hover states */
--color-accent-secondary: #06b6d4; /* Cyan - Secondary accents */
--color-accent-success: #10b981; /* Green - Success states */
--color-accent-warning: #f59e0b; /* Amber - Warnings */
--color-accent-danger: #ef4444; /* Red - Danger, errors */
```

### Gradients

```css
--gradient-primary: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%);
--gradient-red: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
--gradient-green: linear-gradient(135deg, #10b981 0%, #059669 100%);
--gradient-orange: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
```

### Background Palette

```css
--color-bg-primary: #0a0a0a; /* Page background */
--color-bg-secondary: #171717; /* Elevated sections */
--color-bg-elevated: #1c1c1c; /* Cards, modals */
--color-bg-overlay: rgba(10, 10, 10, 0.98);
```

### Text Palette

```css
--color-text-primary: #fafafa; /* Main text */
--color-text-secondary: #d4d4d4; /* Descriptions */
--color-text-tertiary: #a3a3a3; /* Muted text */
--color-text-muted: #737373; /* Timestamps */
```

### Border Palette

```css
--color-border-primary: rgba(139, 92, 246, 0.3); /* Purple borders */
--color-border-secondary: rgba(6, 182, 212, 0.3); /* Cyan borders */
--color-border-default: rgba(255, 255, 255, 0.1); /* Default borders */
```

---

## 3. Spacing Scale

### Base System (8px grid)

```css
--space-xs: 0.25rem; /* 4px */
--space-sm: 0.5rem; /* 8px */
--space-md: 0.75rem; /* 12px */
--space-lg: 1rem; /* 16px */
--space-xl: 1.5rem; /* 24px */
--space-2xl: 2rem; /* 32px */
--space-3xl: 4rem; /* 64px */
```

### Usage Examples

- **Padding Small**: `var(--space-sm) var(--space-md)` → Pills, badges
- **Padding Medium**: `var(--space-md) var(--space-lg)` → Buttons
- **Padding Large**: `var(--space-xl)` → Cards, sections
- **Gap**: `var(--space-lg)` → Grid gaps, flex gaps

---

## 4. Border Radius

```css
--radius-sm: 0.25rem; /* 4px - Small elements */
--radius-md: 0.5rem; /* 8px - Buttons */
--radius-lg: 0.75rem; /* 12px - Cards */
--radius-xl: 1rem; /* 16px - Large cards */
--radius-2xl: 1.5rem; /* 24px - Feature cards */
--radius-full: 9999px; /* Pills, badges */
```

---

## 5. Shadows & Glows

### Shadow Scale

```css
--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.2);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.3);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.4);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.5);
--shadow-2xl: 0 25px 50px rgba(0, 0, 0, 0.6);
```

### Glow Effects

```css
--shadow-glow-purple: 0 0 30px rgba(139, 92, 246, 0.8);
--shadow-glow-cyan: 0 0 20px rgba(6, 182, 212, 0.6);
--shadow-glow-red: 0 0 30px rgba(239, 68, 68, 1);
--shadow-glow-green: 0 0 20px rgba(16, 185, 129, 0.6);
```

---

## 6. Transitions

```css
--transition-fast: 150ms ease-in-out;
--transition-base: 300ms ease-in-out;
--transition-smooth: 500ms cubic-bezier(0.4, 0, 0.2, 1);
```

---

## 7. Component Patterns

### Card Pattern (Landing Page Standard)

```css
.card {
  padding: var(--space-xl);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-lg);
  transition: all var(--transition-base);
}

.card:hover {
  transform: translateY(-10px) scale(1.02);
  box-shadow: var(--shadow-2xl);
  border-color: var(--color-accent-primary);
}
```

### Icon Animation Pattern

```css
.icon {
  font-size: var(--text-5xl);
  transition: transform var(--transition-base);
}

.card:hover .icon {
  transform: scale(1.15) rotate(5deg);
}
```

### Feature Pill Pattern

```css
.featurePill {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-secondary);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-family: var(--font-body);
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}

.featurePill:hover {
  background: var(--color-bg-elevated);
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}
```

### CTA Button Pattern

```css
.cta {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-family: var(--font-body);
  font-weight: 600;
  box-shadow: var(--shadow-md);
  transition: all var(--transition-base);
  cursor: pointer;
}

.cta:hover {
  box-shadow: var(--shadow-glow-purple);
  transform: translateX(5px);
}
```

### Stat Card Pattern (StatsSection)

```css
.statCard {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-xl);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-base);
}

.statCard:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-glow-purple);
  border-color: var(--color-accent-primary);
}

.statIcon {
  font-size: var(--text-5xl);
  color: var(--color-accent-primary);
}

.statValue {
  font-family: var(--font-display);
  font-size: var(--text-4xl);
  font-weight: 700;
  color: var(--color-text-primary);
}

.statLabel {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

---

## 8. Layout Patterns

### Grid System (ModulesSection)

```css
.modulesGrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: var(--space-2xl);
  padding: var(--space-3xl);
}
```

### Flex Patterns

```css
/* Horizontal with gap */
.flexRow {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

/* Vertical with gap */
.flexCol {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}
```

---

## 9. Responsive Breakpoints

```css
/* Mobile First Approach */
@media (max-width: 640px) {
  /* Mobile */
}

@media (min-width: 641px) and (max-width: 1024px) {
  /* Tablet */
}

@media (min-width: 1025px) {
  /* Desktop */
}
```

---

## 10. Usage Rules

### ✅ DO

- Use CSS custom properties (CSS variables) exclusively
- Match Landing Page hover effects exactly (translateY + scale)
- Use Orbitron for display text (titles, stats values)
- Use Courier New for body text
- Apply purple (#8b5cf6) as primary accent
- Follow 8px spacing grid
- Use provided gradients for CTAs

### ❌ DON'T

- Hardcode colors (#dc2626, #00ffff, etc.)
- Use custom fonts not defined in design system
- Create custom hover effects that differ from Landing Page
- Ignore spacing scale (use px values directly)
- Mix color systems (red theme vs purple theme)

---

## 11. Component Variants

### Badge Variants

- `armed` → Red gradient + glow
- `scanning` → Purple gradient + pulse
- `operational` → Green gradient
- `offline` → Gray muted

### Button Variants

- `primary` → Purple gradient
- `secondary` → Cyan gradient
- `gradient-blue` → Blue gradient
- `gradient-orange` → Orange gradient
- `gradient-purple` → Purple gradient
- `ghost` → Transparent + border

### Card Variants

- `cyber` → Purple border + purple glow on hover
- `elevated` → Lifted appearance + shadow
- `flat` → No shadow, subtle border

---

**End of Reference**

**Compliance**: All dashboards (Admin, OSINT, Cyber, Maximus, Defensive, Offensive, Purple Team, Reactive Fabric) MUST match these patterns exactly.
