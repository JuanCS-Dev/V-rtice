# Component Standards - Vértice Frontend

## Button Components Strategy

### Current State
We have **three** button implementations:

1. **`components/ui/button.tsx`** (Shadcn/UI - RECOMMENDED)
2. **`components/shared/AccessibleButton.jsx`** (Legacy Accessible)
3. **`components/shared/Button/Button.jsx`** (Legacy CSS Modules)

---

## RECOMMENDED: Use Shadcn/UI Button

**File:** `/src/components/ui/button.tsx`

### When to use:
- **ALL new components** should use this
- Building UI with Radix UI primitives
- Need TypeScript support
- Want consistent design system
- Require composition via `asChild` prop

### Features:
- TypeScript with proper types
- Radix UI Slot for composition
- CVA (Class Variance Authority) for variants
- Built-in focus management
- Variants: default, destructive, outline, secondary, ghost, link
- Sizes: sm, md, lg, icon

### Example:
```tsx
import { Button } from '@/components/ui/button';

<Button variant="destructive" size="lg">Delete</Button>
<Button variant="ghost" size="icon" aria-label="Close">
  <XIcon />
</Button>
```

---

## LEGACY: AccessibleButton (Deprecated - Migration Recommended)

**File:** `/src/components/shared/AccessibleButton.jsx`

### Current Status: **DEPRECATED**
- Still functional but not actively developed
- Migrate to Shadcn/UI Button when refactoring
- OK to keep in existing code (don't rush migration)

### When it was used:
- Accessibility-first implementation before Shadcn/UI
- Components built during Phase 4C
- Custom ARIA needs

### Migration Path:
```jsx
// OLD
import { Button } from '@/components/shared/AccessibleButton';
<Button variant="danger" ariaLabel="Delete user">Delete</Button>

// NEW
import { Button } from '@/components/ui/button';
<Button variant="destructive" aria-label="Delete user">Delete</Button>
```

---

## LEGACY: Button (Deprecated - Migration Recommended)

**File:** `/src/components/shared/Button/Button.jsx`

### Current Status: **DEPRECATED**
- Simple CSS modules implementation
- Missing proper accessibility features
- Migrate to Shadcn/UI Button when refactoring

### When it was used:
- Early components before standardization
- Components with loading states (though Shadcn supports this too)

### Migration Path:
```jsx
// OLD
import { Button } from '@/components/shared/Button';
<Button variant="primary" loading={isLoading}>Submit</Button>

// NEW
import { Button } from '@/components/ui/button';
<Button disabled={isLoading}>
  {isLoading ? 'Loading...' : 'Submit'}
</Button>
```

---

## Loading State Pattern

### Standardization: Use LoadingSpinner Component
```jsx
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';

<Button disabled={isLoading}>
  {isLoading ? (
    <>
      <LoadingSpinner size="sm" />
      <span>Loading...</span>
    </>
  ) : (
    'Submit'
  )}
</Button>
```

---

## Modal Components Strategy

### Current State
We have **two** modal implementations:

1. **`components/shared/Modal/Modal.jsx`** (RECOMMENDED)
2. Various inline modals scattered across components

### RECOMMENDED: Use Modal Component

**File:** `/src/components/shared/Modal/Modal.jsx`

```jsx
import { Modal } from '@/components/shared/Modal';

<Modal
  isOpen={isOpen}
  onClose={handleClose}
  title="Confirm Action"
>
  <p>Are you sure?</p>
</Modal>
```

### Features:
- Proper focus management
- Escape key to close
- Click outside to close
- Accessible (ARIA roles)
- Consistent styling

---

## CSS Strategy

### Standard: Tailwind for Utilities, CSS Modules for Components

#### Use Tailwind when:
- Applying utility styles (spacing, colors, layout)
- Rapid prototyping
- One-off styling needs
- Responsive design

```jsx
<div className="flex items-center gap-4 p-4 bg-gray-900 rounded-lg">
  <span className="text-green-400">Status</span>
</div>
```

#### Use CSS Modules when:
- Complex component-specific styles
- Need scoped styles to avoid conflicts
- Animations and transitions
- Theme-specific overrides

```jsx
// Component.module.css
.container {
  background: var(--bg-primary);
  transition: all var(--duration-base);
}

.container:hover {
  box-shadow: 0 0 20px var(--glow-color);
}

// Component.jsx
import styles from './Component.module.css';
<div className={styles.container}>...</div>
```

#### Combining Both (Preferred):
```jsx
import styles from './Card.module.css';

<div className={`${styles.card} p-4 rounded-lg`}>
  <h3 className={`${styles.title} text-xl font-bold`}>Title</h3>
</div>
```

---

## Alert/Error Display Standard

### RECOMMENDED: Use Alert Component

**File:** `/src/components/shared/Alert/Alert.jsx`

```jsx
import { Alert } from '@/components/shared/Alert';

<Alert variant="error" icon={<WarningIcon />}>
  Operation failed. Please try again.
</Alert>

<Alert variant="success">
  Data saved successfully!
</Alert>

<Alert variant="warning">
  This action cannot be undone.
</Alert>
```

### Accessibility Requirements:
- ALL error alerts MUST have `role="alert"` and `aria-live="assertive"`
- ALL success messages MUST have `role="status"` and `aria-live="polite"`
- Link errors to inputs using `aria-describedby`

---

## Design Token System

### CSS Variables for Semantic Colors

**File:** `/src/styles/tokens.css` or similar

```css
:root {
  /* Semantic Colors */
  --color-primary: #00ff88;
  --color-secondary: #ff0044;
  --color-success: #00ff00;
  --color-error: #ff0000;
  --color-warning: #ffaa00;
  --color-info: #00aaff;

  /* Backgrounds */
  --bg-primary: #0a0a0a;
  --bg-secondary: rgba(255, 255, 255, 0.05);
  --bg-tertiary: rgba(255, 255, 255, 0.1);

  /* Text */
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.7);
  --text-tertiary: rgba(255, 255, 255, 0.5);

  /* Borders */
  --border-primary: rgba(255, 255, 255, 0.2);
  --border-secondary: rgba(255, 255, 255, 0.1);

  /* Transitions */
  --duration-fast: 150ms;
  --duration-base: 200ms;
  --duration-slow: 300ms;

  /* Focus Ring */
  --focus-ring: 0 0 0 3px rgba(0, 255, 136, 0.5);
}
```

### Usage:
```css
.button {
  background: var(--color-primary);
  color: var(--text-primary);
  transition: all var(--duration-base);
}

.button:focus {
  box-shadow: var(--focus-ring);
}
```

---

## Migration Timeline

### Phase 1 (Current)
- Document all standards (this file)
- Stop using deprecated components in NEW code
- All new features use Shadcn/UI buttons

### Phase 2 (Next Sprint)
- Create EmptyState component
- Standardize all loading patterns
- Add CSS variables system

### Phase 3 (Future)
- Gradually migrate legacy buttons during refactors
- Don't do mass migration - migrate when touching files
- Update when fixing bugs or adding features

---

## Questions?

- Shadcn/UI Button: `/src/components/ui/button.tsx`
- Legacy components marked as DEPRECATED in this doc
- Always prefer documented RECOMMENDED components
- When in doubt, follow Boris Cherny Standard (type safety + accessibility)
