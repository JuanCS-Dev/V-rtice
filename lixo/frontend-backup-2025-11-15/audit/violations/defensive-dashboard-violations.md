# DefensiveDashboard - Visual Violations Report

**Generated:** 2025-10-14
**Reference:** Landing Page Design System v1.0.0
**Audit Scope:** DefensiveDashboard components

---

## Summary

- **Total violations:** 35
- **Critical (P0):** 18
- **High (P1):** 10
- **Medium (P2):** 7

---

## Violations by Category

### 1. Hardcoded Colors (15 violations)

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/DefensiveDashboard.module.css:72`

**Found:** `box-shadow: 0 0 40px rgba(139, 92, 246, 1);`
**Expected:** `box-shadow: var(--shadow-glow-purple);` (defined as `0 0 30px rgba(139, 92, 246, 0.8)`)
**Severity:** P1
**Fix:** Replace with design token or adjust to match standard shadow value

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:16`

**Found:** `background: linear-gradient(180deg, rgba(139, 92, 246, 0.05) 0%, rgba(0, 0, 0, 0.4) 100%);`
**Expected:** Use design token gradients or background colors
**Severity:** P0
**Fix:** Replace with `var(--gradient-primary)` or create proper token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:26`

**Found:** `background: rgba(0, 0, 0, 0.5);`
**Expected:** `background: var(--color-bg-overlay);` or `var(--color-bg-elevated)`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:85`

**Found:** `background: rgba(0, 0, 0, 0.3);`
**Expected:** `background: var(--color-bg-elevated);`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:162`

**Found:** `background: rgba(239, 68, 68, 0.2);`
**Expected:** Use design token for danger/critical background
**Severity:** P1
**Fix:** Create token like `var(--color-bg-danger)` or use existing pattern

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:164`

**Found:** `border: 1px solid rgba(239, 68, 68, 0.4);`
**Expected:** Use design token for danger border
**Severity:** P1
**Fix:** Create token like `var(--color-border-danger)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:176`

**Found:** `background: rgba(245, 158, 11, 0.2);`
**Expected:** Use design token for warning background
**Severity:** P1
**Fix:** Create token like `var(--color-bg-warning)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:178`

**Found:** `border: 1px solid rgba(245, 158, 11, 0.4);`
**Expected:** Use design token for warning border
**Severity:** P1
**Fix:** Create token like `var(--color-border-warning)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:190`

**Found:** `background: rgba(59, 130, 246, 0.2);`
**Expected:** Use design token for info background
**Severity:** P1
**Fix:** Create token like `var(--color-bg-info)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:192`

**Found:** `border: 1px solid rgba(59, 130, 246, 0.4);`
**Expected:** Use design token for info border
**Severity:** P1
**Fix:** Create token like `var(--color-border-info)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:204`

**Found:** `background: rgba(16, 185, 129, 0.2);`
**Expected:** Use design token for success background
**Severity:** P1
**Fix:** Create token like `var(--color-bg-success)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:206`

**Found:** `border: 1px solid rgba(16, 185, 129, 0.4);`
**Expected:** Use design token for success border
**Severity:** P1
**Fix:** Create token like `var(--color-border-success)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:218`

**Found:** `background: rgba(100, 116, 139, 0.2);`
**Expected:** Use design token for neutral/info background
**Severity:** P1
**Fix:** Create appropriate design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:220`

**Found:** `border: 1px solid rgba(100, 116, 139, 0.4);`
**Expected:** Use design token for neutral border
**Severity:** P1
**Fix:** Create appropriate design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:229`

**Found:** `background: rgba(0, 0, 0, 0.5);`
**Expected:** `background: var(--color-bg-overlay);` or `var(--color-bg-elevated)`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveHeader.module.css:7`

**Found:** `background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(0, 0, 0, 0.4) 100%);`
**Expected:** Use design token gradient
**Severity:** P0
**Fix:** Replace with `var(--gradient-primary)` or create appropriate token

---

### 2. Hardcoded Spacing (11 violations)

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:56`

**Found:** `width: 6px;`
**Expected:** Use design token spacing
**Severity:** P2
**Fix:** Replace with `var(--space-1.5)` or appropriate token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:65`

**Found:** `border-radius: 3px;`
**Expected:** Use design token border radius
**Severity:** P2
**Fix:** Replace with `var(--radius-sm)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:74`

**Found:** `padding: 2rem 1rem;`
**Expected:** Use design token spacing like `var(--space-8) var(--space-4)`
**Severity:** P1
**Fix:** Replace with appropriate spacing tokens

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:76`

