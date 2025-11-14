/**
 * ═══════════════════════════════════════════════════════════════════════════
 * CLAUDE.AI GREEN DESIGN SYSTEM - COMPONENT EXPORTS
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Componentes UI REESCRITOS DO ZERO no estilo Claude.ai com verde
 *
 * Usage:
 * ```tsx
 * import { Button, Input, Card, Badge } from '@/components/ui/claude'
 * ```
 */

// ============================================================================
// CORE COMPONENTS
// ============================================================================

// Button
export { Button, buttonVariants } from './button'
export type { ButtonProps } from './button'

// Input
export { Input } from './input'
export type { InputProps } from './input'

// Textarea
export { Textarea } from './textarea'
export type { TextareaProps } from './textarea'

// Label
export { Label } from './label'

// Card
export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
} from './card'

// Badge
export { Badge, badgeVariants } from './badge'
export type { BadgeProps } from './badge'

// ============================================================================
// FORM COMPONENTS
// ============================================================================

// Select
export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
} from './select'

// Switch
export { Switch } from './switch'

// Checkbox
export { Checkbox } from './checkbox'

// ============================================================================
// FEEDBACK COMPONENTS
// ============================================================================

// Alert
export { Alert, AlertTitle, AlertDescription, alertVariants } from './alert'
export type { AlertProps } from './alert'

// Spinner
export { Spinner, LoadingOverlay, spinnerVariants } from './spinner'
export type { SpinnerProps, LoadingOverlayProps } from './spinner'

// Skeleton
export { Skeleton, CardSkeleton, ListSkeleton } from './skeleton'

/**
 * Design System Tokens
 *
 * CRITICAL: Certifique-se de importar o CSS do design system:
 * @import '../../../styles/claude-design-green.css'
 *
 * Total Components: 12
 * - Button, Input, Textarea, Label
 * - Card (+ 5 subcomponents)
 * - Badge
 * - Select (+ 7 subcomponents)
 * - Switch, Checkbox
 * - Alert (+ 2 subcomponents)
 * - Spinner, LoadingOverlay
 * - Skeleton, CardSkeleton, ListSkeleton
 */
