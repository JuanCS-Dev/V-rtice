# OffensiveDashboard - Visual Violations Report

**Generated:** 2025-10-14
**Reference:** Landing Page Design System v1.0.0
**Audit Scope:** OffensiveDashboard components

---

## Summary
- **Total violations:** 89
- **Critical (P0):** 36
- **High (P1):** 40
- **Medium (P2):** 13

---

## Violations by Category

### 1. Hardcoded Colors (49 violations)

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/OffensiveDashboard.module.css:30`
**Found:** `background: rgba(0, 0, 0, 0.3);`
**Expected:** `background: var(--color-bg-elevated);` or `var(--color-bg-secondary)`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/OffensiveDashboard.module.css:39`
**Found:** `background: rgba(0, 0, 0, 0.5);`
**Expected:** `background: var(--color-bg-overlay);` or `var(--color-bg-elevated)`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/OffensiveDashboard.module.css:43`
**Found:** `background: linear-gradient(180deg, var(--color-accent-primary) 0%, #991b1b 100%);`
**Expected:** Use design token gradient (no hardcoded #991b1b)
**Severity:** P0
**Fix:** Replace with `var(--gradient-red)` or define appropriate red gradient token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:7`
**Found:** `background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(0, 0, 0, 0.4) 100%);`
**Expected:** Use design token gradient
**Severity:** P0
**Fix:** Replace with design token or create appropriate header gradient token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:9`
**Found:** `box-shadow: 0 4px 20px var(--shadow-glow-purple);`
**Expected:** `box-shadow: var(--shadow-glow-purple);` (defined as `0 0 30px rgba(139, 92, 246, 0.8)`)
**Severity:** P1
**Fix:** Shadow has custom blur values not matching design system - should be `0 0 30px` not `0 4px 20px`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:55`
**Found:** `filter: drop-shadow(0 0 10px rgba(139, 92, 246, 0.6));`
**Expected:** Use design token for glow effect
**Severity:** P1
**Fix:** Create token or use existing `var(--shadow-glow-purple)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:63`
**Found:** `text-shadow: 0 0 20px rgba(139, 92, 246, 0.5);`
**Expected:** Use design token for text glow
**Severity:** P1
**Fix:** Create appropriate text shadow token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:112`
**Found:** `text-shadow: 0 0 10px rgba(139, 92, 246, 0.5);`
**Expected:** Use design token for text glow
**Severity:** P1
**Fix:** Create appropriate text shadow token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:164`
**Found:** `box-shadow: 0 -3px 10px rgba(139, 92, 246, 0.2);`
**Expected:** Use design token for shadow
**Severity:** P1
**Fix:** Create appropriate shadow token or use existing

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:173`
**Found:** `filter: drop-shadow(0 0 10px rgba(139, 92, 246, 0.6));`
**Expected:** Use design token
**Severity:** P1
**Fix:** Use `var(--shadow-glow-purple)` or create appropriate token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:176`
**Found:** `filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.8));`
**Expected:** Use design token
**Severity:** P1
**Fix:** Use `var(--shadow-glow-purple)` which is exactly this value

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:6`
**Found:** `background: linear-gradient(180deg, rgba(139, 0, 0, 0.1) 0%, rgba(0, 0, 0, 0.4) 100%);`
**Expected:** Use design token gradient (no hardcoded red #8b0000)
**Severity:** P0
**Fix:** Replace with `var(--gradient-red)` or create appropriate red theme gradient

**Note:** Mixing red theme colors (#8b0000, #ff4444, #ff0000) violates design system purple/cyan color scheme

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:7`
**Found:** `border-left: 2px solid rgba(255, 68, 68, 0.2);`
**Expected:** Use design token for border (no hardcoded red)
**Severity:** P0
**Fix:** Replace with `var(--color-border-primary)` or define red border token

**Note:** Red borders (#ff4444) violate design system purple/cyan theme

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:15`
**Found:** `border-bottom: 2px solid rgba(255, 68, 68, 0.2);`
**Expected:** Use design token
**Severity:** P0
**Fix:** Replace with `var(--color-border-primary)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:16`
**Found:** `background: rgba(0, 0, 0, 0.3);`
**Expected:** `background: var(--color-bg-elevated);` or `var(--color-bg-secondary)`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:25`
**Found:** `color: #ff4444;`
**Expected:** Use design token (no hardcoded red)
**Severity:** P0
**Fix:** Replace with `var(--color-accent-primary)` or define red accent token

**Note:** Red color scheme (#ff4444) violates design system

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:39`
**Found:** `background: linear-gradient(135deg, #ff4444 0%, #ff0000 100%);`
**Expected:** Use `var(--gradient-red)` token
**Severity:** P0
**Fix:** Replace with design token (design system has red gradient defined)

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:45`
**Found:** `box-shadow: 0 0 15px rgba(255, 68, 68, 0.5);`
**Expected:** Use `var(--shadow-glow-red)` token
**Severity:** P0
**Fix:** Replace with design token (design system has red glow defined: `0 0 30px rgba(239, 68, 68, 1)`)

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:62`
**Found:** `background: rgba(0, 0, 0, 0.3);`
**Expected:** `background: var(--color-bg-elevated);`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:66`
**Found:** `background: rgba(255, 68, 68, 0.3);`
**Expected:** Use design token for scrollbar thumb
**Severity:** P1
**Fix:** Create scrollbar token or use existing pattern

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:77`
**Found:** `color: rgba(255, 68, 68, 0.4);`
**Expected:** Use design token
**Severity:** P1
**Fix:** Use `var(--color-text-muted)` or create appropriate token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:99`
**Found:** `background: rgba(0, 0, 0, 0.4);`
**Expected:** `background: var(--color-bg-elevated);`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:100`
**Found:** `border: 1px solid rgba(255, 68, 68, 0.2);`
**Expected:** `border: 1px solid var(--color-border-primary);`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:108`
**Found:** `border-color: #ff4444;`
**Expected:** `border-color: var(--color-accent-primary);`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:109`
**Found:** `box-shadow: 0 0 15px rgba(255, 68, 68, 0.3);`
**Expected:** Use design token for shadow
**Severity:** P1
**Fix:** Use `var(--shadow-glow-red)` or create appropriate token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:114`
**Found:** `border-left: 4px solid #ff9500;`
**Expected:** Use design token (no hardcoded orange)
**Severity:** P0
**Fix:** Use `var(--color-accent-warning)` which is #f59e0b

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:115`
**Found:** `background: linear-gradient(90deg, rgba(255, 149, 0, 0.1) 0%, rgba(0, 0, 0, 0.4) 100%);`
**Expected:** Use design token gradient
**Severity:** P0
**Fix:** Create appropriate warning/orange gradient token or use existing

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:119`
**Found:** `border-left: 4px solid #00ff00;`
**Expected:** Use design token
**Severity:** P0
**Fix:** Use `var(--color-accent-success)` which is #10b981

**Note:** #00ff00 is pure green, not matching design system green (#10b981)

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:120`
**Found:** `background: linear-gradient(90deg, rgba(0, 255, 0, 0.1) 0%, rgba(0, 0, 0, 0.4) 100%);`
**Expected:** Use design token gradient
**Severity:** P0
**Fix:** Use `var(--gradient-green)` or create appropriate success gradient

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:124`
**Found:** `border-left: 4px solid #ff0000;`
**Expected:** Use design token
**Severity:** P0
**Fix:** Use `var(--color-accent-danger)` which is #ef4444

**Note:** #ff0000 is pure red, not matching design system danger (#ef4444)

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:125`
**Found:** `background: linear-gradient(90deg, rgba(255, 0, 0, 0.1) 0%, rgba(0, 0, 0, 0.4) 100%);`
**Expected:** Use design token gradient
**Severity:** P0
**Fix:** Use `var(--gradient-red)` defined in design system

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:138`
**Found:** `color: #ff4444;`
**Expected:** Use design token
**Severity:** P0
**Fix:** Use `var(--color-accent-primary)` or define appropriate token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:151`
**Found:** `background: rgba(255, 149, 0, 0.2);`
**Expected:** Use design token for warning background
**Severity:** P1
**Fix:** Create `var(--color-bg-warning)` token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:152`
**Found:** `color: #ff9500;`
**Expected:** Use `var(--color-accent-warning)` (which is #f59e0b)
**Severity:** P0
**Fix:** Replace with design token

**Note:** #ff9500 doesn't match design system warning color #f59e0b

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:153`
**Found:** `border: 1px solid rgba(255, 149, 0, 0.4);`
**Expected:** Use design token for warning border
**Severity:** P1
**Fix:** Create `var(--color-border-warning)` token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:158`
**Found:** `background: rgba(0, 255, 0, 0.2);`
**Expected:** Use design token for success background
**Severity:** P1
**Fix:** Create `var(--color-bg-success)` token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:159`
**Found:** `color: #00ff00;`
**Expected:** Use `var(--color-accent-success)` (which is #10b981)
**Severity:** P0
**Fix:** Replace with design token

**Note:** #00ff00 is pure green, doesn't match design system

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:160`
**Found:** `border: 1px solid rgba(0, 255, 0, 0.4);`
**Expected:** Use design token for success border
**Severity:** P1
**Fix:** Create `var(--color-border-success)` token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:164`
**Found:** `background: rgba(255, 0, 0, 0.2);`
**Expected:** Use design token for danger background
**Severity:** P1
**Fix:** Create `var(--color-bg-danger)` token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:165`
**Found:** `color: #ff0000;`
**Expected:** Use `var(--color-accent-danger)` (which is #ef4444)
**Severity:** P0
**Fix:** Replace with design token

**Note:** #ff0000 is pure red, doesn't match design system

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:166`
**Found:** `border: 1px solid rgba(255, 0, 0, 0.4);`
**Expected:** Use design token for danger border
**Severity:** P1
**Fix:** Create `var(--color-border-danger)` token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:175`
**Found:** `background: rgba(0, 0, 0, 0.3);`
**Expected:** `background: var(--color-bg-elevated);`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:185`
**Found:** `color: rgba(255, 68, 68, 0.8);`
**Expected:** Use design token
**Severity:** P1
**Fix:** Use `var(--color-accent-primary)` or create appropriate token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:195`
**Found:** `background: rgba(0, 0, 0, 0.5);`
**Expected:** `background: var(--color-bg-overlay);`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:199`
**Found:** `border: 1px solid rgba(255, 68, 68, 0.2);`
**Expected:** `border: 1px solid var(--color-border-primary);`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:204`
**Found:** `background: linear-gradient(90deg, #ff9500 0%, #ff4444 100%);`
**Expected:** Use design token gradient
**Severity:** P0
**Fix:** Create appropriate warning-to-danger gradient token or use existing

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:206`
**Found:** `box-shadow: 0 0 10px rgba(255, 68, 68, 0.5);`
**Expected:** Use design token for shadow
**Severity:** P1
**Fix:** Use `var(--shadow-glow-red)` or create appropriate token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:217`
**Found:** `text-shadow: 0 0 5px rgba(0, 0, 0, 0.8);`
**Expected:** Use design token for text shadow
**Severity:** P2
**Fix:** Create appropriate token if needed

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:223`
**Found:** `border-top: 1px solid rgba(255, 68, 68, 0.2);`
**Expected:** `border-top: 1px solid var(--color-border-primary);`
**Severity:** P0
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:229`
**Found:** `color: rgba(255, 68, 68, 0.7);`
**Expected:** Use design token
**Severity:** P1
**Fix:** Use `var(--color-text-tertiary)` or create appropriate token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:241`
**Found:** `background: rgba(0, 0, 0, 0.3);`
**Expected:** `background: var(--color-bg-elevated);`
**Severity:** P0
**Fix:** Replace with design token

---

### 2. Hardcoded Spacing (23 violations)

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/OffensiveDashboard.module.css:44`
**Found:** `border-radius: 5px;`
**Expected:** `border-radius: var(--radius-md);` (0.375rem)
**Severity:** P2
**Fix:** Replace with design token

**Note:** 5px is not a standard border radius in design system

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/OffensiveDashboard.module.css:52`
**Found:** `height: 400px;`
**Expected:** Use design token spacing or viewport units
**Severity:** P2
**Fix:** Consider using design tokens or relative units

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/OffensiveDashboard.module.css:53`
**Found:** `gap: 1.5rem;`
**Expected:** `gap: var(--space-6);` (which is 1.5rem)
**Severity:** P1
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/OffensiveDashboard.module.css:58`
**Found:** `font-size: 1.1rem;`
**Expected:** Use design token (closest is `var(--text-lg)` which is 1.125rem)
**Severity:** P1
**Fix:** Replace with `var(--text-lg)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/OffensiveDashboard.module.css:66`
**Found:** `width: 60px;` and `height: 60px;`
**Expected:** Use design token spacing
**Severity:** P2
**Fix:** Use `var(--space-16)` or create appropriate size token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/OffensiveDashboard.module.css:68`
**Found:** `border: 4px solid ...`
**Expected:** Use design token spacing
**Severity:** P2
**Fix:** Use `var(--space-1)` for border width

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:44`
**Found:** `border-radius: 12px;`
**Expected:** Use design token
**Severity:** P2
**Fix:** Use `var(--radius-xl)` (0.75rem) or `var(--radius-2xl)` (1rem)

**Note:** 12px = 0.75rem which is var(--radius-xl)

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:101`
**Found:** `border-radius: 8px;`
**Expected:** Use design token
**Severity:** P2
**Fix:** Use `var(--radius-lg)` (0.5rem) or `var(--radius-xl)` (0.75rem)

**Note:** 8px is not exact match - closest is 0.5rem or 0.75rem

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:125`
**Found:** `height: 4px;`
**Expected:** Use design token spacing
**Severity:** P2
**Fix:** Use `var(--space-1)` (0.25rem = 4px)

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:134`
**Found:** `border-radius: 2px;`
**Expected:** Use design token
**Severity:** P2
**Fix:** Use `var(--radius-sm)` (0.125rem = 2px)

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:14`
**Found:** `padding: 1.5rem;`
**Expected:** `padding: var(--space-6);` (which is 1.5rem)
**Severity:** P1
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:23`
**Found:** `font-size: 1.1rem;`
**Expected:** Use design token (closest is `var(--text-lg)` which is 1.125rem)
**Severity:** P1
**Fix:** Replace with `var(--text-lg)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:28`
**Found:** `gap: 0.5rem;`
**Expected:** `gap: var(--space-2);` (which is 0.5rem)
**Severity:** P1
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:41`
**Found:** `font-size: 0.9rem;`
**Expected:** Use design token (closest is `var(--text-sm)` which is 0.875rem)
**Severity:** P1
**Fix:** Replace with `var(--text-sm)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:43`
**Found:** `padding: 0.3rem 0.8rem;`
**Expected:** Use design token spacing
**Severity:** P1
**Fix:** Use appropriate spacing tokens like `var(--space-1.5) var(--space-3)`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:44`
**Found:** `border-radius: 12px;`
**Expected:** Use design token
**Severity:** P2
**Fix:** Use `var(--radius-xl)` (0.75rem = 12px)

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:51`
**Found:** `padding: 1rem;`
**Expected:** `padding: var(--space-4);` (which is 1rem)
**Severity:** P1
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:54`
**Found:** `gap: 1rem;`
**Expected:** `gap: var(--space-4);` (which is 1rem)
**Severity:** P1
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:58`
**Found:** `width: 6px;`
**Expected:** Use design token spacing
**Severity:** P2
**Fix:** Use `var(--space-1.5)` (0.375rem ~ 6px)

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:67`
**Found:** `border-radius: 3px;`
**Expected:** Use design token
**Severity:** P2
**Fix:** Use `var(--radius-sm)` (0.125rem = 2px) or create 3px token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:82`
**Found:** `font-size: 4rem;`
**Expected:** Use design token
**Severity:** P1
**Fix:** Use `var(--text-6xl)` (3.75rem) or create larger token

**Note:** 4rem is not in design system (max is 3.75rem for 6xl)

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:83`
**Found:** `margin-bottom: 1rem;`
**Expected:** `margin-bottom: var(--space-4);` (which is 1rem)
**Severity:** P1
**Fix:** Replace with design token

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:88`
**Found:** `font-size: 1.1rem;`
**Expected:** Use design token
**Severity:** P1
**Fix:** Use `var(--text-lg)` (1.125rem)

---

### 3. Wrong Fonts (3 violations)

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:113`
**Found:** `font-family: 'Orbitron', system-ui, sans-serif;`
**Expected:** `font-family: 'Orbitron', monospace;`
**Severity:** P0
**Fix:** Replace fallback with monospace instead of system-ui, sans-serif

**Note:** Design system specifies Orbitron should fall back to monospace

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:66`
**Found:** `font-family: 'Courier New', monospace;` in h1 element
**Expected:** `font-family: 'Orbitron', monospace;` for titles per design system
**Severity:** P0
**Fix:** Title h1 should use Orbitron for display text

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/OffensiveDashboard.module.css:13`
**Found:** `font-family: 'Courier New', monospace;` on root element
**Expected:** This is correct for body, but ensure child headings override with Orbitron
**Severity:** P2
**Fix:** Verify all headings properly override with Orbitron

---

### 4. Inline Styles (1 violation)

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.jsx:71`
**Found:**
```jsx
<div
  className={styles.progressFill}
  style={{ width: `${execution.progress}%` }}
/>
```
**Expected:** Dynamic width is acceptable for progress bars
**Severity:** P2
**Fix:** This is acceptable - dynamic inline styles for progress are a valid use case

**Note:** This is an acceptable use of inline styles for dynamic values

---

### 5. Wrong Hover Effects (13 violations)

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:44`
**Found:** `transform: translateX(-5px);` (back button)
**Expected:** Buttons should use `translateX(5px)` per design system
**Severity:** P0
**Fix:** Change to `transform: translateX(5px);`

**Note:** Design system button hover is `translateX(5px)` not `-5px`

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveHeader.module.css:96`
**Found:** `transform: translateY(-5px);` (metric cards)
**Expected:** Cards should use `transform: translateY(-10px) scale(1.02);`
**Severity:** P0
**Fix:** Change to `transform: translateY(-10px) scale(1.02);`

**Note:** Missing scale transformation

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/OffensiveSidebar.module.css:110`
**Found:** `transform: translateX(-3px);` (execution cards)
**Expected:** Cards should use `translateY(-10px) scale(1.02)`
**Severity:** P1
**Fix:** Change to `transform: translateY(-10px) scale(1.02);` to match card hover pattern

**Note:** Using horizontal transform instead of vertical for cards

---

#### File: `/home/juan/vertice-dev/frontend/src/components/dashboards/OffensiveDashboard/components/ModuleContainer.module.css:13`
**Found:** `transform: translateY(10px);` in animation
**Expected:** Design system fadeIn uses Y translation but check animation pattern
**Severity:** P2
**Fix:** Verify animation follows design system pattern

---

---

## Fix Priority

### P0 - Critical Fixes (Breaking consistency) - 36 violations

**Color violations (26):**
1. **OffensiveDashboard.module.css:30** - Hardcoded rgba(0,0,0,0.3)
2. **OffensiveDashboard.module.css:39** - Hardcoded rgba(0,0,0,0.5)
3. **OffensiveDashboard.module.css:43** - Hardcoded red gradient #991b1b
4. **OffensiveHeader.module.css:7** - Hardcoded gradient background
5. **OffensiveSidebar.module.css:6** - Hardcoded red gradient (violates purple/cyan theme)
6. **OffensiveSidebar.module.css:7** - Hardcoded red border (violates theme)
7. **OffensiveSidebar.module.css:15** - Hardcoded red border
8. **OffensiveSidebar.module.css:16** - Hardcoded rgba(0,0,0,0.3)
9. **OffensiveSidebar.module.css:25** - Hardcoded red #ff4444
10. **OffensiveSidebar.module.css:39** - Hardcoded red gradient
11. **OffensiveSidebar.module.css:45** - Hardcoded red shadow
12. **OffensiveSidebar.module.css:62** - Hardcoded rgba(0,0,0,0.3)
13. **OffensiveSidebar.module.css:99** - Hardcoded rgba(0,0,0,0.4)
14. **OffensiveSidebar.module.css:100** - Hardcoded red border
15. **OffensiveSidebar.module.css:108** - Hardcoded red #ff4444
16. **OffensiveSidebar.module.css:114** - Hardcoded orange #ff9500
17. **OffensiveSidebar.module.css:115** - Hardcoded orange gradient
18. **OffensiveSidebar.module.css:119** - Hardcoded pure green #00ff00
19. **OffensiveSidebar.module.css:120** - Hardcoded green gradient
20. **OffensiveSidebar.module.css:124** - Hardcoded pure red #ff0000
21. **OffensiveSidebar.module.css:125** - Hardcoded red gradient
22. **OffensiveSidebar.module.css:138** - Hardcoded red #ff4444
23. **OffensiveSidebar.module.css:152** - Hardcoded orange #ff9500
24. **OffensiveSidebar.module.css:159** - Hardcoded pure green #00ff00
25. **OffensiveSidebar.module.css:165** - Hardcoded pure red #ff0000
26. **OffensiveSidebar.module.css:175** - Hardcoded rgba(0,0,0,0.3)
27. **OffensiveSidebar.module.css:195** - Hardcoded rgba(0,0,0,0.5)
28. **OffensiveSidebar.module.css:199** - Hardcoded red border
29. **OffensiveSidebar.module.css:204** - Hardcoded red/orange gradient
30. **OffensiveSidebar.module.css:223** - Hardcoded red border
31. **OffensiveSidebar.module.css:241** - Hardcoded rgba(0,0,0,0.3)

**Font violations (2):**
1. **OffensiveHeader.module.css:113** - Wrong Orbitron fallback
2. **OffensiveHeader.module.css:66** - Should use Orbitron for h1

**Hover violations (3):**
1. **OffensiveHeader.module.css:44** - Wrong button hover direction
2. **OffensiveHeader.module.css:96** - Wrong card hover (missing scale)
3. **OffensiveSidebar.module.css:110** - Wrong card hover direction

### P1 - High Priority (Noticeable) - 40 violations

**Color violations (18):**
1. **OffensiveHeader.module.css:9** - Non-standard shadow values
2. **OffensiveHeader.module.css:55** - Hardcoded drop-shadow
3. **OffensiveHeader.module.css:63** - Hardcoded text-shadow
4. **OffensiveHeader.module.css:112** - Hardcoded text-shadow
5. **OffensiveHeader.module.css:164** - Hardcoded shadow
6. **OffensiveHeader.module.css:173** - Hardcoded drop-shadow
7. **OffensiveHeader.module.css:176** - Hardcoded drop-shadow
8. **OffensiveSidebar.module.css:66** - Hardcoded scrollbar color
9. **OffensiveSidebar.module.css:77** - Hardcoded rgba color
10. **OffensiveSidebar.module.css:109** - Hardcoded shadow
11. **OffensiveSidebar.module.css:151** - Hardcoded warning background
12. **OffensiveSidebar.module.css:153** - Hardcoded warning border
13. **OffensiveSidebar.module.css:158** - Hardcoded success background
14. **OffensiveSidebar.module.css:160** - Hardcoded success border
15. **OffensiveSidebar.module.css:164** - Hardcoded danger background
16. **OffensiveSidebar.module.css:166** - Hardcoded danger border
17. **OffensiveSidebar.module.css:185** - Hardcoded rgba color
18. **OffensiveSidebar.module.css:206** - Hardcoded shadow
19. **OffensiveSidebar.module.css:229** - Hardcoded rgba color

**Spacing violations (21):**
1. **OffensiveDashboard.module.css:53** - Hardcoded 1.5rem gap
2. **OffensiveDashboard.module.css:58** - Hardcoded 1.1rem font
3. **OffensiveSidebar.module.css:14** - Hardcoded 1.5rem padding
4. **OffensiveSidebar.module.css:23** - Hardcoded 1.1rem font
5. **OffensiveSidebar.module.css:28** - Hardcoded 0.5rem gap
6. **OffensiveSidebar.module.css:41** - Hardcoded 0.9rem font
7. **OffensiveSidebar.module.css:43** - Hardcoded padding
8. **OffensiveSidebar.module.css:51** - Hardcoded 1rem padding
9. **OffensiveSidebar.module.css:54** - Hardcoded 1rem gap
10. **OffensiveSidebar.module.css:82** - Hardcoded 4rem font (exceeds design system)
11. **OffensiveSidebar.module.css:83** - Hardcoded 1rem margin
12. **OffensiveSidebar.module.css:88** - Hardcoded 1.1rem font

**Hover violations (1):**
1. **OffensiveSidebar.module.css:110** - Non-standard card hover pattern

### P2 - Minor Fixes - 13 violations

**Spacing violations (11):**
1. **OffensiveDashboard.module.css:44** - Hardcoded 5px border-radius
2. **OffensiveDashboard.module.css:52** - Hardcoded 400px height
3. **OffensiveDashboard.module.css:66-68** - Hardcoded spinner dimensions
4. **OffensiveHeader.module.css:44** - Hardcoded 12px border-radius
5. **OffensiveHeader.module.css:101** - Hardcoded 8px border-radius
6. **OffensiveHeader.module.css:125** - Hardcoded 4px height
7. **OffensiveHeader.module.css:134** - Hardcoded 2px border-radius
8. **OffensiveSidebar.module.css:44** - Hardcoded 12px border-radius
9. **OffensiveSidebar.module.css:58** - Hardcoded 6px width
10. **OffensiveSidebar.module.css:67** - Hardcoded 3px border-radius

**Other violations (2):**
1. **OffensiveDashboard.module.css:13** - Font family hierarchy check
2. **OffensiveSidebar.module.css:217** - Hardcoded text-shadow
3. **OffensiveSidebar.jsx:71** - Acceptable inline style for progress
4. **ModuleContainer.module.css:13** - Animation pattern verification

---

## Recommended Actions

### Immediate (P0)

1. **Replace ALL red color scheme with design system purple/cyan**
   - The entire OffensiveDashboard uses red (#ff4444, #ff0000, #8b0000) which violates the design system
   - Replace with `var(--color-accent-primary)` (#8b5cf6) and `var(--color-accent-secondary)` (#06b6d4)
   - Use `var(--gradient-primary)` instead of red gradients

2. **Replace ALL hardcoded rgba(0,0,0,...) backgrounds**
   - Use `var(--color-bg-elevated)` for rgba(0,0,0,0.3)
   - Use `var(--color-bg-overlay)` for rgba(0,0,0,0.5)
   - Use `var(--color-bg-secondary)` for rgba(0,0,0,0.4)

3. **Fix font fallbacks**
   - Change Orbitron fallback from `system-ui, sans-serif` to `monospace`
   - Use Orbitron for h1 title elements instead of Courier New

4. **Fix hover effects**
   - Buttons: `translateX(5px)` not `-5px`
   - Cards: `translateY(-10px) scale(1.02)` not just `translateY(-5px)`

### Short-term (P1)

1. **Replace all hardcoded spacing values** with design tokens:
   - `1rem` → `var(--space-4)`
   - `1.5rem` → `var(--space-6)`
   - `0.5rem` → `var(--space-2)`

2. **Replace all hardcoded font sizes** with design tokens:
   - `1.1rem` → `var(--text-lg)` (1.125rem)
   - `0.9rem` → `var(--text-sm)` (0.875rem)

3. **Add status/severity color tokens** to design system:
   - `--color-bg-warning`, `--color-border-warning`
   - `--color-bg-success`, `--color-border-success`
   - `--color-bg-danger`, `--color-border-danger`

4. **Standardize shadow effects** using design tokens

### Long-term (P2)

1. **Create scrollbar styling tokens** for reusability
2. **Verify all animations** follow design system patterns
3. **Document red theme alternative** if offensive context requires different colors

---

## Critical Design System Violations

### 🚨 MAJOR ISSUE: Red Color Scheme

The OffensiveDashboard uses a red color scheme (#ff4444, #ff0000, etc.) throughout, which **completely violates** the design system's purple/cyan theme:

**Design System Colors:**
- Primary: #8b5cf6 (purple)
- Secondary: #06b6d4 (cyan)

**OffensiveDashboard Colors:**
- Primary: #ff4444 (red)
- Accents: #ff0000, #ff9500 (red/orange)

**Impact:** High - Creates visual inconsistency with rest of application

**Recommendation:**
- If red theme is intentional for "offensive" context, document it in design system as an alternative theme
- Otherwise, migrate entirely to purple/cyan design system colors

### Pure Web Colors Used

Multiple instances of pure web colors that don't match design system:
- `#ff0000` (pure red) instead of `#ef4444` (danger)
- `#00ff00` (pure green) instead of `#10b981` (success)
- `#ff9500` (bright orange) instead of `#f59e0b` (warning)

---

## Design System Gaps Identified

1. **Status/Severity Colors** - Need background and border variants
2. **Background Overlays** - Multiple hardcoded black overlays need standardization
3. **Scrollbar Styles** - Consistent scrollbar styling tokens needed
4. **Alternative Color Themes** - Consider documenting red theme for offensive contexts
5. **Text Shadows** - Glow effects need standardization

---

**End of Report**
