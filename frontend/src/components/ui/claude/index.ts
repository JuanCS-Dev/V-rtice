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

// Core Components
export { Button, buttonVariants } from './button'
export type { ButtonProps } from './button'

export { Input } from './input'
export type { InputProps } from './input'

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
} from './card'

export { Badge, badgeVariants } from './badge'
export type { BadgeProps } from './badge'

/**
 * Design System Tokens
 *
 * CRITICAL: Certifique-se de importar o CSS do design system:
 * @import '../../../styles/claude-design-green.css'
 */
