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

---

## Form Input Standards
### Boris Cherny Standard - GAP #97 FIX

#### RECOMMENDED: Use AccessibleForm Components

**File:** `/src/components/shared/AccessibleForm.jsx`

##### Input Fields
```jsx
import { FormInput } from '@/components/shared/AccessibleForm';

<FormInput
  label="Email Address"
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  error={emailError}
  helperText="We'll never share your email"
  required
/>
```

##### Textarea Fields
```jsx
import { FormTextarea } from '@/components/shared/AccessibleForm';

<FormTextarea
  label="Comments"
  value={comments}
  onChange={(e) => setComments(e.target.value)}
  rows={4}
  maxLength={1000}
  helperText="Maximum 1000 characters"
/>
```

#### Input Validation Requirements
- ALL inputs MUST have associated `<label>` elements
- ALL required inputs MUST show `required` attribute
- ALL error states MUST use `aria-invalid` and `aria-describedby`
- ALL inputs MUST have appropriate `maxLength` (see validation.js)
  - Short text (usernames): 100 chars
  - Medium text (emails, descriptions): 500 chars
  - Long text (comments): 1000 chars
  - Very long text (JSON data): 5000 chars

#### Standard Input Patterns
```jsx
// Email input
<input
  type="email"
  maxLength={500}
  autoComplete="email"
  required
/>

// Username input
<input
  type="text"
  minLength={3}
  maxLength={100}
  autoComplete="username"
  required
/>

// Password input
<input
  type="password"
  minLength={8}
  maxLength={100}
  autoComplete="current-password"
  required
/>

// Textarea (comments, notes)
<textarea
  rows={4}
  maxLength={1000}
  placeholder="Add your comments here..."
/>

// Textarea (JSON data)
<textarea
  rows={6}
  maxLength={5000}
  placeholder='{"key": "value"}'
/>
```

---

## HTTP Client Pattern
### Boris Cherny Standard - GAP #104 FIX

#### RECOMMENDED: Use Axios via API Client

**File:** `/src/api/client.js`

All API calls should go through the centralized API client which uses Axios:

```javascript
import apiClient from '@/api/client';

// GET request
const response = await apiClient.get('/defensive/metrics');

// POST request
const response = await apiClient.post('/offensive/scan', {
  target: '192.168.1.1',
  ports: '80,443'
});

// PUT request
const response = await apiClient.put('/hitl/decision', {
  patchId: '123',
  decision: 'approved'
});
```

#### Why Axios over Fetch?
- **Automatic JSON parsing**: No need for `response.json()`
- **Request/Response interceptors**: Centralized auth, error handling
- **Timeout support**: Built-in request timeouts
- **Progress tracking**: Upload/download progress
- **XSRF protection**: Built-in CSRF token handling
- **Better error handling**: Rejects on HTTP errors automatically

#### DO NOT Use raw fetch() for API calls
```javascript
// ❌ WRONG - Don't use raw fetch
fetch('/api/data')
  .then(res => res.json())
  .then(data => console.log(data));

// ✅ CORRECT - Use API client
import apiClient from '@/api/client';
const { data } = await apiClient.get('/data');
```

#### Exception: fetch() is OK for non-API calls
```javascript
// OK: Loading static resources
fetch('/config.json')

// OK: External third-party APIs (not our backend)
fetch('https://external-api.com/data')
```

---

## Toast Notification Pattern
### Boris Cherny Standard - GAP #105 FIX

#### Current State: Using Alert Component (No Toast Library)

We use the **Alert component** for notifications instead of a separate toast library:

**File:** `/src/components/shared/Toast.jsx` or use inline Alert

#### Pattern: Alert as Toast Alternative
```jsx
import { Alert } from '@/components/shared/Alert';

// Success notification
{showSuccess && (
  <Alert variant="success" onClose={() => setShowSuccess(false)}>
    ✓ Data saved successfully!
  </Alert>
)}

// Error notification
{showError && (
  <Alert variant="error" onClose={() => setShowError(false)}>
    ✗ Operation failed. Please try again.
  </Alert>
)}

// Warning notification
{showWarning && (
  <Alert variant="warning">
    ⚠ This action cannot be undone.
  </Alert>
)}
```

#### Accessibility Requirements for Notifications
```jsx
// Success/Info messages - polite announcement
<div
  role="status"
  aria-live="polite"
  className="alert alert-success"
>
  Data saved successfully
</div>

// Error/Warning messages - assertive announcement
<div
  role="alert"
  aria-live="assertive"
  className="alert alert-error"
>
  Error: Failed to save data
</div>
```

#### DO NOT install react-toastify or similar
- Adds unnecessary bundle size
- Alert component handles all notification needs
- Already accessible with proper ARIA attributes

---

## Disabled States Standard
### Boris Cherny Standard - GAP #100 FIX

All disabled states documented in design-tokens.css are:

### Disabled Buttons
```css
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
```

### Disabled Inputs
```css
input:disabled,
textarea:disabled,
select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: var(--color-bg-secondary);
  color: var(--color-text-tertiary);
}
```

### Usage in Components
```jsx
// Button
<Button disabled={isLoading || !isValid}>
  Submit
</Button>

// Input
<input
  type="text"
  disabled={isProcessing}
  aria-disabled={isProcessing}
/>

// With visual indication
<button
  disabled={!canSubmit}
  className={!canSubmit ? 'opacity-50 cursor-not-allowed' : ''}
>
  Submit
</button>
```

### Accessibility Requirements
- ALL disabled elements MUST have `disabled` attribute (not just CSS)
- ALL disabled interactive elements SHOULD have `aria-disabled="true"`
- ALL disabled elements MUST show `cursor: not-allowed`
- ALL disabled elements MUST have reduced opacity (0.5-0.6)

---

## Design Token Usage
### Boris Cherny Standard - GAPS #94, #95, #99 FIX

All design tokens are documented in `/src/styles/design-tokens.css`:

### Spacing Values (GAP #94 ✓ Already Documented)
```css
--space-xs: 0.25rem;   /* 4px */
--space-sm: 0.5rem;    /* 8px */
--space-md: 1rem;      /* 16px */
--space-lg: 1.5rem;    /* 24px */
--space-xl: 2.5rem;    /* 40px */
--space-2xl: 4rem;     /* 64px */
```

Usage:
```css
.card {
  padding: var(--space-md);
  margin-bottom: var(--space-lg);
  gap: var(--space-sm);
}
```

### Typography Scale (GAP #95 ✓ Already Documented)
```css
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
```

Font weights:
```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Responsive Breakpoints (GAP #99 ✓ Already Documented)
```css
--breakpoint-sm: 640px;   /* Mobile landscape */
--breakpoint-md: 768px;   /* Tablet */
--breakpoint-lg: 1024px;  /* Laptop */
--breakpoint-xl: 1280px;  /* Desktop */
--breakpoint-2xl: 1536px; /* Large desktop */
```

Usage in media queries:
```css
@media (min-width: 768px) {  /* Tablet and up */
  .container {
    max-width: var(--container-md);
  }
}

@media (min-width: 1024px) {  /* Laptop and up */
  .container {
    max-width: var(--container-lg);
  }
}
```

---

## Questions?

- Shadcn/UI Button: `/src/components/ui/button.tsx`
- Legacy components marked as DEPRECATED in this doc
- Always prefer documented RECOMMENDED components
- Design tokens reference: `/src/styles/design-tokens.css`
- Validation limits: `/src/utils/validation.js`
- When in doubt, follow Boris Cherny Standard (type safety + accessibility)