**Found:** `font-size: 0.875rem;`
**Expected:** `font-size: var(--text-sm);`
**Severity:** P1
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:106`

**Found:** `margin-bottom: 0.5rem;`
**Expected:** `margin-bottom: var(--space-2);`
**Severity:** P1
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:117`

**Found:** `font-size: 0.65rem;`
**Expected:** Use `var(--text-xs)` (0.75rem) or create smaller token
**Severity:** P2
**Fix:** Use existing token or define new one

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:120`

**Found:** `padding: 0.15rem 0.4rem;`
**Expected:** Use design token spacing
**Severity:** P2
**Fix:** Replace with appropriate spacing tokens

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:135`

**Found:** `font-size: 0.7rem;`
**Expected:** Use `var(--text-xs)` or define token
**Severity:** P2
**Fix:** Use existing token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:141`

**Found:** `font-size: 0.65rem;`
**Expected:** Use design token
**Severity:** P2
**Fix:** Use existing token or define new one

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:234`

**Found:** `font-size: 0.7rem;`
**Expected:** Use `var(--text-xs)` or appropriate token
**Severity:** P2
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:300`

**Found:** `padding: 0.5rem;`
**Expected:** `padding: var(--space-2);`
**Severity:** P1
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:304`

**Found:** `font-size: 1rem;`
**Expected:** `font-size: var(--text-base);`
**Severity:** P1
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveHeader.module.css:125`

**Found:** `height: 4px;`
**Expected:** Use design token spacing
**Severity:** P2
**Fix:** Replace with `var(--space-1)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveHeader.module.css:134`

**Found:** `border-radius: 2px;`
**Expected:** Use design token border radius
**Severity:** P2
**Fix:** Replace with `var(--radius-sm)`

---

### 3. Wrong Fonts (2 violations)

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveHeader.module.css:113`

**Found:** `font-family: 'Orbitron', system-ui, sans-serif;`
**Expected:** `font-family: 'Orbitron', monospace;` (per design system)
**Severity:** P0
**Fix:** Replace fallback with monospace instead of system-ui, sans-serif

**Note:** Design system specifies 'Orbitron' should fall back to monospace, not system fonts

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveHeader.module.css:66`

**Found:** Uses 'Courier New' correctly but in h1 element
**Expected:** 'Orbitron' for titles/headings per design system
**Severity:** P0
**Fix:** Title h1 should use `font-family: 'Orbitron', monospace;`

---

### 4. Inline Styles (1 violation)

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/ModuleContainer.jsx:10-12`

**Found:**

```jsx
<div style={{
  height: '100%',
  animation: 'fade-in 0.3s ease-out'
}}>
```

**Expected:** Move styles to CSS module
**Severity:** P0
**Fix:** Create ModuleContainer.module.css with proper styling using design tokens

---

### 5. Wrong Hover Effects (6 violations)

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:98`

**Found:** `transform: translateX(-3px);`
**Expected:** Not a card or button, but alert item should follow design patterns
**Severity:** P1
**Fix:** Consider if this is appropriate for list items or align with design system

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveHeader.module.css:44`

**Found:** `transform: translateX(-5px);` (back button)
**Expected:** Buttons should use `translateX(5px)` (forward movement)
**Severity:** P0
**Fix:** Change to `transform: translateX(5px);` to match design system button hover

**Note:** Design system specifies button hover should be `translateX(5px)` not `-5px`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveHeader.module.css:96`

**Found:** `transform: translateY(-5px);` (metric cards)
**Expected:** Cards should use `translateY(-10px) scale(1.02)`
**Severity:** P0
**Fix:** Change to `transform: translateY(-10px) scale(1.02);`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/DefensiveDashboard.module.css:59`

**Found:** `padding: var(--spacing-lg, 1.5rem);`
**Expected:** Remove hardcoded fallback value
**Severity:** P1
**Fix:** Use `padding: var(--space-6);` without fallback

---

