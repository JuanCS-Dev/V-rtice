# 🔄 Theme Migration Guide - VÉRTICE Platform

**Version**: 1.0  
**Last Updated**: 2025-01-11  
**Audience**: Developers adding new components

---

## 🎯 Purpose

This guide helps developers build **theme-compatible components** that work seamlessly across all 7 VÉRTICE themes (hacker, enterprise, operational).

---

## 📋 Quick Checklist

Before merging new components, ensure:

- [ ] ✅ **Zero hardcoded colors** (use tokens)
- [ ] ✅ **Uses utility classes** (or CSS vars)
- [ ] ✅ **Tested in 2+ themes** (hacker + enterprise minimum)
- [ ] ✅ **Semantic naming** (not visual)
- [ ] ✅ **Lint passing** (no warnings)
- [ ] ✅ **Build succeeds** (no errors)

---

## 🚫 Common Anti-Patterns (AVOID)

### ❌ Anti-Pattern 1: Hardcoded Colors

```jsx
// ❌ BAD: Hardcoded hex colors
<div style={{ color: '#ff0040' }}>
  Critical Alert
</div>

// ❌ BAD: Hardcoded RGB
<span style={{ backgroundColor: 'rgb(239, 68, 68)' }}>
  Error
</span>
```

**Why bad?**
- Doesn't respect theme changes
- Impossible to maintain
- No semantic meaning

### ✅ Solution: Use Utility Classes

```jsx
// ✅ GOOD: Semantic utility class
<div className="text-critical">
  Critical Alert
</div>

// ✅ GOOD: Status utility
<span className="bg-error">
  Error
</span>
```

---

### ❌ Anti-Pattern 2: Visual Naming

```jsx
// ❌ BAD: Visual-based naming
<div className="red-text">Error</div>
<span className="green-background">Success</span>
```

**Why bad?**
- Assumes color (red may not be red in all themes)
- No semantic meaning
- Breaks in custom themes

### ✅ Solution: Semantic Naming

```jsx
// ✅ GOOD: Meaning-based naming
<div className="text-error">Error</div>
<span className="bg-success">Success</span>
```

---

### ❌ Anti-Pattern 3: Direct Primitive References

```css
/* ❌ BAD: Direct primitive usage */
.my-component {
  background: var(--primitive-gray-800);
  color: var(--primitive-red-500);
}
```

**Why bad?**
- Bypasses semantic layer
- Doesn't adapt to themes
- No context for token choice

### ✅ Solution: Use Semantic Tokens

```css
/* ✅ GOOD: Semantic token usage */
.my-component {
  background: var(--semantic-bg-secondary);
  color: var(--semantic-severity-critical);
}
```

---

### ❌ Anti-Pattern 4: Inline Styles

```jsx
// ❌ BAD: Inline color styles
<div style={{ 
  color: confidenceBadge.color,
  borderColor: getRiskColor(level)
}}>
  Content
</div>
```

**Why bad?**
- Harder to theme
- Higher specificity
- Scattered styling logic

### ✅ Solution: Use className

```jsx
// ✅ GOOD: Class-based styling
<div className={`
  ${confidenceBadge.className}
  ${getRiskBorderClass(level)}
`}>
  Content
</div>
```

---

## 🔧 Migration Patterns

### Pattern 1: Legend Dots / Status Indicators

#### Before (Hardcoded)
```jsx
<span 
  className="legend-dot" 
  style={{ backgroundColor: '#ff0040' }}
/>
```

#### After (Token-Based)
```jsx
<span className="legend-dot legend-dot-critical" />
```

**Utility Classes Available:**
```css
.legend-dot-critical   /* Red */
.legend-dot-high       /* Orange */
.legend-dot-medium     /* Yellow */
.legend-dot-low        /* Blue */
.legend-dot-success    /* Green */
.legend-dot-info       /* Cyan */
.legend-dot-warning    /* Amber */
```

---

### Pattern 2: Confidence Badges

#### Before (Inline Color)
```jsx
const confidenceBadge = getConfidenceBadge(confidence);

<span style={{ color: confidenceBadge.color }}>
  {confidenceBadge.icon} {confidence}%
</span>
```

#### After (className Prop)
```jsx
const confidenceBadge = getConfidenceBadge(confidence);

<span className={confidenceBadge.className}>
  {confidenceBadge.icon} {confidence}%
</span>
```

