# 🎨 MAXIMUS Vértice - Visual Style Guide

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: 2025-10-13

---

## 🌈 Color System

### Theme Architecture

MAXIMUS uses a sophisticated theme system with 6 premium themes, each optimized for different scenarios and user preferences.

#### Primary Themes

**1. Matrix Green** - Default Hacker Aesthetic
```css
--primary: #00ff00
--secondary: #00cc00
--background: #0d0208
--text: #39ff14
```
Use when: Terminal operations, OSINT, code analysis

**2. Cyber Blue** - Cyberpunk Vibes
```css
--primary: #00d9ff
--secondary: #0099cc
--background: #0a0e27
--text: #00d9ff
```
Use when: Network scanning, threat intelligence

**3. Purple Haze** - Mysterious & Deep
```css
--primary: #a855f7
--secondary: #7c3aed
--background: #0f0a1e
--text: #c084fc
```
Use when: Purple team operations, analysis

**4. Red Alert** - High Urgency
```css
--primary: #ff0040
--secondary: #cc0033
--background: #1a0000
--text: #ff3366
```
Use when: Offensive operations, alerts, incidents

**5. Windows 11** - Enterprise Clean
```css
--primary: #0078d4
--secondary: #005a9e
--background: #f3f3f3
--text: #1f1f1f
```
Use when: Business presentations, compliance reports

**6. Stealth** - Professional Dark
```css
--primary: #64748b
--secondary: #475569
--background: #0f172a
--text: #cbd5e1
```
Use when: Covert operations, minimal UI

### Semantic Colors

All themes inherit semantic colors that adapt:

```css
--success: Theme-adapted green
--warning: Theme-adapted yellow
--error: Theme-adapted red
--info: Theme-adapted blue
```

---

## 📝 Typography

### Font Stack

```css
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
--font-mono: 'Fira Code', 'JetBrains Mono', 'Consolas', monospace
--font-display: 'Orbitron', 'Exo 2', sans-serif
```

### Type Scale

```css
--text-xs: 0.75rem    /* 12px */
--text-sm: 0.875rem   /* 14px */
--text-base: 1rem     /* 16px */
--text-lg: 1.125rem   /* 18px */
--text-xl: 1.25rem    /* 20px */
--text-2xl: 1.5rem    /* 24px */
--text-3xl: 1.875rem  /* 30px */
--text-4xl: 2.25rem   /* 36px */
```

---

## 🎭 Animation System

### Duration Tokens

```css
--duration-instant: 50ms
--duration-fast: 150ms
--duration-normal: 250ms
--duration-slow: 500ms
```

### Easing Functions

```css
--ease-standard: cubic-bezier(0.4, 0, 0.2, 1)
--ease-decelerate: cubic-bezier(0, 0, 0.2, 1)
--ease-accelerate: cubic-bezier(0.4, 0, 1, 1)
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55)
```

---

## 🔘 Component Patterns

### Buttons

```jsx
<Button variant="primary" size="md">Save</Button>
<Button variant="danger">Delete</Button>
<IconButton icon={CloseIcon} label="Close" />
```

### Forms

```jsx
<Input
  label="Email"
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  required
  error={error}
/>
```

---

## ♿ Accessibility

- All themes meet WCAG 2.1 AA (4.5:1 contrast)
- Focus indicators on all interactive elements
- Screen reader support
- Keyboard navigation complete
- Semantic HTML

---

## 📱 Responsive Breakpoints

```css
--screen-sm: 640px
--screen-md: 768px
--screen-lg: 1024px
--screen-xl: 1280px
```

---

## 🎯 Best Practices

✅ **DO**: Use theme variables, test all themes, check contrast  
❌ **DON'T**: Hardcode colors, skip accessibility, ignore keyboard

---

**Built with ❤️ and ⚡ by the MAXIMUS Team**  
**Em nome de Jesus! 🙏**