### 6. Missing Design Tokens Reference (3 violations)

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/components/DefensiveSidebar.module.css:154-221`

**Found:** Severity colors use fallbacks but some colors not in design system
**Expected:** All severity colors should be defined in design tokens
**Severity:** P1
**Fix:** Define `--severity-critical`, `--severity-high`, `--severity-medium`, `--severity-low`, `--severity-info` in design system

**Colors used:**

- Critical: `#ef4444` (matches `--color-accent-danger`)
- High: `#f59e0b` (matches `--color-accent-warning`)
- Medium: `#3b82f6` (matches `--color-accent-info`)
- Low: `#10b981` (matches `--color-accent-success`)
- Info: `#64748b` (NOT in design system - needs to be added)

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/DefensiveDashboard.module.css:18`

**Found:** `background: var(--dashboard-bg);`
**Expected:** Verify `--dashboard-bg` is defined in design system
**Severity:** P2
**Fix:** Ensure this token exists or use `var(--color-bg-primary)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/DefensiveDashboard/DefensiveDashboard.module.css:59`

**Found:** `padding: var(--spacing-lg, 1.5rem);`
**Expected:** Design system uses `--space-*` not `--spacing-*`
**Severity:** P1
**Fix:** Change to `var(--space-6)` (which equals 1.5rem)

---

## Fix Priority

### P0 - Critical Fixes (Breaking consistency) - 18 violations

1. **DefensiveSidebar.module.css:16** - Hardcoded gradient background
2. **DefensiveSidebar.module.css:26** - Hardcoded rgba(0,0,0,0.5) background
3. **DefensiveSidebar.module.css:85** - Hardcoded rgba(0,0,0,0.3) background
4. **DefensiveSidebar.module.css:229** - Hardcoded rgba(0,0,0,0.5) background
5. **DefensiveHeader.module.css:7** - Hardcoded gradient background
6. **DefensiveHeader.module.css:113** - Wrong font fallback (system-ui instead of monospace)
7. **DefensiveHeader.module.css:66** - Wrong font family for h1 (should be Orbitron)
8. **ModuleContainer.jsx:10-12** - Inline styles instead of CSS module
9. **DefensiveHeader.module.css:44** - Wrong button hover direction (should be +5px not -5px)
10. **DefensiveHeader.module.css:96** - Wrong card hover transform (missing scale)

### P1 - High Priority (Noticeable) - 10 violations

1. **DefensiveDashboard.module.css:72** - Hardcoded shadow with wrong opacity
2. **DefensiveSidebar.module.css:162-220** - Multiple hardcoded severity colors (8 occurrences)
3. **DefensiveSidebar.module.css:74** - Hardcoded padding values
4. **DefensiveSidebar.module.css:76** - Hardcoded font-size
5. **DefensiveSidebar.module.css:106** - Hardcoded margin
6. **DefensiveSidebar.module.css:300** - Hardcoded padding
7. **DefensiveSidebar.module.css:304** - Hardcoded font-size
8. **DefensiveSidebar.module.css:98** - Non-standard hover effect
9. **DefensiveDashboard.module.css:59** - Wrong token name (--spacing-lg)
10. **DefensiveSidebar.module.css:154-221** - Missing severity color tokens

### P2 - Minor Fixes - 7 violations

1. **DefensiveSidebar.module.css:56** - Hardcoded scrollbar width
2. **DefensiveSidebar.module.css:65** - Hardcoded border-radius
3. **DefensiveSidebar.module.css:117** - Hardcoded font-size (0.65rem)
4. **DefensiveSidebar.module.css:120** - Hardcoded padding
5. **DefensiveSidebar.module.css:135** - Hardcoded font-size (0.7rem)
6. **DefensiveSidebar.module.css:141** - Hardcoded font-size (0.65rem)
7. **DefensiveSidebar.module.css:234** - Hardcoded font-size (0.7rem)
8. **DefensiveHeader.module.css:125** - Hardcoded scrollbar height
9. **DefensiveHeader.module.css:134** - Hardcoded border-radius
10. **DefensiveDashboard.module.css:18** - Unverified token (--dashboard-bg)

---

## Recommended Actions

### Immediate (P0)

1. **Create ModuleContainer.module.css** to eliminate inline styles
2. **Replace all hardcoded rgba(0,0,0,...) backgrounds** with design tokens
3. **Fix font fallbacks** to use monospace instead of system fonts
4. **Correct hover effects** for buttons (translateX(5px)) and cards (translateY(-10px) scale(1.02))

### Short-term (P1)

1. **Add severity color tokens** to design system:
   - `--color-severity-critical: #ef4444`
   - `--color-severity-high: #f59e0b`
   - `--color-severity-medium: #3b82f6`
   - `--color-severity-low: #10b981`
   - `--color-severity-info: #64748b`
2. **Replace all hardcoded spacing** with design tokens
3. **Standardize token naming** (--space-_ not --spacing-_)

### Long-term (P2)

1. **Create scrollbar styling tokens** for reusability
2. **Standardize smaller font sizes** (add tokens for 0.65rem and 0.7rem if needed)
3. **Document custom animations** in design system

---

## Design System Gaps Identified

The following additions should be made to the design system:

1. **Severity Colors** - Add severity-specific color tokens
2. **Background Overlays** - Standardize overlay backgrounds (currently hardcoded)
3. **Scrollbar Styles** - Define standard scrollbar styling tokens
4. **Micro Font Sizes** - Define tokens for sizes below 0.75rem if needed
5. **Alert/List Item Hover** - Define hover pattern for list items (different from cards/buttons)

---

**End of Report**