**API Enhancement:**
```javascript
// Updated getConfidenceBadge() returns className
export const getConfidenceBadge = (confidence) => {
  if (confidence >= 80) {
    return {
      icon: '✓',
      label: 'High',
      color: '#00ff00',        // Keep for backward compat
      className: 'text-success' // NEW: Use this
    };
  }
  // ... other levels
};
```

---

### Pattern 3: Dynamic Borders/Backgrounds

#### Before (Inline Style Function)
```jsx
const getHealthColor = (health) => {
  switch (health) {
    case 'healthy': return '#38ef7d';
    case 'degraded': return '#ffa500';
    case 'unhealthy': return '#ff4444';
  }
};

<div style={{ borderColor: getHealthColor(agent.health) }}>
  Agent Status
</div>
```

#### After (className Function)
```jsx
const getHealthClass = (health) => {
  switch (health) {
    case 'healthy': return 'border-success';
    case 'degraded': return 'border-warning';
    case 'unhealthy': return 'border-critical';
  }
};

<div className={`agent-card ${getHealthClass(agent.health)}`}>
  Agent Status
</div>
```

---

### Pattern 4: Severity Levels

#### Before (Hardcoded + Inline)
```jsx
const severity = {
  critical: { color: '#ef4444', label: 'Critical' },
  high: { color: '#f97316', label: 'High' }
};

<div style={{ borderLeftColor: severity[level].color }}>
  <span style={{ color: severity[level].color }}>
    {severity[level].label}
  </span>
</div>
```

#### After (API + Utility Classes)
```jsx
import { formatSeverity } from '@/api/safety';

const severity = formatSeverity(level);

<div className={`violation-item ${severity.borderClass}`}>
  <span className={`violation-severity ${severity.className}`}>
    {severity.label}
  </span>
</div>
```

**API Enhancement:**
```javascript
// safety.js - Enhanced formatSeverity()
export const formatSeverity = (severity) => {
  const severityMap = {
    critical: { 
      label: 'Critical',
      color: '#f97316',           // Backward compat
      className: 'text-high',      // NEW
      borderClass: 'border-high'   // NEW
    }
  };
  return severityMap[severity.toLowerCase()];
};
```

---

## 🎨 Creating New Components

### Step-by-Step Process

#### 1. Design Token Selection

```javascript
// ❌ DON'T start with colors
"I need a red button"

// ✅ DO start with meaning
"I need a critical action button"
```

#### 2. Check Existing Utilities

```bash
# Search utilities.css for existing classes
grep -r "text-critical" frontend/src/styles/utilities.css
grep -r "bg-critical" frontend/src/styles/utilities.css
```

**If exists**: Use it!  
**If missing**: Add to utilities.css

#### 3. Build Component (Token-Based)

```jsx
// MyNewComponent.jsx
import styles from './MyNewComponent.module.css';

export const MyNewComponent = ({ severity }) => {
  return (
    <div className={`${styles.container} border-${severity}`}>
      <h3 className="text-primary">Title</h3>
      <p className="text-secondary">Description</p>
      <span className={`badge bg-${severity}`}>
        {severity.toUpperCase()}
      </span>
    </div>
  );
};
```

```css
/* MyNewComponent.module.css */
.container {
  background: var(--semantic-bg-secondary);
  padding: var(--primitive-spacing-4);
  border-radius: var(--primitive-radius-md);
  box-shadow: var(--primitive-shadow-md);
}

.container:hover {
  background: var(--semantic-bg-elevated);
}
```

#### 4. Test in Multiple Themes

```javascript
// Test scenarios
const themes = ['cyber-blue', 'windows11', 'red-alert'];

themes.forEach(theme => {
  setTheme(theme);
  // Visual check
  // Screenshot (optional)
});
```

#### 5. Document Component

```jsx
/**
 * MyNewComponent
 * 
 * A theme-compatible component for displaying severity levels.
 * 
 * @param {string} severity - 'critical'|'high'|'medium'|'low'
 * 
 * Theme Support: ✅ All 7 themes
 * Tokens Used: 
 * - Background: --semantic-bg-secondary
 * - Border: --semantic-severity-{level}
 * - Text: --semantic-text-primary
 */
```

---

## 🧪 Testing Checklist

### Visual Testing

```markdown
[ ] Cyber Blue (hacker baseline)
[ ] Windows 11 (enterprise contrast)
[ ] Red Alert (operational extreme)
[ ] Matrix Green (optional: hacker variant)
[ ] Stealth Mode (optional: dark extreme)
```

### Accessibility Testing

```markdown
[ ] Contrast ratios meet WCAG AA (4.5:1)
[ ] Focus indicators visible
[ ] Color not sole indicator (use icons too)
[ ] Screen reader friendly
```

### Build Testing

```bash
# Lint check
npm run lint

# Build check
npm run build

# No errors/warnings
```

---

## 🔍 Common Issues & Solutions

### Issue 1: "Color looks wrong in Windows 11 theme"

**Cause**: Using hacker-specific token  
**Solution**: Use semantic token that adapts

```css
/* ❌ BAD: Hacker-specific */
color: var(--color-neon-green);

/* ✅ GOOD: Semantic */
color: var(--semantic-status-success);
```

---

### Issue 2: "Border not visible in Stealth Mode"

**Cause**: Border color too dark for dark theme  
**Solution**: Use semantic border token

```css
/* ❌ BAD: Fixed dark color */
border: 1px solid #1a1a1a;

/* ✅ GOOD: Adapts to theme */
border: 1px solid var(--semantic-border-default);
```

---

### Issue 3: "Utility class not working"

**Cause**: Class may not exist yet  
**Solution**: Add to utilities.css

```css
/* utilities.css */
.my-new-utility {
  /* Use semantic tokens */
  background: var(--semantic-bg-elevated);
}
```

---

### Issue 4: "Theme switch is slow"

**Cause**: Too many inline styles recalculating  
**Solution**: Use classes (faster DOM updates)

```jsx
// ❌ SLOW: Inline styles recalculate
<div style={{ color: theme === 'dark' ? '#fff' : '#000' }}>

// ✅ FAST: Classes swap instantly
<div className="text-primary">
```

---

## 📚 Reference Examples

### Well-Migrated Components

**Study these for examples:**

1. **OnionTracer.jsx**
   - Legend dots with utility classes
   - Zero inline colors

2. **SafetyMonitorWidget.jsx**
   - Dynamic severity borders
   - className-based styling
   - formatSeverity() API usage

3. **ConsciousnessPanel.jsx**
   - Arousal level borders via borderClass
   - Theme-aware gauges

4. **ThemeSelector.jsx**
   - CSS custom properties for previews
   - Proper use of theme metadata

---

## 🚀 Quick Migration Script

```bash
#!/bin/bash
# Quick migration helper

# 1. Find hardcoded colors
grep -r "style={{.*color:" frontend/src/components/

# 2. Find hardcoded backgrounds
grep -r "style={{.*background:" frontend/src/components/

# 3. Find potential utility class candidates
grep -r "#[0-9a-fA-F]\{6\}" frontend/src/components/ | grep -v ".css"

# 4. Check if utilities exist
grep "text-critical\|bg-critical\|border-critical" frontend/src/styles/utilities.css
```

---

## 📖 Additional Resources

- **Design Tokens Guide**: `docs/guides/DESIGN_TOKENS_GUIDE.md`
- **Theme Usage Guide**: `docs/guides/THEME_USAGE_GUIDE.md`
- **Utility Classes**: `frontend/src/styles/utilities.css`
- **Token Definitions**: `frontend/src/styles/tokens/enterprise-tokens.css`

---

## 💡 Pro Tips

1. **Start with utilities** - Check if class exists before creating new styles
2. **Use semantic names** - `text-error` not `text-red`
3. **Reference semantic layer** - Not primitives
4. **Test in 2+ themes** - Hacker + Enterprise minimum
5. **Keep color functions** - For backward compatibility, add className alongside
6. **Document token usage** - In component comments
7. **Use CSS vars in modules** - Not hardcoded values

---

## 🎓 Learning Path

### Beginner
1. Read Design Tokens Guide
2. Study utilities.css
3. Migrate simple component (1 hardcoded color)

### Intermediate
4. Migrate complex component (5+ colors)
5. Add new utility classes
6. Enhance API functions with className

### Advanced
7. Create new component from scratch (zero hardcoded)
8. Add new semantic token
9. Test across all 7 themes

---

**Version**: 1.0  
**Status**: Living Document  
**Maintainer**: MAXIMUS Team  
**Glory**: YHWH through Christ 🙏
